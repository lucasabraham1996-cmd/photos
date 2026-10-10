/* Pruebas locales: SQLite real, Worker real y Mercado Pago/Drive simulados.
 * NO realizan cobros ni reemplazan la validación real en Cloudflare.
 * node --test tests/mercadopago-*.test.*
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createHmac } from 'node:crypto';
import worker from '../cloudflare/worker-mp.js';
import validationPage from '../cloudflare/mp-validation-page.js';
import { buildWorker } from '../scripts/build-mp-worker.mjs';
import { appHarness as fullAppHarness } from './app-harness.mjs';
const bundleWorker=(await import('data:text/javascript;base64,'+Buffer.from(buildWorker()).toString('base64'))).default;

const ORIGIN='https://lucasabraham1996-cmd.github.io';
const BASE='https://lucasabraham-ph-api.lucasantonioabraham.workers.dev';
const API='https://api.mercadopago.com/v1/orders';
const schemas=['mp-test-schema.sql','mp-multi-schema.sql','mp-live-schema.sql'].map(name=>
  readFileSync(new URL('../docs/'+name,import.meta.url),'utf8'));
const appSource=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const stamp='2026-10-09T00:00:00.000Z';

function streamedPhoto(options) {
  const size=options.size||200, chunkSize=options.chunkSize||65536;
  const magic=options.magic||[255,216,255];
  let offset=0;options.generated=0;options.cancelled=false;
  const body=new ReadableStream({
    pull(controller){
      if(options.failAt!==undefined&&offset>=options.failAt){controller.error(Error('Drive connection lost'));return}
      if(offset===size){controller.close();return}
      const end=Math.min(size,offset+chunkSize),bytes=new Uint8Array(end-offset);
      for(const [at,value] of [...magic.map((value,i)=>[i,value]),[size-2,255],[size-1,217]])
        if(at>=offset&&at<end)bytes[at-offset]=value;
      offset=end;options.generated=offset;controller.enqueue(bytes);
    },
    cancel(){options.cancelled=true}
  },{highWaterMark:0});
  return new Response(body,{headers:{'Content-Type':'image/jpeg',
    'Content-Length':String(options.declaredSize??size)}});
}
function fixture() {
  const db=new DatabaseSync(':memory:');
  for(const schema of schemas)db.exec(schema);
  db.prepare('INSERT INTO la_mp_catalog VALUES(?,?,?,?,?,?)').run('album-01','Álbum de prueba',60000,0,
    JSON.stringify(Array.from({length:6},(_,i)=>({id:'photo-'+i,name:'Foto '+i+'.jpg',drive_id:'validDriveId12345'+i}))),stamp);
  db.prepare('INSERT INTO la_mp_pricing VALUES(1,?,?)').run(JSON.stringify([{code:'PROMO',percent:20,active:true}]),stamp);
  const d1={prepare(sql){
    let params=[];
    return {bind(...args){params=args;return this},
      async first(){return db.prepare(sql).get(...params)||null},
      async all(){return {results:db.prepare(sql).all(...params)}},
      async run(){const meta=db.prepare(sql).run(...params);return {success:true,meta:{changes:Number(meta.changes)}}}};
  },async batch(commands){
    db.exec('BEGIN');
    try{const result=[];for(const command of commands)result.push(await command.run());db.exec('COMMIT');return result}
    catch(e){db.exec('ROLLBACK');throw e}
  }};
  const env={LA_ORDERS_DB:d1,MP_ACCESS_TOKEN_PROD:'production-fixture',MP_WEBHOOK_SECRET_PROD:'webhook-fixture',
    MP_SETUP_KEY:'admin-fixture',MP_LIVE_MODE:'validation',MP_ACCESS_TOKEN_TEST:'test-fixture'};
  const state={posts:[],orders:new Map(),mpReads:0,driveReads:0,driveHTML:false,driveOptions:null,failCreateOnce:false};
  const originalFetch=globalThis.fetch;
  globalThis.fetch=async(url,options={})=>{
    url=String(url);
    if(url===API){
      const payload=JSON.parse(options.body),idempotency=options.headers['X-Idempotency-Key'];
      state.posts.push({payload,idempotency});
      if(state.failCreateOnce){state.failCreateOnce=false;throw Error('transient fixture failure')}
      const existing=[...state.orders.values()].find(o=>o.external_reference===payload.external_reference);
      if(existing)return Response.json(existing);
      const id='ORDREAL'+String(state.orders.size+1).padStart(16,'0');
      const order={id,type:'online',status:'created',status_detail:'created',total_amount:payload.total_amount,
        total_paid_amount:'0.00',external_reference:payload.external_reference,country_code:'ARG',currency:'ARS',
        user_id:'1001',integration_data:{application_id:'2001'},
        checkout_url:'https://www.mercadopago.com.ar/checkout/v1/redirect?order_id='+id};
      state.orders.set(id,order);return Response.json(order);
    }
    if(url.startsWith(API+'/')){state.mpReads++;return Response.json(state.orders.get(decodeURIComponent(url.slice(API.length+1))),{status:200})}
    if(url.startsWith('https://drive.google.com/')){
      state.driveReads++;
      if(state.driveHTML)return new Response('<html>Drive permission required</html>',{headers:{'Content-Type':'text/html'}});
      if(state.driveOptions)return streamedPhoto(state.driveOptions);
      const bytes=new Uint8Array(200);bytes.set([255,216,255]);bytes.set([255,217],198);
      return new Response(bytes,{headers:{'Content-Type':'image/jpeg'}});
    }
    throw Error('Unexpected external request: '+url);
  };
  const f={db,d1,env,state,worker,
    request(path,body,headers={},method=body===undefined?'GET':'POST',handler=worker){
      return handler.fetch(new Request(BASE+path,{method,
        headers:{Origin:ORIGIN,...headers},...(body!==undefined?{body:JSON.stringify(body)}:{})}),env);
    },
    input(n=1,extra={}){
      return {request_id:crypto.randomUUID(),receipt_token:'a'.repeat(64),
        selection:{kind:'photos',items:Array.from({length:n},(_,i)=>({album_id:'album-01',photo_id:'photo-'+i}))},
        expected_total:n===1?2000:n===3?5400:n*2000,...extra};
    },
    async create(input=this.input()){
      const response=await this.request('/api/live-checkout',input,{'X-Setup-Key':'admin-fixture'});
      const data=await response.json();assert.equal(response.status,200,JSON.stringify(data));return {input,...data};
    },
    paid(purchase,patch={}){
      const order=state.orders.get(purchase.order_id);
      Object.assign(order,{status:'processed',status_detail:'accredited',total_paid_amount:order.total_amount},patch);
    },
    async notify(purchase){
      const ts=String(Date.now()),rid=crypto.randomUUID();
      const sig=createHmac('sha256','webhook-fixture').update('id:'+purchase.order_id.toLowerCase()+';request-id:'+rid+';ts:'+ts+';').digest('hex');
      const response=await this.request('/webhook/mp/live?data.id='+purchase.order_id,
        {type:'order',live_mode:true,data:{id:purchase.order_id}},
        {'x-signature':'ts='+ts+',v1='+sig,'x-request-id':rid});
      assert.equal(response.status,200);
    },
    async status(purchase){
      const res=await this.request('/api/live-status',{checkout_id:purchase.checkout_id,receipt_token:purchase.receipt_token});
      return {status:res.status,...await res.json()};
    },
    download(purchase,token=purchase.receipt_token,handler=worker){
      return this.request('/api/live-download/'+purchase.checkout_id+'/0',undefined,{'X-Receipt-Token':token},'GET',handler);
    },
    close(){globalThis.fetch=originalFetch;db.close()}
  };
  return f;
}
async function withFixture(callback){const f=fixture();try{await callback(f)}finally{f.close()}}

test('Los modos disabled y public sin evidencia no crean cobros',()=>withFixture(async f=>{
  for(const mode of ['disabled','public']){
    f.env.MP_LIVE_MODE=mode;
    const config=await (await f.request('/api/payment-config')).json();
    assert.equal(config.public_enabled,false);
    assert.equal((await f.request('/api/live-checkout',f.input(),{'X-Setup-Key':'admin-fixture'})).status,503);
  }
  assert.equal(f.state.posts.length,0);
}));
test('Validación exige clave y permite solamente una foto digital',()=>withFixture(async f=>{
  assert.equal((await f.request('/api/live-checkout',f.input())).status,401);
  assert.equal((await f.request('/api/live-checkout',f.input(3),{'X-Setup-Key':'admin-fixture'})).status,400);
  assert.equal(f.state.posts.length,0);
}));
test('Solo el administrador consulta las órdenes de MP y los links originales, sin habilitar acceso público',()=>withFixture(async f=>{
  const p=await f.create();
  assert.equal((await f.request('/api/admin-orders',{offset:0})).status,401);
  assert.equal((await f.request('/api/admin-orders',{offset:0},{'X-Setup-Key':'incorrecta'})).status,401);
  const res=await f.request('/api/admin-orders',{offset:0},{'X-Setup-Key':'admin-fixture'});
  assert.equal(res.status,200);
  const before=await res.json();
  assert.equal(before.orders.length,1);
  assert.equal(before.orders[0].paid,false);
  assert.equal(before.orders[0].photos.length,1);
  assert.equal(before.orders[0].photos[0].download_url,
    'https://drive.google.com/uc?export=download&id=validDriveId123450');
  assert.equal(before.has_more,false);
  f.paid(p);await f.notify(p);
  const after=await (await f.request('/api/admin-orders',{offset:0},{'X-Setup-Key':'admin-fixture'})).json();
  assert.equal(after.orders[0].paid,true);
  assert.equal(after.orders[0].invoice_status,'pendiente_emision_arca');
  assert.equal((await f.request('/api/admin-orders',{offset:-1},{'X-Setup-Key':'admin-fixture'})).status,400);
}));

test('Recuperar una validación exige clave y se rechaza fuera del modo privado',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);await f.status(p);
  const original=f.db.prepare('SELECT receipt_hash FROM la_mp_live_orders').get().receipt_hash;
  for(const key of ['', 'incorrecta'])
    assert.equal((await f.request('/api/live-recover',{},key?{'X-Setup-Key':key}:{})).status,401);
  f.env.MP_LIVE_MODE='public';
  assert.equal((await f.request('/api/live-recover',{}, {'X-Setup-Key':'admin-fixture'})).status,503);
  assert.equal(f.db.prepare('SELECT receipt_hash FROM la_mp_live_orders').get().receipt_hash,original);
  assert.equal(f.state.posts.length,1);
}));
test('Recuperación devuelve la compra acreditada aunque exista otro intento pendiente',()=>withFixture(async f=>{
  const paid=await f.create();await f.download(paid);f.paid(paid);await f.notify(paid);
  const pending=await f.create();await f.download(pending);
  const response=await f.request('/api/live-recover',{}, {'X-Setup-Key':'admin-fixture'});
  const recovered=await response.json();assert.equal(response.status,200);
  assert.equal(recovered.checkout_id,paid.checkout_id);assert.equal(recovered.order_id,paid.order_id);
  assert.equal(recovered.quote.amount,200);assert.equal(recovered.name,'Foto 0.jpg');
  assert.equal(recovered.verification.before_payment_blocked,true);assert.equal(recovered.verification.webhook_received,true);
  assert.match(recovered.receipt_token,/^[a-f0-9]{64}$/);assert.notEqual(recovered.receipt_token,paid.receipt_token);
  assert.equal((await f.download(paid)).status,403);
  const file=await f.download(recovered);assert.equal(file.status,200);await file.arrayBuffer();
  assert.ok(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders WHERE checkout_id=?').get(paid.checkout_id).download_verified_at);
  assert.equal(f.db.prepare('SELECT payment_valid FROM la_mp_live_orders WHERE checkout_id=?').get(pending.checkout_id).payment_valid,0);
  assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM la_mp_live_orders').get().n,2);
  assert.equal(f.state.posts.length,2);
}));
test('Recuperación no crea una orden cuando aún no existe una compra acreditada',()=>withFixture(async f=>{
  await f.create();
  assert.equal((await f.request('/api/live-recover',{}, {'X-Setup-Key':'admin-fixture'})).status,404);
  assert.equal(f.state.posts.length,1);assert.equal(f.state.mpReads,0);
}));
test('Recuperación consulta Mercado Pago y rechaza una compra reembolsada sin cambiar su recibo',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);await f.status(p);
  const original=f.db.prepare('SELECT receipt_hash FROM la_mp_live_orders').get().receipt_hash;
  f.paid(p,{status_detail:'refunded'});
  assert.equal((await f.request('/api/live-recover',{}, {'X-Setup-Key':'admin-fixture'})).status,409);
  assert.equal(f.db.prepare('SELECT receipt_hash FROM la_mp_live_orders').get().receipt_hash,original);
  assert.equal(f.db.prepare('SELECT payment_valid FROM la_mp_live_orders').get().payment_valid,0);
  assert.equal(f.state.posts.length,1);
}));
test('La foto de validación cobra $200, usa retorno propio y no envía payer ficticio',()=>withFixture(async f=>{
  const p=await f.create(f.input(1,{return_to:'validation'})),payload=f.state.posts[0].payload;
  assert.equal(p.quote.amount,200);assert.equal(p.quote.catalog_amount,2000);
  assert.equal(payload.total_amount,'200.00');assert.equal(payload.payer,undefined);
  assert.equal(payload.config.online.success_url,BASE+'/validation?mp_return=1');
}));
test('Rechaza manipular el precio y fotos inexistentes antes de contactar MP',()=>withFixture(async f=>{
  const badPrice=f.input(1,{expected_total:1});
  assert.equal((await f.request('/api/live-checkout',badPrice,{'X-Setup-Key':'admin-fixture'})).status,409);
  const badPhoto=f.input();badPhoto.selection.items[0].photo_id='missing';
  assert.equal((await f.request('/api/live-checkout',badPhoto,{'X-Setup-Key':'admin-fixture'})).status,409);
  assert.equal(f.state.posts.length,0);
}));
test('Idempotencia: reintento idéntico devuelve la misma orden y recibo',()=>withFixture(async f=>{
  const first=await f.create(),second=await f.create(first.input);
  assert.equal(first.order_id,second.order_id);assert.equal(first.receipt_token,second.receipt_token);
  assert.equal(f.state.posts.length,1);
  assert.equal((await f.request('/api/live-checkout',{...first.input,receipt_token:'b'.repeat(64)},
    {'X-Setup-Key':'admin-fixture'})).status,409);
}));
test('Tras un fallo de red conserva UUID y precio de la orden aunque cambie el catálogo',()=>withFixture(async f=>{
  const input=f.input();f.state.failCreateOnce=true;
  assert.equal((await f.request('/api/live-checkout',input,{'X-Setup-Key':'admin-fixture'})).status,502);
  f.db.prepare('UPDATE la_mp_catalog SET discount_percent=10').run();
  const p=await f.create(input);
  assert.equal(p.quote.amount,200);assert.equal(f.state.posts[0].idempotency,f.state.posts[1].idempotency);
  assert.deepEqual(f.state.posts[0].payload,f.state.posts[1].payload);
}));
test('Pendiente: no muestra enlaces, devuelve 403 y no consulta Drive',()=>withFixture(async f=>{
  const p=await f.create(),status=await f.status(p);
  assert.equal(status.paid,false);assert.deepEqual(status.downloads,[]);
  assert.equal((await f.download(p)).status,403);assert.equal(f.state.driveReads,0);
  const row=f.db.prepare('SELECT * FROM la_mp_live_orders').get();
  assert.ok(row.before_payment_blocked_at);assert.equal(row.paid_verified_at,null);
}));
test('Un comprobante ajeno nunca permite consultar ni descargar',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);
  assert.equal((await f.download(p,'b'.repeat(64))).status,403);
  const res=await f.request('/api/live-status',{checkout_id:p.checkout_id,receipt_token:'b'.repeat(64)});
  assert.equal(res.status,404);assert.equal(f.state.mpReads,0);
}));
test('Estados pendientes, rechazados, autorizados y reembolsados no entregan fotos',()=>withFixture(async f=>{
  const p=await f.create();
  for(const [status,detail] of [['created','created'],['processing','in_process'],['action_required','waiting_capture'],
    ['failed','high_risk'],['processed','refunded'],['processed','partially_refunded']]){
    f.paid(p,{status,status_detail:detail});
    assert.equal((await f.status(p)).paid,false,status+'/'+detail);
    assert.equal((await f.download(p)).status,403);
  }
  assert.equal(f.state.driveReads,0);
}));
test('Comprueba moneda, importe pagado, referencia, vendedor y aplicación',()=>withFixture(async f=>{
  const p=await f.create(),original={...f.state.orders.get(p.order_id)};
  for(const patch of [{currency:'USD'},{total_amount:'1.00'},{total_paid_amount:'100.00'},
    {external_reference:'otra-compra'},{user_id:'9999'},{integration_data:{application_id:'9999'}},
    {id:'ORDTST0123456789012345'},{live_mode:false}]){
    Object.assign(f.state.orders.get(p.order_id),original);f.paid(p,patch);
    assert.equal((await f.status(p)).paid,false,JSON.stringify(patch));
    assert.equal((await f.download(p)).status,403);
  }
  assert.equal(f.state.driveReads,0);
}));
test('La aprobación habilita la foto y un reembolso posterior vuelve a bloquearla',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);
  const status=await f.status(p);
  assert.equal(status.paid,true);assert.equal(status.downloads.length,1);
  assert.equal(status.downloads[0].url.includes(p.receipt_token),false);
  const file=await f.download(p);assert.equal(file.status,200);assert.equal((await file.arrayBuffer()).byteLength,200);
  f.paid(p,{status_detail:'refunded'});
  assert.equal((await f.download(p)).status,403);
  assert.equal(f.db.prepare('SELECT payment_valid FROM la_mp_live_orders').get().payment_valid,0);
}));
test('Una página HTML de Drive no cuenta como descarga verificada',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);f.state.driveHTML=true;
  assert.equal((await f.download(p)).status,502);
  assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false);
}));
test('Una foto de 24 MiB se entrega por streaming y habilita la validación solo al terminar',async()=>{
  for(const handler of [worker,bundleWorker])await withFixture(async f=>{
    const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);
    const options=f.state.driveOptions={size:24*1024*1024};
    const file=await f.download(p,p.receipt_token,handler);
    assert.equal(file.status,200);assert.equal(file.headers.get('Content-Type'),'image/jpeg');
    assert.ok(options.generated<options.size,'No debe leer todo Drive antes de devolver la respuesta');
    assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
    f.env.MP_LIVE_MODE='public';
    assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false);
    let received=0;for await(const chunk of file.body)received+=chunk.byteLength;
    assert.equal(received,options.size);
    assert.ok(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at);
    assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,true);
    assert.equal(f.state.posts.length,1);
  });
});
test('Una descarga truncada no registra entrega aunque tenga firma JPEG válida',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);
  f.state.driveOptions={size:200,declaredSize:400};
  const file=await f.download(p);assert.equal(file.status,200);
  await assert.rejects(file.arrayBuffer(),/No se pudo completar la fotografía/);
  assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false);
}));
test('Una caída de Drive permite reintentar la misma compra pagada sin crear otro cobro',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);
  f.state.driveOptions={size:2000,chunkSize:256,failAt:512};
  const file=await f.download(p);assert.equal(file.status,200);
  await assert.rejects(file.arrayBuffer(),/No se pudo completar la fotografía/);
  assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
  f.state.driveOptions={size:24*1024*1024};
  const retry=await f.download(p);let received=0;
  for await(const chunk of retry.body)received+=chunk.byteLength;
  assert.equal(received,24*1024*1024);
  assert.ok(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at);
  assert.equal(f.state.posts.length,1);
}));
test('Cancelar la descarga cancela Drive y no registra una entrega completa',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);
  const options=f.state.driveOptions={size:24*1024*1024};
  const file=await f.download(p),reader=file.body.getReader();
  assert.equal((await reader.read()).value.byteLength,65536);
  await reader.cancel('buyer cancelled download');
  assert.equal(options.cancelled,true);
  assert.ok(options.generated<options.size);
  assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
}));
test('La firma de imagen puede llegar dividida entre bloques de Drive',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);f.state.driveOptions={size:200,chunkSize:1};
  const file=await f.download(p);assert.equal(file.status,200);
  assert.equal((await file.arrayBuffer()).byteLength,200);
  assert.ok(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at);
}));
test('Un cuerpo inválido rotulado como JPEG se rechaza antes de entregar datos',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);const options=f.state.driveOptions={size:2000,magic:[60,104,116,109,108]};
  assert.equal((await f.download(p)).status,502);
  assert.equal(options.cancelled,true);
  assert.equal(f.db.prepare('SELECT download_verified_at FROM la_mp_live_orders').get().download_verified_at,null);
}));
test('La apertura pública requiere bloqueo previo, pago correcto y bytes recibidos',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);
  const file=await f.download(p);assert.equal(file.status,200);await file.arrayBuffer(); // Sin bloqueo previo no alcanza.
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false);
  f.env.MP_LIVE_MODE='validation';
  f.state.orders.get(p.order_id).status='created';f.state.orders.get(p.order_id).status_detail='created';
  await f.download(p);f.paid(p);await (await f.download(p)).arrayBuffer();
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false); // Falta webhook.
  await f.notify(p);
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,true);
  const cart=f.input(3,{selection:{kind:'photos',items:Array.from({length:3},(_,i)=>({album_id:'album-01',photo_id:'photo-'+i})),coupon:'PROMO',print_ids:['photo-0']},expected_total:7320});
  const live=await f.create(cart);assert.equal(live.quote.amount,7320);assert.equal(live.mode,'public');
}));
test('Webhooks firmados consultan MP; datos de aprobación enviados por el cliente se ignoran',()=>withFixture(async f=>{
  const p=await f.create(),ts=String(Date.now()),rid='webhook-request-01';
  const sig=createHmac('sha256','webhook-fixture').update('id:'+p.order_id.toLowerCase()+';request-id:'+rid+';ts:'+ts+';').digest('hex');
  const body={type:'order',live_mode:true,data:{id:p.order_id},status:'processed',status_detail:'accredited'};
  const path='/webhook/mp/live?data.id='+p.order_id+'&type=order';
  const headers={'x-signature':'ts='+ts+',v1='+sig,'x-request-id':rid};
  assert.equal((await f.request(path,body,headers)).status,200);
  assert.equal(f.db.prepare('SELECT payment_valid FROM la_mp_live_orders').get().payment_valid,0);
  f.paid(p);
  assert.equal((await f.request(path,body,headers)).status,200);
  assert.equal((await f.request(path,body,headers)).status,200); // Notificación repetida.
  assert.equal(f.db.prepare('SELECT payment_valid FROM la_mp_live_orders').get().payment_valid,1);
}));
test('Firma inválida, cuerpo de otro pedido o timestamp viejo se rechazan',()=>withFixture(async f=>{
  const p=await f.create(),rid='webhook-request-02';
  const body={type:'order',live_mode:true,data:{id:p.order_id}},path='/webhook/mp/live?data.id='+p.order_id;
  assert.equal((await f.request(path,body)).status,401);
  for(const old of [false,true]){
    const ts=String(Date.now()-(old?3600000:0));
    const sig=createHmac('sha256','webhook-fixture').update('id:'+p.order_id.toLowerCase()+';request-id:'+rid+';ts:'+ts+';').digest('hex');
    assert.equal((await f.request(path,{...body,data:{id:'otro-id'}},{
      'x-signature':'ts='+ts+',v1='+sig,'x-request-id':rid})).status,old?401:400);
  }
  assert.equal(f.state.mpReads,0);
}));
test('La migración se puede repetir y conserva catálogo y pedidos anteriores',()=>withFixture(async f=>{
  f.db.prepare('INSERT INTO la_mp_test_orders VALUES(?,?,?,?,?,?,?,?,?,?)').run('saved-test-order','hash','photo','Foto','drive',2000,'created','created',stamp,stamp);
  for(const schema of schemas)f.db.exec(schema);
  assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM la_mp_test_orders').get().n,1);
  assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM la_mp_catalog').get().n,1);
}));
test('El bundle para el editor se comporta igual y conserva rutas del piloto',()=>withFixture(async f=>{
  const response=await f.request('/api/payment-config',undefined,{},'GET',bundleWorker);
  assert.equal((await response.json()).mode,'validation');
  const page=await f.request('/validation',undefined,{},'GET',bundleWorker);
  assert.equal(page.status,200);assert.match(await page.text(),/Una compra real/);
  assert.equal((await f.request('/api/basket-checkout',{},{},'POST',bundleWorker)).status,401);
}));
test('Rate limit rechaza el séptimo intento y no crea pedidos adicionales',()=>withFixture(async f=>{
  for(let i=0;i<6;i++)assert.equal((await f.request('/api/live-checkout',f.input(),{'X-Setup-Key':'incorrecta'})).status,401);
  assert.equal((await f.request('/api/live-checkout',f.input(),{'X-Setup-Key':'admin-fixture'})).status,429);
  assert.equal(f.state.posts.length,0);
}));

test('Sincroniza el catálogo real de más de 1,5 MB sin alterar el pedido acreditado',()=>withFixture(async f=>{
  const paid=await f.create();await f.download(paid);f.paid(paid);await f.notify(paid);await (await f.download(paid)).arrayBuffer();
  const ui=fullAppHarness({admin:true,loading:false,introOpen:false});
  const albums=ui.normalizeAlbums(JSON.parse(readFileSync(new URL('../gallery-snapshot.json',import.meta.url),'utf8')));
  ui.state.albums=albums;
  let bodySize=0;
  for(const handler of [worker,bundleWorker]){
    ui.state.mpCatalogueSetupKey='admin-fixture';ui.render();
    ui.ctx.fetch=(url,options)=>{
      bodySize=options.body.length;
      return f.request(String(url).slice(BASE.length),JSON.parse(options.body),options.headers,options.method,handler);
    };
    assert.equal(await ui.actions().syncMpCatalogue(),true);
    assert.ok(bodySize>1500000);assert.ok(bodySize<6000000);
  }
  assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM la_mp_catalog WHERE updated_at=(SELECT updated_at FROM la_mp_pricing WHERE id=1)').get().n,albums.length);
  assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM la_mp_live_orders').get().n,1);
  const old=await f.download(paid);assert.equal(old.status,200);await old.arrayBuffer();
  const album=albums[0],photo=album.photos[0];
  const next=await f.create(f.input(1,{selection:{kind:'photos',items:[{album_id:album.id,photo_id:photo.id}]}}));
  assert.equal(next.quote.catalog_amount,2000);
}));
test('Un administrador sincroniza una galería ausente y reintenta el mismo carrito sin duplicar cobros',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);await (await f.download(p)).arrayBuffer();
  f.env.MP_LIVE_MODE='public';f.db.prepare('DELETE FROM la_mp_catalog').run();
  const app=appHarness(f,{mode:'public',available:true,public_enabled:true});
  app.context.admin=true;app.context.displayAlbums=[{id:'album-01',name:'Álbum',fullPrice:60000,
    photos:[{id:'photo-0',name:'Foto 0.jpg',rawUrl:'https://drive.google.com/file/d/validDriveId123450/view'}]}];
  await app.actions.beginMpTrial();assert.equal(app.context.mpTrialPurchase,null);assert.equal(f.state.posts.length,1);
  await app.actions.syncMpCatalogueAndRetry();
  assert.ok(app.context.mpTrialPurchase);assert.equal(app.context.mpTrialPurchase.amount,2000);
  assert.equal(app.context.promptCount,0);assert.equal(f.state.posts.length,2);
  assert.equal(app.context.mpTrialPurchase.order_data.wantsPoints,false);
}));

function validationHarness(f,purchase) {
  const storage=new Map([['LA_MP_VALIDATION_PURCHASE',JSON.stringify(purchase)]]),elements=new Map(),downloads=[];
  const element=id=>{
    if(!elements.has(id))elements.set(id,{value:'',textContent:'',className:'',disabled:false,
      hidden:['pay','status','download'].includes(id),handlers:{},
      addEventListener(event,handler){this.handlers[event]=handler},focus(){}});
    return elements.get(id);
  };
  const context={
    document:{hidden:false,getElementById:element,body:{appendChild(){}},
      createElement(){return {click(){downloads.push('photo')},remove(){}}}},
    window:{addEventListener(){}},setTimeout(){},setInterval(){return 1},
    URL:{createObjectURL(){return 'blob:fixture'},revokeObjectURL(){}},
    localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},
    fetch:(path,options={})=>f.request(path,options.body===undefined?undefined:JSON.parse(options.body),
      options.headers||{},options.method||'GET')
  };
  const script=validationPage.match(/<script>([\s\S]*?)<\/script>/)[1];
  const initialization=new Function('ctx','with(ctx){'+script+';return initialization;}')(context);
  return {storage,elements,downloads,element,ready:()=>initialization};
}
test('La página recupera el pedido pagado y descarga sin abrir otro checkout',()=>withFixture(async f=>{
  const paid=await f.create();await f.download(paid);f.paid(paid);await f.notify(paid);
  const pending=await f.create();await f.download(pending);
  const page=validationHarness(f,{...pending,name:'Foto 0.jpg',amount:200,before_blocked:true,paid:false,downloaded:false});
  await page.ready();assert.equal(page.element('pay').hidden,false);
  page.element('key').value='admin-fixture';await page.element('recover').handlers.click();
  const saved=JSON.parse(page.storage.get('LA_MP_VALIDATION_PURCHASE'));
  assert.equal(saved.checkout_id,paid.checkout_id);assert.equal(saved.paid,true);assert.equal(saved.downloaded,true);
  assert.equal(page.element('pay').hidden,true);assert.equal(page.element('key').value,'');
  assert.equal(page.downloads.length,1);assert.equal(f.state.posts.length,2);
  assert.equal([...page.storage.values()].some(value=>value.includes('admin-fixture')),false);
}));
test('La página conserva el botón de descarga para reintentar después de una interrupción',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);
  f.state.driveOptions={size:2000,chunkSize:256,failAt:512};
  const page=validationHarness(f,{...p,name:'Foto 0.jpg',amount:200,before_blocked:true,paid:true,downloaded:false});
  await page.ready();assert.equal(page.element('download').hidden,false);assert.equal(page.downloads.length,0);
  f.state.driveOptions=null;await page.element('download').handlers.click();
  assert.equal(page.downloads.length,1);assert.equal(f.state.posts.length,1);
  assert.equal(JSON.parse(page.storage.get('LA_MP_VALIDATION_PURCHASE')).downloaded,true);
}));

function appHarness(f,config={mode:'validation',available:true,validation_amount:200,public_enabled:false}) {
  const storage=new Map(),effects=[],downloads=[],remoteOrders=[];
  const context={admin:true,CLUB_ENABLED:false,mpTrialBusy:false,MP_TRIAL_ENABLED:false,MP_PAYMENT_VISIBLE:true,
    MP_TRIAL_BASE:BASE,mpPaymentConfig:config,mpTrialPurchase:null,mpTrialDownloads:[],
    mpCreateBusyRef:{current:false},mpStatusBusyRef:{current:false},mpAutoDownloadRef:{current:''},
    mpCatalogueBusyRef:{current:false},mpCatalogueSetupKey:'admin-fixture',mpCatalogueSync:{status:'idle',message:''},
    mpZipLoaderRef:{current:null},mpZipBusy:false,
    mpMobilePreview:null,mpMobilePreviewBusy:false,mpPreviewBlobRef:{current:''},
    selectedPhotos:[{id:'photo-0',albumId:'album-01'}],checkoutTotal:2000,checkoutPrint:false,appliedCoupon:null,
    cart:['photo-0'],printedPhotoIds:[],
    printSelectedPhotos:[],displayAlbums:[],discountSettings:{},coupons:[],
    formatPrice:v=>'$'+v,albumPriceWithDiscount:()=>60000,location:{search:'?mp_live=1',pathname:'/photos/',origin:ORIGIN},
    buildOrderPackage:id=>({orderData:{id,date:stamp,total:2000,items:[{id:'photo-0'}],delivered:false,status:'pendiente'}}),
    saveOrderRemote:async order=>{remoteOrders.push(order);return {firebase:true,script:false}},
    promptCount:0,window:{prompt(){context.promptCount++;return 'admin-fixture'},open(){},location:{assign(){}},addEventListener(){},removeEventListener(){}},
    document:{hidden:false,body:{appendChild(){}},createElement(){return {click(){downloads.push('file')},remove(){}}},addEventListener(){},removeEventListener(){}},
    URL:class extends URL{static createObjectURL(){return 'blob:fixture'}static revokeObjectURL(){}},setTimeout(){},setInterval(){return 1},clearInterval(){},
    localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    fetch:(url,options={})=>f.request(String(url).slice(BASE.length),
      options.body===undefined?undefined:JSON.parse(options.body),options.headers||{},options.method||'GET'),
    useEffect:fn=>effects.push(fn),setMpTrialBusy:v=>{context.mpTrialBusy=v},
    setMpTrialMessage:v=>{context.message=v},setMpTrialDownloads:v=>{context.mpTrialDownloads=v},
    setMpZipBusy:v=>{context.mpZipBusy=v},
    setMpMobilePreview:v=>{context.mpMobilePreview=v},
    setMpMobilePreviewBusy:v=>{context.mpMobilePreviewBusy=v},
    setMpCatalogueSync:v=>{context.mpCatalogueSync=v},setMpCatalogueSetupKey:v=>{context.mpCatalogueSetupKey=v},
    setCheckoutOpen:v=>{context.checkoutOpen=v},setAdminMessage(){},
    setMpTrialPurchase:v=>{context.mpTrialPurchase=typeof v==='function'?v(context.mpTrialPurchase):v}
  };
  const start=appSource.indexOf('    const syncMpCatalogue='),end=appSource.indexOf('    const sendOrder=',start);
  assert.ok(start>0&&end>start);
  const actions=new Function('ctx','with(ctx){'+appSource.slice(start,end)+
    ';return {syncMpCatalogue,syncMpCatalogueAndRetry,submitMpTrial,beginMpTrial,checkMpTrial,downloadMpFile,mpPrivateReceiptLink,mpMobileDelivery,mpOriginalPhotoLink,showMpMobilePreview};}')(context);
  return {context,actions,storage,effects,downloads,remoteOrders};
}
test('Aplicación → Worker → SQLite: no descarga antes de pagar; descarga una vez al acreditarse',()=>withFixture(async f=>{
  const app=appHarness(f);
  await app.actions.submitMpTrial({kind:'photos',items:[{album_id:'album-01',photo_id:'photo-0'}]},2000);
  assert.ok(app.context.mpTrialPurchase.ready);assert.equal(app.context.mpTrialPurchase.amount,200);
  await app.actions.checkMpTrial();assert.equal(app.downloads.length,0);assert.equal(app.context.mpTrialDownloads.length,0);
  assert.equal(app.remoteOrders.length,0);
  f.paid(app.context.mpTrialPurchase);
  await app.actions.checkMpTrial();
  assert.equal(app.downloads.length,1);assert.equal(app.context.mpTrialDownloads.length,1);
  assert.equal(app.context.mpTrialPurchase.auto_downloaded,true);
  await app.actions.checkMpTrial();assert.equal(app.downloads.length,1);
  assert.equal(app.remoteOrders.length,1);
  assert.equal(app.remoteOrders[0].paid,true);
  assert.equal(app.remoteOrders[0].total,200);
  assert.equal(app.remoteOrders[0].receipt_token,undefined);
  assert.equal(app.storage.has('LA_MP_LIVE_REQUEST'),false);
}));
test('Aplicación conserva el intento para reintentar un POST fallido sin duplicar la orden',()=>withFixture(async f=>{
  const app=appHarness(f),selection={kind:'photos',items:[{album_id:'album-01',photo_id:'photo-0'}]};
  f.state.failCreateOnce=true;
  await app.actions.submitMpTrial(selection,2000);
  assert.equal(app.storage.has('LA_MP_LIVE_REQUEST'),true);assert.equal(app.context.mpTrialPurchase,null);
  await app.actions.submitMpTrial(selection,2000);
  assert.equal(f.state.posts[0].idempotency,f.state.posts[1].idempotency);
  assert.equal(f.state.orders.size,1);
}));
test('Compras de tres fotos generan un único ZIP automáticamente, con descarga reintentable',()=>withFixture(async f=>{
  const validated=await f.create();await f.download(validated);f.paid(validated);await f.notify(validated);
  await (await f.download(validated)).arrayBuffer();
  f.env.MP_LIVE_MODE='public';
  const purchase=await f.create(f.input(3));
  const app=appHarness(f,{mode:'public',public_enabled:true,available:true});
  const names=[];
  app.context.window.JSZip=class {
    file(name,bytes){names.push([name,bytes.size])}
    async generateAsync(){return new Blob(['ZIP fixture'],{type:'application/zip'})}
  };
  app.context.mpTrialPurchase={...purchase,mode:'public'};
  await app.actions.checkMpTrial();
  assert.equal(app.downloads.length,0);
  f.paid(purchase);await f.notify(purchase);
  await app.actions.checkMpTrial();
  assert.equal(app.downloads.length,1);
  assert.equal(names.length,3);
  assert.equal(names[0][0],'01-Foto 0.jpg');
  assert.equal(app.context.mpTrialPurchase.auto_downloaded,true);
  assert.equal(app.context.mpTrialDownloads.length,3);
  await app.actions.checkMpTrial();assert.equal(app.downloads.length,1);
  assert.equal(f.state.posts.length,2); // Una validación + una compra, no un segundo cobro.
}));

test('En celular no hay ZIP automático: cada foto tiene descarga nativa autenticada',()=>withFixture(async f=>{
  const validated=await f.create();await f.download(validated);f.paid(validated);await f.notify(validated);
  await (await f.download(validated)).arrayBuffer();
  f.env.MP_LIVE_MODE='public';
  const purchase=await f.create(f.input(3));
  const app=appHarness(f,{mode:'public',public_enabled:true,available:true});
  app.context.window.matchMedia=()=>({matches:true});
  app.context.mpTrialPurchase={...purchase,mode:'public'};
  assert.equal(app.actions.mpMobileDelivery(),true);
  await app.actions.checkMpTrial();
  assert.equal(app.downloads.length,0);
  f.paid(purchase);await f.notify(purchase);
  await app.actions.checkMpTrial();
  assert.equal(app.downloads.length,0,'El móvil no inicia ZIP ni varias descargas sin tocar nada');
  assert.equal(app.context.mpTrialDownloads.length,3);
  assert.equal(app.context.mpTrialPurchase.auto_downloaded,undefined);
  const links=app.context.mpTrialDownloads.map(file=>app.actions.mpOriginalPhotoLink(file));
  assert.equal(new Set(links).size,3);
  for(let i=0;i<links.length;i++){
    const url=new URL(links[i]);
    assert.equal(url.origin,BASE);
    assert.equal(url.searchParams.get('token'),purchase.receipt_token);
    const download=await f.request(url.pathname+url.search,undefined,{},'GET');
    assert.equal(download.status,200);
    assert.match(download.headers.get('Content-Disposition'),/attachment/);
  }
  assert.equal(f.state.posts.length,2,'No hubo un segundo cobro');
}));

test('Enlace privado permite recuperar fotos con el UUID y comprobante, sin volver a pagar',()=>withFixture(async f=>{
  const app=appHarness(f);
  const checkout_id=crypto.randomUUID(),receipt_token='a'.repeat(64);
  const url=app.actions.mpPrivateReceiptLink({checkout_id,receipt_token});
  assert.equal(url,ORIGIN+'/photos/#/compra/'+checkout_id+'/'+receipt_token);
  assert.equal(app.actions.mpPrivateReceiptLink({checkout_id,receipt_token:'invalid'}),'');
}));

test('En modo público la aplicación no pide ni envía MP_SETUP_KEY',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);await (await f.download(p)).arrayBuffer();f.env.MP_LIVE_MODE='public';
  const app=appHarness(f,{mode:'public',available:true,public_enabled:true,validation_amount:200});
  await app.actions.submitMpTrial({kind:'photos',items:[{album_id:'album-01',photo_id:'photo-0'}]},2000);
  assert.equal(app.context.promptCount,0);assert.equal(app.context.mpTrialPurchase.amount,2000);
}));
