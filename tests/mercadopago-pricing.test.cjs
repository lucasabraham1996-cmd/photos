/*
 * Pruebas locales de precios Mercado Pago sin cobros, tokens, D1 ni Cloudflare.
 * Ejecutar: node --test tests/mercadopago-pricing.test.cjs
 *
 * Lee y ejecuta únicamente las funciones puras de precios del Worker real;
 * NO simula un pago acreditado ni habilita descargas.
 */
'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');

const source = readFileSync(join(__dirname, '..', 'cloudflare', 'worker-mp-trial.js'), 'utf8');
const begin = source.indexOf('function intMoney(');
const end = source.indexOf('async function multiRead(', begin);
assert(begin >= 0 && end > begin, 'No se encontraron las funciones de precios originales');
const { computePriceBasket } = new Function(
  'const MAX_CART=500;\n' + source.slice(begin, end) + '\nreturn {computePriceBasket};'
)();

const originals = Array.from({length:12}, (_, i) => ({
  id: 'photo-' + i, name: 'Foto ' + i, drive_id: 'validid123456' + i
}));
const album = {
  album_id: 'album-a',
  full_price: 60000,
  discount_percent: 0,
  photos_json: JSON.stringify(originals)
};
const cart = (n, extra = {}, rows = [album], coupons = []) =>
  computePriceBasket({
    kind: 'photos',
    items: Array.from({length:n}, (_, i) => ({album_id:'album-a', photo_id:'photo-'+i})),
    ...extra
  }, rows, coupons);
const quoteAlbum = (rows = [album]) =>
  computePriceBasket({kind:'album',album_id:'album-a'}, rows, []);

test('Una foto: $2.000', () => assert.equal(cart(1).amount, 2000));
test('Dos fotos: $4.000', () => assert.equal(cart(2).amount, 4000));
test('Tres fotos: descuento 10% y total $5.400', () => assert.equal(cart(3).amount, 5400));
test('Cinco fotos: descuento 15% y total $8.500', () => assert.equal(cart(5).amount, 8500));
test('Descuento web 10% adicional a tres fotos', () => assert.equal(
  cart(3, {}, [{...album, discount_percent:10}]).amount, 4860
));
test('Cupón 20% adicional a cantidad y web', () => assert.equal(
  cart(3, {coupon:'promo'}, [{...album,discount_percent:10}], [{code:'PROMO',percent:20,active:true}]).amount,
  3888
));
test('Dos impresiones suman $6.000', () => assert.equal(
  cart(3, {print_ids:['photo-0','photo-1']}).amount, 11400
));
test('Álbum sin descuento: $60.000', () => assert.equal(quoteAlbum().amount, 60000));
test('Álbum con descuento web 10%: $54.000', () => assert.equal(
  quoteAlbum([{...album,discount_percent:10}]).amount, 54000
));
test('Rechaza cupones inexistentes', () => assert.throws(() => cart(3,{coupon:'inexistente'})));
test('Rechaza la misma fotografía dos veces', () => assert.throws(() => cart(2,{
  items:[{album_id:'album-a',photo_id:'photo-0'},{album_id:'album-a',photo_id:'photo-0'}]
})));
test('Rechaza solicitar impresión de una foto fuera del carrito', () =>
  assert.throws(() => cart(3,{print_ids:['photo-5']})));
test('Rechaza fotos que no existen en el catálogo', () =>
  assert.throws(() => cart(1,{items:[{album_id:'album-a',photo_id:'photo-999'}]})));
