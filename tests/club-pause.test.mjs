import { test } from 'node:test';
import assert from 'node:assert/strict';
import { appHarness, nodes, textContent } from './app-harness.mjs';

const phone = '3515580770';
const photo = { id:'photo-01', albumId:'album-01', albumName:'All Boys', name:'Foto 1.jpg', price:2000, url:'https://drive.google.com/file/d/validDriveId12345/view', rawUrl:'https://drive.google.com/file/d/validDriveId12345/view' };
const albums = [{ id:'album-01', name:'All Boys', fullPrice:60000, dateTs:Date.now(), photos:[photo], subalbums:[] }];
const oldOrder = { id:'LA-OLD', date:'2026-09-01T12:00:00Z', phone, total:20000, delivered:true, wantsPoints:true, items:[] };
const base = { albums, cart:[photo.id], loading:false, introOpen:false, checkoutOpen:true,
  checkoutWantsPoints:true, customerDetailsSaved:true, customerDetailsOpen:true,
  checkoutPhone:phone, checkoutCustomerName:'Lucas Abraham', clubSessionPhone:phone,
  clubModalOpen:true, orders:[oldOrder], mpPaymentConfig:{mode:'public',available:true,public_enabled:true,loading:false} };

test('El carrito y la cabecera no muestran el Club aunque haya una sesión anterior', () => {
  const h=appHarness(base), tree=h.render();
  assert.doesNotMatch(textContent(tree), /puntos|club de beneficios|sumar|canjes/i);
  assert.equal(nodes(tree).some(n=>/la-club-header|checkout-guest-choice|benefits-glass-btn|club-modal-shell/.test(n.props.className||'')),false);
  assert.ok(nodes(tree).find(n=>n.props.id==='checkout-mercadopago'));
});
test('La administración conserva los pedidos comunes y oculta movimientos y controles del Club', () => {
  const redemption={id:'CB-OLD',date:'2026-09-01T12:00:00Z',type:'benefit_redemption',rewardName:'Premio',redeemedPoints:5,items:[],total:0};
  const pending={id:'LA-PENDING',date:'2026-09-01T12:00:00Z',items:[photo],total:2000};
  const h=appHarness({...base,route:'#/admin',admin:true,orders:[oldOrder,redemption,pending],checkoutOpen:false}), tree=h.render();
  assert.doesNotMatch(textContent(tree), /puntos|club de beneficios|canjes|CANJE CLUB/i);
  assert.match(textContent(tree), /LA-PENDING/);
  assert.doesNotMatch(textContent(tree), /CB-OLD/);
  assert.deepEqual(h.state.orders,[oldOrder,redemption,pending]);
});
test('Las compras nuevas no activan puntos y las confirmaciones no reutilizan promociones antiguas', () => {
  const h=appHarness(base);h.render();const a=h.actions();
  const pkg=a.buildOrderPackage('LA-NEW');
  assert.equal(pkg.orderData.wantsPoints,false);assert.equal(pkg.orderData.phone,'');
  assert.doesNotMatch(pkg.confirmationMessage,/puntos|club|beneficios/i);
  const url=a.orderConfirmationWhatsappUrl({phone,customerName:'Lucas',confirmationMessage:'Sumaste puntos del Club'});
  assert.doesNotMatch(decodeURIComponent(url),/puntos|club|beneficios/i);
  assert.match(decodeURIComponent(url),/Lucas/);
});
test('Las funciones pausadas no consultan ni escriben usuarios, productos, puntos o canjes', async () => {
  const h=appHarness({...base,clubUsers:[{phone,name:'Lucas'}]});h.render();const a=h.actions();
  for(const name of ['openClub','saveCheckoutCustomer','addClubProduct','addManualClubPoints','transferClubPoints','registerClubUser','lookupClubPoints'])await a[name]();
  await a.redeemClubProduct({id:'reward',points:1,active:true});
  const result=await h.saveOrderRemote({id:'CP-NEW',type:'club_points_adjustment',manualPoints:3});
  assert.equal(result.firebase,false);assert.equal(result.script,false);
  assert.equal(h.ctx.requests.length,0);assert.deepEqual(h.state.clubUsers,[{phone,name:'Lucas'}]);
  assert.deepEqual(h.state.orders,[oldOrder]);
});
test('Los saldos históricos se conservan y los pedidos sin puntos no aumentan ese saldo', () => {
  const h=appHarness(base);h.render();
  const balance=h.actions().clubAccountFromOrders([oldOrder,{...oldOrder,id:'LA-NEW',wantsPoints:false}],phone);
  assert.equal(balance.spent,20000);assert.equal(balance.points,5);assert.equal(oldOrder.wantsPoints,true);
});
test('Un enlace antiguo del Club vuelve a la galería sin consultar puntos', () => {
  const h=appHarness({...base,route:'#/club'});h.ctx.location.hash='#/club';h.render();
  const effect=h.effects.find(fn=>fn.toString().includes("route !== '#/club'"));
  assert.ok(effect);effect();assert.equal(h.ctx.location.hash,'#/galeria');
  assert.equal(h.state.clubModalOpen,false);assert.equal(h.ctx.requests.length,0);
});
