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
import { buildWorker } from '../scripts/build-mp-worker.mjs';
const bundleWorker=(await import('data:text/javascript;base64,'+Buffer.from(buildWorker()).toString('base64'))).default;

const ORIGIN='https://lucasabraham1996-cmd.github.io';
const BASE='https://lucasabraham-ph-api.lucasantonioabraham.workers.dev';
const API='https://api.mercadopago.com/v1/orders';
const schemas=['mp-test-schema.sql','mp-multi-schema.sql','mp-live-schema.sql'].map(name=>
  readFileSync(new URL('../docs/'+name,import.meta.url),'utf8'));
const appSource=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const stamp='2026-10-09T00:00:00.000Z';

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
  const state={posts:[],orders:new Map(),mpReads:0,driveReads:0,driveHTML:false,failCreateOnce:false};
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
    download(purchase,token=purchase.receipt_token){
      return this.request('/api/live-download/'+purchase.checkout_id+'/0',undefined,{'X-Receipt-Token':token});
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
test('La apertura pública requiere bloqueo previo, pago correcto y bytes recibidos',()=>withFixture(async f=>{
  const p=await f.create();f.paid(p);
  assert.equal((await f.download(p)).status,200); // Sin bloqueo previo no alcanza.
  f.env.MP_LIVE_MODE='public';
  assert.equal((await (await f.request('/api/payment-config')).json()).public_enabled,false);
  f.env.MP_LIVE_MODE='validation';
  f.state.orders.get(p.order_id).status='created';f.state.orders.get(p.order_id).status_detail='created';
  await f.download(p);f.paid(p);await f.download(p);
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

function appHarness(f,config={mode:'validation',available:true,validation_amount:200,public_enabled:false}) {
  const storage=new Map(),effects=[],downloads=[],remoteOrders=[];
  const context={admin:false,mpTrialBusy:false,MP_TRIAL_ENABLED:false,MP_PAYMENT_VISIBLE:true,
    MP_TRIAL_BASE:BASE,mpPaymentConfig:config,mpTrialPurchase:null,mpTrialDownloads:[],
    mpCreateBusyRef:{current:false},mpStatusBusyRef:{current:false},mpAutoDownloadRef:{current:''},
    selectedPhotos:[{id:'photo-0',albumId:'album-01'}],checkoutTotal:2000,checkoutPrint:false,appliedCoupon:null,
    printSelectedPhotos:[],displayAlbums:[],discountSettings:{},coupons:[],
    formatPrice:v=>'$'+v,albumPriceWithDiscount:()=>60000,location:{search:'?mp_live=1'},
    buildOrderPackage:id=>({orderData:{id,date:stamp,total:2000,items:[{id:'photo-0'}],delivered:false,status:'pendiente'}}),
    saveOrderRemote:async order=>{remoteOrders.push(order);return {firebase:true,script:false}},
    promptCount:0,window:{prompt(){context.promptCount++;return 'admin-fixture'},open(){},addEventListener(){},removeEventListener(){}},
    document:{hidden:false,body:{appendChild(){}},createElement(){return {click(){downloads.push('file')},remove(){}}},addEventListener(){},removeEventListener(){}},
    URL:{createObjectURL(){return 'blob:fixture'},revokeObjectURL(){}},setTimeout(){},setInterval(){return 1},clearInterval(){},
    localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    fetch:(url,options={})=>f.request(String(url).slice(BASE.length),
      options.body===undefined?undefined:JSON.parse(options.body),options.headers||{},options.method||'GET'),
    useEffect:fn=>effects.push(fn),setMpTrialBusy:v=>{context.mpTrialBusy=v},
    setMpTrialMessage:v=>{context.message=v},setMpTrialDownloads:v=>{context.mpTrialDownloads=v},
    setCheckoutOpen:v=>{context.checkoutOpen=v},setAdminMessage(){},
    setMpTrialPurchase:v=>{context.mpTrialPurchase=typeof v==='function'?v(context.mpTrialPurchase):v}
  };
  const start=appSource.indexOf('    const syncMpCatalogue='),end=appSource.indexOf('    const sendOrder=',start);
  assert.ok(start>0&&end>start);
  const actions=new Function('ctx','with(ctx){'+appSource.slice(start,end)+
    ';return {submitMpTrial,beginMpTrial,checkMpTrial,downloadMpFile};}')(context);
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
test('En modo público la aplicación no pide ni envía MP_SETUP_KEY',()=>withFixture(async f=>{
  const p=await f.create();await f.download(p);f.paid(p);await f.notify(p);await f.download(p);f.env.MP_LIVE_MODE='public';
  const app=appHarness(f,{mode:'public',available:true,public_enabled:true,validation_amount:200});
  await app.actions.submitMpTrial({kind:'photos',items:[{album_id:'album-01',photo_id:'photo-0'}]},2000);
  assert.equal(app.context.promptCount,0);assert.equal(app.context.mpTrialPurchase.amount,2000);
}));
