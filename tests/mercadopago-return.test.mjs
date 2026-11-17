import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import worker from '../cloudflare/worker-mp-recuperacion.mjs';

const id = 'f0c209ac-a4fe-4a6a-84f9-88a4017cd30b';
const token = 'b'.repeat(64);
const api = 'https://lucasabraham-ph-api.lucasantonioabraham.workers.dev';
const hash = value => createHash('sha256').update(value).digest('hex');

function environment() {
  let selectedId = '';
  return {
    MP_ACCESS_TOKEN_PROD: 'test-token-not-a-production-secret',
    LA_ORDERS_DB: {
      prepare(sql) {
        assert.match(sql, /SELECT \* FROM la_mp_live_orders WHERE checkout_id=\?/);
        return {
          bind(v) {
            selectedId = v;
            return {
              async first() {
                if(selectedId !== id) return null;
                return {checkout_id:id,receipt_hash:hash(token),mp_order_id:'ORD123456789012',mode:'public'};
              }
            };
          }
        };
      }
    }
  };
}

test('retorno de Mercado Pago redirige al ticket privado en otro navegador', async () => {
  const r = await worker.fetch(new Request(api+'/api/mp-return/'+id+'/'+token+'?status=approved'), environment());
  assert.equal(r.status, 303);
  assert.equal(r.headers.get('Location'), 'https://lucasabrahamph.com/?mp_live=1&mp_return=1#/compra/'+id+'/'+token);
  assert.match(r.headers.get('Cache-Control'), /no-store/);
  assert.equal(r.headers.get('Referrer-Policy'), 'no-referrer');
  assert.equal(r.headers.get('X-Robots-Tag'), 'noindex, nofollow');
});

test('un token incorrecto nunca devuelve fotografías o URL privada', async () => {
  const r = await worker.fetch(new Request(api+'/api/mp-return/'+id+'/'+'c'.repeat(64)), environment());
  assert.equal(r.status, 404);
  assert.equal(r.headers.get('Location'), null);
});

test('un checkout inexistente no crea un acceso', async () => {
  const r = await worker.fetch(new Request(api+'/api/mp-return/'+'f0c209ac-a4fe-4a6a-84f9-88a4017cd30c'+'/'+token), environment());
  assert.equal(r.status, 404);
});

test('un UUID o token inválidos son rechazados', async () => {
  const r = await worker.fetch(new Request(api+'/api/mp-return/abc/not-a-token'), environment());
  assert.equal(r.status, 404);
});

test('el enlace de Mercado Pago apunta al puente, no a un hash que MP puede descartar', () => {
  const source = readFileSync(new URL('../cloudflare/worker-mp-recuperacion.mjs', import.meta.url),'utf8');
  assert.match(source, /new URL\('\/api\/mp-return\/' \+ input.request_id \+ '\/' \+ input.receipt_token, request.url\)/);
  assert.match(source, /const target = new URL\(APP_URL\);/);
  assert.match(source, /target.hash = '#\/compra\/' \+ row.checkout_id/);
});
