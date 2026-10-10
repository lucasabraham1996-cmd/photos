import { test } from 'node:test';
import assert from 'node:assert/strict';
import { appHarness, nodes, textContent } from './app-harness.mjs';

const photo={id:'photo-01',albumId:'album-01',albumName:'All Boys',name:'Foto 1.jpg',code:'001',price:2000,
  rawUrl:'https://drive.google.com/file/d/validDriveId12345/view',url:'https://drive.google.com/file/d/validDriveId12345/view'};
const base={albums:[{id:'album-01',name:'All Boys',fullPrice:60000,dateTs:Date.now(),photos:[photo],subalbums:[]}],
  cart:[photo.id],loading:false,introOpen:false,checkoutOpen:true,
  mpPaymentConfig:{mode:'public',available:true,public_enabled:true,loading:false}};
const reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
const paymentButton=tree=>nodes(tree).find(n=>n.props.className==='mp-pay-button');

test('El carrito ofrece pago directo y consulta al WhatsApp personal sin registrar una venta',()=>{
  const h=appHarness(base),tree=h.render();
  const card=nodes(tree).find(n=>n.props.id==='checkout-mercadopago');
  const actions=nodes(card).filter(n=>n.type==='button'||n.type==='a');
  assert.equal(actions.length,2);assert.equal(actions[0].props.disabled,false);
  assert.match(textContent(actions[0]),/Pagar con Mercado Pago/);
  const url=new URL(actions[1].props.href);
  assert.equal(url.hostname,'wa.me');assert.equal(url.pathname,'/5493515580770');
  assert.match(url.searchParams.get('text'),/consultar otros medios de pago/);
  assert.match(url.searchParams.get('text'),/All Boys · Foto 1.jpg/);
  assert.doesNotMatch(url.searchParams.get('text'),/comprobante|transferí|puntos|club/i);
  assert.equal(nodes(tree).some(n=>/checkout-floating-cta|checkout-simple-cta/.test(n.props.className||'')),false);
  assert.equal(h.ctx.requests.length,0);assert.equal(h.storage.size,0);
});
test('No ofrece descargas sin verificación ni filtra una compra anterior en otro carrito',()=>{
  const oldOrder={checkout_id:'old-order',order_id:'MP-OLD',receipt_token:'a'.repeat(64),
    mode:'public',paid:true,amount:2000,selection_signature:'old-signature'};
  const sampleFiles=[{name:'Foto original.jpg',url:'https://lucasabraham-ph-api.lucasantonioabraham.workers.dev/api/live-download/old-order/0'}];
  for(const overrides of [
    {mpTrialPurchase:oldOrder,mpTrialDownloads:sampleFiles,mpReceiptView:false,
     mpVerifiedCheckoutId:'old-order'},
    {mpTrialPurchase:oldOrder,mpTrialDownloads:sampleFiles,mpReceiptView:true,
     mpVerifiedCheckoutId:''},
    {mpTrialPurchase:{...oldOrder,paid:false},mpTrialDownloads:sampleFiles,mpReceiptView:true,
     mpVerifiedCheckoutId:''}
  ]){
    const h=appHarness({...base,...overrides});
    const tree=h.render();
    assert.equal(nodes(tree).some(n=>n.props['aria-label']==='Descargar fotografías compradas'),false,
      'Nunca enseñar controles de descarga para un carrito nuevo ni pago no verificado');
    assert.equal(nodes(tree).some(n=>n.props.href&&/live-download/.test(n.props.href)),false,
      'Nunca exponer enlace de descarga hasta validar en servidor');
    if(!overrides.mpReceiptView)
      assert.ok(nodes(tree).some(n=>n.props.id==='checkout-mercadopago'),
        'El nuevo carrito conserva su botón de pago, no el recibo viejo');
    else
      assert.equal(nodes(tree).some(n=>n.props.id==='checkout-mercadopago'),false,
        'La pantalla de verificación nunca ofrece otro pago accidental');
  }
});
test('Sin clave, la sincronización explica el problema junto al botón sin usar diálogos',async()=>{
  const h=appHarness({...base,admin:true,route:'#/admin',checkoutOpen:false});
  h.ctx.window.prompt=()=>{throw Error('No se debe abrir un diálogo')};h.render();
  assert.equal(await h.actions().syncMpCatalogue(),false);
  const tree=h.render(),field=nodes(tree).find(n=>n.props.id==='mp-catalogue-key-admin');
  assert.equal(field.props.type,'password');
  assert.ok(nodes(tree).some(n=>n.props.role==='alert'&&/Ingresá la clave/.test(textContent(n))));
  assert.equal(h.ctx.requests.length,0);
});
test('La sincronización muestra progreso y resultado, evita un segundo envío y borra la clave',async()=>{
  const h=appHarness({...base,admin:true,route:'#/admin',checkoutOpen:false,mpCatalogueSetupKey:'admin-fixture'});h.render();
  let release,requests=0;
  h.ctx.fetch=(_,options)=>{
    requests++;assert.equal(options.headers['X-Setup-Key'],'admin-fixture');
    return new Promise(resolve=>{release=resolve});
  };
  const actions=h.actions(),first=actions.syncMpCatalogue();
  assert.equal(h.state.mpCatalogueSync.status,'working');
  assert.equal(await actions.syncMpCatalogue(),false);assert.equal(requests,1);
  release(reply({ok:true,albums:21,photos:12006}));assert.equal(await first,true);
  assert.equal(h.state.mpCatalogueSetupKey,'');
  const tree=h.render();
  assert.ok(nodes(tree).some(n=>n.props.className==='mp-catalogue-result success'&&/21 galerías y 12006 fotos/.test(textContent(n))));
  assert.equal([...h.storage.values()].some(value=>value.includes('admin-fixture')),false);
});
test('Errores de clave, límite antiguo, Cloudflare y conexión quedan visibles y permiten reintentar',async()=>{
  for(const [response,expected] of [
    [()=>reply({error:'Unauthorized'},401),/no es correcta/],
    [()=>reply({error:'Solicitud demasiado grande'},400),/límite anterior/],
    [()=>new Response('<html>Forbidden</html>',{status:403}),/HTTP 403/],
    [()=>{throw new TypeError('Failed to fetch')},/conectar con Cloudflare/]
  ]){
    const h=appHarness({...base,admin:true,route:'#/admin',checkoutOpen:false,mpCatalogueSetupKey:'admin-fixture'});h.render();
    h.ctx.fetch=async()=>response();assert.equal(await h.actions().syncMpCatalogue(),false);
    assert.match(h.state.mpCatalogueSync.message,expected);assert.equal(h.state.mpTrialBusy,false);
    assert.ok(nodes(h.render()).some(n=>n.props.role==='alert'&&expected.test(textContent(n))));
  }
  const h=appHarness({...base,admin:true,route:'#/admin',checkoutOpen:false,mpCatalogueSetupKey:'admin-fixture'});let timer;
  h.ctx.setTimeout=fn=>{timer=fn};h.ctx.fetch=(_,options)=>new Promise((_,reject)=>{
    options.signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')));
  });h.render();const pending=h.actions().syncMpCatalogue();timer();
  assert.equal(await pending,false);assert.match(h.state.mpCatalogueSync.message,/45 segundos/);
  assert.equal(h.state.mpTrialBusy,false);
});
test('Un clic abre Mercado Pago después de guardar el recibo y reusa el pago pendiente',async()=>{
  const h=appHarness(base),navigations=[];h.render();let requests=0;
  h.ctx.fetch=async(_,options)=>{
    requests++;assert.equal(options.headers['X-Setup-Key'],undefined);
    return reply({ok:true,mode:'public',order_id:'ORD123',checkout_id:'checkout-123',receipt_token:'receipt-fixture',
      checkout_url:'https://www.mercadopago.com.ar/checkout/v1/redirect?order_id=ORD123',
      quote:{kind:'photos',quantity:1,amount:2000}});
  };
  h.ctx.window.location.assign=url=>{
    assert.equal(JSON.parse(h.storage.get('LA_MP_LIVE_PURCHASE')).receipt_token,'receipt-fixture');
    assert.deepEqual(JSON.parse(h.storage.get('LA_MP_CHECKOUT_STATE')).cart,[photo.id]);
    navigations.push(url);
  };
  await paymentButton(h.render()).props.onClick();
  assert.equal(requests,1);assert.equal(navigations.length,1);
  assert.match(navigations[0],/^https:\/\/www.mercadopago.com.ar\/checkout\//);
  await paymentButton(h.render()).props.onClick();
  assert.equal(requests,1);assert.equal(navigations.length,2);
  h.state.mpTrialPurchase={...h.state.mpTrialPurchase,paid:true};
  assert.equal(paymentButton(h.render()).props.disabled,false,
    'Una compra antigua no bloquea un carrito nuevo');
});
test('Volver de Mercado Pago abre ticket sin restaurar un carrito viejo ni enlaces ajenos',async()=>{
  const {cart:_,...rest}=base;
  const h=appHarness(rest);h.ctx.location.search='?mp_return=1';
  h.storage.set('LA_MP_LIVE_PURCHASE',JSON.stringify({order_id:'ORD123',receipt_token:'receipt-fixture'}));
  h.storage.set('LA_MP_CHECKOUT_STATE',JSON.stringify({order_id:'ORD123',cart:[photo.id],print:true,
    print_ids:[photo.id],coupon:{code:'AHORRO',percent:10}}));h.render();
  assert.deepEqual(h.state.cart,[]);assert.equal(h.state.checkoutPrint,false);
  assert.deepEqual(h.state.printedPhotoIds,[]);assert.equal(h.state.appliedCoupon,null);
  assert.equal(h.state.mpReceiptView,true,'La devolución debe abrir el comprobante y no el carrito');
  const bad=appHarness(base);bad.render();let navigated=false;
  bad.ctx.window.location.assign=()=>{navigated=true};
  bad.ctx.fetch=async()=>reply({ok:true,mode:'public',order_id:'ORD123',checkout_id:'checkout-123',receipt_token:'receipt-fixture',
    checkout_url:'https://example.com/checkout/?order_id=ORD123',quote:{kind:'photos',quantity:1,amount:2000}});
  await paymentButton(bad.render()).props.onClick();assert.equal(navigated,false);
  assert.match(bad.state.mpTrialMessage,/enlace de pago válido/);
});
test('El álbum completo ofrece las mismas dos opciones y su botón paga el álbum correcto',async()=>{
  const h=appHarness({...base,activeAlbum:'album-01',route:'#/album/album-01',checkoutOpen:false,purchaseHelpOpen:true});
  let tree=h.render(),card=nodes(tree).find(n=>n.props.id==='album-payment-options');
  assert.ok(card);assert.equal(nodes(card).filter(n=>n.type==='a'||n.type==='button').length,2);
  const consultation=new URL(nodes(card).find(n=>n.type==='a').props.href);
  assert.match(consultation.searchParams.get('text'),/colección completa de All Boys/);
  assert.match(consultation.searchParams.get('text'),/60\.000/);
  assert.doesNotMatch(consultation.searchParams.get('text'),/alias|comprobante/i);
  assert.doesNotMatch(textContent(tree),/Copiá el alias|Finalizar compra|adjuntás el comprobante/i);
  let navigated=false;
  h.ctx.window.location.assign=()=>{navigated=true};
  h.ctx.fetch=async(_,options)=>{
    const input=JSON.parse(options.body);
    assert.deepEqual(input.selection,{kind:'album',album_id:'album-01'});assert.equal(input.expected_total,60000);
    return reply({ok:true,mode:'public',order_id:'ORD123',checkout_id:'checkout-123',receipt_token:'receipt-fixture',
      checkout_url:'https://www.mercadopago.com.ar/checkout/v1/redirect?order_id=ORD123',quote:{kind:'album',quantity:1,amount:60000}});
  };
  await nodes(card).find(n=>n.type==='button').props.onClick();assert.equal(navigated,true);
});
