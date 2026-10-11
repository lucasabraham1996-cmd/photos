import { test } from 'node:test';
import assert from 'node:assert/strict';
import { appHarness, nodes, textContent } from './app-harness.mjs';

const photo={id:'photo-01',albumId:'album-01',albumName:'All Boys',name:'Foto 1.jpg',code:'001',price:2000,
  rawUrl:'https://drive.google.com/file/d/validDriveId12345/view',url:'https://drive.google.com/file/d/validDriveId12345/view'};
const base={albums:[{id:'album-01',name:'All Boys',fullPrice:60000,dateTs:Date.now(),photos:[photo],subalbums:[]}],
  cart:[photo.id],loading:false,introOpen:false,checkoutOpen:true,
  checkoutCustomerName:'Lucas Abraham',checkoutPhone:'3515580770',
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
test('El regreso en otro navegador recupera ticket, tres fotos y cierre sin carrito viejo',async()=>{
  const checkout=crypto.randomUUID(),token='f'.repeat(64);
  const h=appHarness({...base,checkoutOpen:false,cart:[]});
  h.ctx.location.search='?mp_return=1&mp_live=1';
  h.ctx.location.hash='#/compra/'+checkout+'/'+token;
  h.ctx.location.href=h.ctx.location.origin+h.ctx.location.pathname+h.ctx.location.search+h.ctx.location.hash;
  h.render();
  assert.equal(h.state.mpReceiptView,true);
  assert.equal(h.state.mpReturnMissing,false);
  assert.equal(h.state.mpTrialPurchase.checkout_id,checkout);
  const resume=h.effects.find(fn=>String(fn).includes('mpReturnRequested&&!mpReceiptDismissed'));
  assert.ok(resume,'El retorno tiene un efecto que abre la compra');
  resume();
  assert.equal(h.state.checkoutOpen,true);
  assert.equal(h.state.cart.length,0);
  h.ctx.fetch=async url=>{
    assert.match(String(url),/\/api\/live-status$/);
    return reply({ok:true,paid:true,checkout_id:checkout,order_id:'MP-ORD-NEW',amount:5400,
      downloads:[0,1,2].map(i=>({name:'Foto-'+(i+1)+'.jpg',url:'/api/live-download/'+checkout+'/'+i}))});
  };
  await h.actions().checkMpTrial();
  const tree=h.render(),ticket=nodes(tree).find(n=>n.props['aria-label']==='Ticket de compra');
  assert.ok(ticket,'Aparece ticket luego de verificar el pago');
  assert.match(textContent(ticket),/MP-ORD-NEW/);
  assert.match(textContent(ticket),/5\.400/);
  assert.equal(nodes(tree).filter(n=>n.props['aria-label']==='Descargar fotografías compradas').length,1);
  assert.equal(nodes(tree).filter(n=>n.props.href&&n.props.href.includes('/api/live-download/')).length,3);
  assert.equal(h.state.mpReceipts.length,1);
  h.actions().closeMpCheckout();
  assert.equal(h.state.checkoutOpen,false);
  assert.equal(h.state.mpReceiptView,false);
  assert.equal(h.state.mpTrialPurchase,null);
  assert.equal(h.state.cart.length,0);
  let after=h.render();
  assert.equal(nodes(after).some(n=>textContent(n)==='Ver mi compra'),false);
  assert.ok(nodes(after).some(n=>textContent(n).includes('Mis compras')));
  h.state.cart=[photo.id];
  h.state.checkoutOpen=true;
  after=h.render();
  assert.ok(nodes(after).some(n=>n.props.id==='checkout-mercadopago'));
  assert.equal(nodes(after).some(n=>n.props['aria-label']==='Descargar fotografías compradas'),false);
});
test('Tickets anteriores se abren voluntariamente sin regalar enlaces antes de reverificar',()=>{
  const older={checkout_id:crypto.randomUUID(),receipt_token:'a'.repeat(64),order_id:'OLD-123',paid:true,
    mode:'public',amount:2000,created_at:new Date().toISOString()};
  const h=appHarness({...base,checkoutOpen:false,cart:[]});
  h.storage.set('LA_MP_PURCHASE_RECEIPTS_V1',JSON.stringify([older]));
  h.render();
  const t=h.render();
  assert.ok(nodes(t).some(n=>textContent(n).includes('Mis compras')),'Acceso al historial');
  assert.equal(nodes(t).some(n=>textContent(n)==='Ver mi compra'),false,'No reaparece la compra antigua');
  h.actions().openSavedMpReceipt(older);
  assert.equal(h.state.checkoutOpen,true);
  assert.equal(h.state.mpTrialPurchase.paid,false,'Historial exige verificación nueva');
  assert.equal(h.state.mpReceiptView,true);
  const pending=h.render();
  assert.equal(nodes(pending).some(n=>n.props['aria-label']==='Descargar fotografías compradas'),false);
  assert.equal(nodes(pending).some(n=>n.props.href&&/live-download/.test(n.props.href)),false);
});
test('El álbum completo se acuerda únicamente por WhatsApp y no abre Mercado Pago',async()=>{
  const h=appHarness({...base,activeAlbum:'album-01',route:'#/album/album-01',checkoutOpen:false,purchaseHelpOpen:true});
  const tree=h.render();
  const card=nodes(tree).find(n=>n.props.id==='album-payment-options');
  assert.ok(card,'La oferta del álbum está visible');
  const options=nodes(card).filter(n=>n.type==='a'||n.type==='button');
  assert.equal(options.length,1,'Solo hay un medio de contacto para álbum completo');
  assert.equal(options[0].type,'button');
  assert.equal(typeof options[0].props.onClick,'function','La consulta primero registra un pedido antes de abrir WhatsApp');
  assert.match(textContent(options[0]),/Hablar con Lucas por WhatsApp/i);
  assert.doesNotMatch(textContent(card),/Pagar con Mercado Pago/i);
});

test('El historial principal muestra órdenes D1 pagadas y pendientes aunque Firebase no las tenga',()=>{
  const paid='11111111-1111-4111-8111-111111111111';
  const pending='22222222-2222-4222-8222-222222222222';
  const h=appHarness({...base,admin:true,route:'#/admin',checkoutOpen:false,orders:[],mpAdminOrders:[
    {checkout_id:paid,order_id:'ORDPAID',amount:2000,created_at:'2026-10-10T12:00:00Z',
      paid:true,payment_status:'processed',customer_name:'Cliente Uno',customer_phone:'3511234567',
      photos:[{photo_id:'p1',name:'Una foto.jpg',download_url:'https://drive.google.com/uc?export=download&id=validDriveId12345'}]},
    {checkout_id:pending,order_id:'ORDPENDING',amount:4000,created_at:'2026-10-10T12:01:00Z',
      paid:false,payment_status:'created',customer_name:'Cliente Dos',
      photos:[{photo_id:'p2',name:'Dos.jpg',download_url:'https://drive.google.com/uc?export=download&id=validDriveId12346'}]}
  ]});
  const tree=h.render(),body=textContent(tree);
  assert.match(body,/Historial unificado de todas las órdenes/);
  assert.match(body,/Recuperar pedidos de hoy y todas las ventas MP/);
  assert.match(body,/Cliente Uno/);
  assert.match(body,/Cliente Dos/);
  assert.match(body,/Pago acreditado/);
  assert.match(body,/Pendiente/);
});
