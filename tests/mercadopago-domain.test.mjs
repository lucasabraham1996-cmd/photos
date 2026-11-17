import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import worker from '../cloudflare/worker-mp-recuperacion.mjs';

const ENDPOINT = 'https://lucasabraham-ph-api.lucasantonioabraham.workers.dev/api/payment-config';
async function options(origin) {
  return worker.fetch(new Request(ENDPOINT, {
    method: 'OPTIONS',
    headers: {
      Origin: origin,
      'Access-Control-Request-Method': 'POST',
      'Access-Control-Request-Headers': 'content-type'
    }
  }), {});
}

test('nuevo dominio permitido con CORS', async () => {
  const response = await options('https://lucasabrahamph.com');
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://lucasabrahamph.com');
  assert.match(response.headers.get('Access-Control-Allow-Methods'), /POST/);
});

test('dominio anterior sigue permitido para compatibilidad', async () => {
  const response = await options('https://lucasabraham1996-cmd.github.io');
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://lucasabraham1996-cmd.github.io');
});

test('origen desconocido nunca recibe permiso de CORS', async () => {
  const response = await options('https://sitio-no-autorizado.example');
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), null);
});

test('el retorno de pagos se fija al dominio nuevo y no acepta URLs arbitrarias', () => {
  const source = readFileSync(new URL('../cloudflare/worker-mp-recuperacion.mjs', import.meta.url), 'utf8');
  assert.match(source, /const APP_URL = APP_ORIGIN \+ '\/';/);
  assert.match(source, /const target = new URL\(APP_URL\);/);
  assert.match(source, /api\/mp-return/);
  assert.match(source, /configured\.origin !== APP_ORIGIN/);
  assert.match(source, /LEGACY_APP_ORIGIN/);
});
