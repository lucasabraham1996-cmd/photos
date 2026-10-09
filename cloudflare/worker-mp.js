/* lucasabraham.ph: Orders API real, cerrada por defecto y compatible con el piloto.
 * Desplegar este módulo (o el bundle del script) conservando bindings y secretos.
 * MP_LIVE_MODE: disabled -> validation -> public, con evidencia real en D1.
 */
import trial, { computePriceBasket, hash } from './worker-mp-trial.js';
import validationPage from './mp-validation-page.js';

const API = 'https://api.mercadopago.com/v1/orders';
const APP_ORIGIN = 'https://lucasabraham1996-cmd.github.io';
const APP_URL = APP_ORIGIN + '/photos/';
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const TOKEN = /^[a-f0-9]{64}$/;
const ORDER = /^ORD(?!TST)[A-Z0-9]{10,100}$/;
const now = () => new Date().toISOString();

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
function json(data, status = 200, origin = '') {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'
  };
  if (origin === APP_ORIGIN) {
    headers['Access-Control-Allow-Origin'] = APP_ORIGIN;
    headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS';
    headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Setup-Key, X-Receipt-Token';
    headers.Vary = 'Origin';
  }
  return new Response(JSON.stringify(data), { status, headers });
}
async function readJSON(request) {
  const reader = request.body?.getReader();
  if (!reader) throw new HttpError(400, 'Solicitud vacía');
  const chunks = [];
  let size = 0;
  for (;;) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > 128000) { await reader.cancel(); throw new HttpError(413, 'Solicitud demasiado grande'); }
    chunks.push(part.value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const part of chunks) { bytes.set(part, offset); offset += part.length; }
  try { return JSON.parse(new TextDecoder().decode(bytes)); }
  catch (_) { throw new HttpError(400, 'Solicitud inválida'); }
}
function cents(value) {
  const match = String(value ?? '').match(/^(\d{1,10})(?:\.(\d{1,2}))?$/);
  if (!match) return null;
  const n = Number(match[1]) * 100 + Number((match[2] || '').padEnd(2, '0'));
  return Number.isSafeInteger(n) ? n : null;
}
function validationAmount(env) {
  const amount = Number(env.MP_VALIDATION_AMOUNT || 200);
  return Number.isSafeInteger(amount) && amount >= 100 && amount <= 500 ? amount : 200;
}
function requireAdmin(request, env) {
  if (!env.MP_SETUP_KEY || request.headers.get('X-Setup-Key') !== env.MP_SETUP_KEY)
    throw new HttpError(401, 'Esta validación requiere la clave de administración');
}
function liveReady(env) {
  return Boolean(env.LA_ORDERS_DB && env.MP_ACCESS_TOKEN_PROD && env.MP_WEBHOOK_SECRET_PROD && env.MP_SETUP_KEY);
}
async function verifiedValidation(env) {
  if (!env.LA_ORDERS_DB) return false;
  const row = await env.LA_ORDERS_DB.prepare(
    "SELECT checkout_id FROM la_mp_live_orders WHERE mode='validation' AND payment_valid=1 AND mp_status='processed' AND status_detail='accredited' AND before_payment_blocked_at IS NOT NULL AND paid_verified_at IS NOT NULL AND webhook_verified_at IS NOT NULL AND download_verified_at IS NOT NULL LIMIT 1"
  ).first();
  return Boolean(row);
}
async function paymentConfig(env) {
  const configured = String(env.MP_LIVE_MODE || 'disabled');
  const verified = configured === 'public' ? await verifiedValidation(env) : false;
  const publicEnabled = configured === 'public' && verified && liveReady(env);
  return {
    ok: true, mode: publicEnabled ? 'public' : configured === 'validation' ? 'validation' : 'disabled',
    public_enabled: publicEnabled, available: liveReady(env) && (configured === 'validation' || publicEnabled),
    validation_amount: validationAmount(env)
  };
}
async function rateLimit(request, env, category, limit) {
  const minute = Math.floor(Date.now() / 60000);
  const key = await hash((request.headers.get('CF-Connecting-IP') || 'unknown') + ':' + category + ':' + minute);
  const row = await env.LA_ORDERS_DB.prepare(
    'INSERT INTO la_mp_live_rate_limits(bucket_hash,attempts,expires_at) VALUES(?,1,?) ON CONFLICT(bucket_hash) DO UPDATE SET attempts=attempts+1 RETURNING attempts'
  ).bind(key, (minute + 2) * 60000).first();
  if (row.attempts > limit) throw new HttpError(429, 'Demasiados intentos. Esperá un minuto');
  if (category === 'checkout') await env.LA_ORDERS_DB.prepare(
    'DELETE FROM la_mp_live_rate_limits WHERE expires_at<?'
  ).bind(Date.now()).run();
}
async function fetchOrder(env, id) {
  try {
    const res = await fetch(API + '/' + encodeURIComponent(id), {
      headers: { Authorization: 'Bearer ' + env.MP_ACCESS_TOKEN_PROD, Accept: 'application/json' },
      signal: AbortSignal.timeout(10000)
    });
    if (!res.ok) throw Error('MP');
    return await res.json();
  } catch (_) { throw new HttpError(502, 'No se pudo verificar el pago con Mercado Pago'); }
}
function sameOrder(mp, row) {
  return ORDER.test(String(mp.id || '')) && (!row.mp_order_id || mp.id === row.mp_order_id) &&
    mp.live_mode !== false && mp.type === 'online' && mp.currency === row.currency &&
    mp.country_code === 'ARG' && mp.external_reference === row.external_reference &&
    cents(mp.total_amount) === row.amount * 100 &&
    /^\d+$/.test(String(mp.user_id || '')) &&
    (!row.seller_id || String(mp.user_id) === row.seller_id) &&
    /^\d+$/.test(String(mp.integration_data?.application_id || '')) &&
    (!row.application_id || String(mp.integration_data?.application_id) === row.application_id);
}
function paidOrder(mp, row) {
  return sameOrder(mp, row) && mp.status === 'processed' && mp.status_detail === 'accredited' &&
    cents(mp.total_paid_amount) === row.amount * 100;
}
async function refreshOrder(env, row) {
  const mp = await fetchOrder(env, row.mp_order_id);
  const paid = paidOrder(mp, row);
  const valid = sameOrder(mp, row);
  const status = valid ? String(mp.status || 'pending').slice(0,80) : 'verification_failed';
  const detail = valid ? String(mp.status_detail || '').slice(0,80) : 'order_mismatch';
  await env.LA_ORDERS_DB.prepare(
    'UPDATE la_mp_live_orders SET mp_status=?,status_detail=?,payment_valid=?,paid_verified_at=CASE WHEN ?=1 THEN COALESCE(paid_verified_at,?) ELSE paid_verified_at END,updated_at=? WHERE checkout_id=?'
  ).bind(status, detail, paid ? 1 : 0, paid ? 1 : 0, now(), now(), row.checkout_id).run();
  return { paid, status, status_detail: detail };
}
async function receipt(env, checkoutId, token) {
  if (!UUID.test(String(checkoutId || '')) || !TOKEN.test(String(token || ''))) return null;
  const row = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_live_orders WHERE checkout_id=?'
  ).bind(checkoutId).first();
  return row && await hash(token) === row.receipt_hash ? row : null;
}
function checkoutResult(row, token) {
  return {
    ok: true, checkout_id: row.checkout_id, order_id: row.mp_order_id, receipt_token: token,
    checkout_url: row.checkout_url, mode: row.mode,
    quote: { kind: row.kind, amount: row.amount, catalog_amount: row.catalog_amount,
      quantity: JSON.parse(row.items_json).length, print_count: JSON.parse(row.print_ids_json).length }
  };
}
function checkoutURL(value, id) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'www.mercadopago.com.ar' &&
      url.pathname.startsWith('/checkout/') && url.searchParams.get('order_id') === id;
  } catch (_) { return false; }
}
function returnURL(input, request, env, mode) {
  // El navegador no puede introducir una URL de retorno arbitraria.
  if (mode === 'validation' && input.return_to === 'validation')
    return new URL('/validation?mp_return=1', request.url).href;
  const url = new URL(env.MP_APP_URL || APP_URL);
  if (url.origin !== APP_ORIGIN || !url.pathname.startsWith('/photos/'))
    throw new HttpError(503, 'La URL de la aplicación no está configurada');
  url.search = '?mp_live=1&mp_return=1';
  url.hash = '';
  return url.href;
}
async function createCheckout(request, env) {
  const config = await paymentConfig(env);
  if (!config.available) throw new HttpError(503, 'Los cobros automáticos todavía no están habilitados');
  await rateLimit(request, env, 'checkout', 6);
  if (config.mode === 'validation') requireAdmin(request, env);
  const input = await readJSON(request);
  if (!UUID.test(String(input.request_id || '')) || !TOKEN.test(String(input.receipt_token || '')))
    throw new HttpError(400, 'Identificador de compra inválido');
  const requestHash = await hash(JSON.stringify({ selection: input.selection, expected_total: input.expected_total }));
  let row = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_live_orders WHERE checkout_id=?'
  ).bind(input.request_id).first();
  if (row) {
    if (row.receipt_hash !== await hash(input.receipt_token) || row.request_hash !== requestHash)
      throw new HttpError(409, 'El identificador pertenece a otra selección');
    if (row.mode !== config.mode) throw new HttpError(409, 'El modo de pago cambió; iniciá una nueva compra');
    if (row.mp_order_id) return checkoutResult(row, input.receipt_token);
  } else {
    const selection = input.selection || {};
    const ids = [...new Set(selection.kind === 'album' ? [String(selection.album_id || '')] :
      Array.isArray(selection.items) ? selection.items.map(p => String(p.album_id || '')) : [])];
    if (!ids.length || ids.length > 80) throw new HttpError(400, 'Selección inválida');
    const pricing = await env.LA_ORDERS_DB.prepare('SELECT * FROM la_mp_pricing WHERE id=1').first();
    if (!pricing) throw new HttpError(409, 'El catálogo todavía no está sincronizado');
    const albums = await env.LA_ORDERS_DB.prepare(
      'SELECT * FROM la_mp_catalog WHERE album_id IN (' + ids.map(() => '?').join(',') + ') AND updated_at=?'
    ).bind(...ids, pricing.updated_at).all();
    let quote;
    try { quote = computePriceBasket(selection, albums.results || [], JSON.parse(pricing.coupons_json)); }
    catch (err) { throw new HttpError(409, err.message); }
    if (input.expected_total !== quote.amount)
      throw new HttpError(409, 'El precio cambió. Actualizá el catálogo antes de continuar');
    if (config.mode === 'validation' &&
      (quote.kind !== 'photos' || quote.quantity !== 1 || quote.printed.length || quote.coupon))
      throw new HttpError(400, 'La validación real permite una sola foto digital, sin cupón ni impresiones');
    const stamp = now();
    const amount = config.mode === 'validation' ? validationAmount(env) : quote.amount;
    await env.LA_ORDERS_DB.prepare(
      'INSERT INTO la_mp_live_orders(checkout_id,receipt_hash,request_hash,external_reference,mode,kind,amount,catalog_amount,items_json,print_ids_json,return_url,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(checkout_id) DO NOTHING'
    ).bind(input.request_id, await hash(input.receipt_token), requestHash, 'LA-LIVE-' + input.request_id,
      config.mode, quote.kind, amount, quote.amount, JSON.stringify(quote.items), JSON.stringify(quote.printed),
      returnURL(input, request, env, config.mode), stamp, stamp).run();
    row = await receipt(env, input.request_id, input.receipt_token);
    if (!row || row.request_hash !== requestHash) throw new HttpError(409, 'Otro intento usa ese identificador');
  }
  // Payload y UUID persistidos antes del POST: reintentos conservan la misma orden.
  const payload = {
    type: 'online', processing_mode: 'manual', total_amount: row.amount.toFixed(2),
    external_reference: row.external_reference, expiration_time: 'P1D',
    description: row.mode === 'validation' ? 'Validacion real privada: fotografia digital' : 'Fotografias lucasabraham.ph',
    items: [{ title: row.mode === 'validation' ? 'Una fotografia digital - validacion privada' :
      row.kind === 'album' ? 'Album digital completo' : 'Fotografias deportivas e impresiones seleccionadas',
      quantity: 1, unit_price: row.amount.toFixed(2) }],
    config: { online: { success_url: row.return_url, failure_url: row.return_url,
      pending_url: row.return_url, auto_return: 'all' } }
  };
  // Se omite el payer ficticio del sandbox: el comprador usa su cuenta real.
  let res, mp;
  try {
    res = await fetch(API, { method: 'POST',
      headers: { Authorization: 'Bearer ' + env.MP_ACCESS_TOKEN_PROD, 'Content-Type': 'application/json',
        Accept: 'application/json', 'X-Idempotency-Key': row.checkout_id },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(10000) });
    mp = await res.json();
  } catch (_) { throw new HttpError(502, 'No se pudo crear la orden. Reintentá la misma compra'); }
  if (!res.ok || !sameOrder(mp, row) || !checkoutURL(mp.checkout_url, mp.id))
    throw new HttpError(502, 'Mercado Pago no devolvió una orden real válida. No se inició el pago');
  await env.LA_ORDERS_DB.prepare(
    'UPDATE la_mp_live_orders SET mp_order_id=?,checkout_url=?,seller_id=?,application_id=?,mp_status=?,status_detail=?,updated_at=? WHERE checkout_id=?'
  ).bind(mp.id, mp.checkout_url, String(mp.user_id), String(mp.integration_data.application_id),
    String(mp.status || 'created'), String(mp.status_detail || ''), now(), row.checkout_id).run();
  row = await receipt(env, row.checkout_id, input.receipt_token);
  return checkoutResult(row, input.receipt_token);
}
async function checkoutStatus(request, env) {
  await rateLimit(request, env, 'status', 60);
  const input = await readJSON(request);
  const row = await receipt(env, input.checkout_id, input.receipt_token);
  if (!row || !row.mp_order_id) throw new HttpError(404, 'Compra inexistente o comprobante inválido');
  const state = await refreshOrder(env, row);
  const items = JSON.parse(row.items_json);
  return { ok: true, ...state, checkout_id: row.checkout_id, order_id: row.mp_order_id,
    mode: row.mode, kind: row.kind, amount: row.amount,
    verification: { before_payment_blocked: Boolean(row.before_payment_blocked_at),
      webhook_received: Boolean(row.webhook_verified_at), download_verified: Boolean(row.download_verified_at) },
    print_requested: JSON.parse(row.print_ids_json).length > 0,
    downloads: state.paid ? items.map((p, i) => ({ name: p.name,
      url: '/api/live-download/' + row.checkout_id + '/' + i })) : [] };
}
function imageMime(bytes) {
  if (bytes.length >= 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if (bytes.length >= 8 && bytes.slice(0,8).every((v,i) => v === [137,80,78,71,13,10,26,10][i])) return 'image/png';
  if (bytes.length >= 12 && new TextDecoder().decode(bytes.slice(0,4)) === 'RIFF' &&
    new TextDecoder().decode(bytes.slice(8,12)) === 'WEBP') return 'image/webp';
  return '';
}
async function download(request, env, url) {
  await rateLimit(request, env, 'download', 60);
  const parts = url.pathname.split('/');
  const token = request.headers.get('X-Receipt-Token') || url.searchParams.get('token');
  const row = await receipt(env, parts[3], token);
  if (!row || !row.mp_order_id) throw new HttpError(403, 'Comprobante de compra inválido');
  const index = /^\d+$/.test(parts[4] || '') ? Number(parts[4]) : -1;
  const items = JSON.parse(row.items_json);
  if (!Number.isSafeInteger(index) || index < 0 || index >= items.length)
    throw new HttpError(404, 'Fotografía inexistente');
  const state = await refreshOrder(env, row); // Nunca confiar solo en un estado almacenado.
  if (!state.paid) {
    if (row.mode === 'validation' && state.status === 'created') await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET before_payment_blocked_at=COALESCE(before_payment_blocked_at,?),updated_at=? WHERE checkout_id=?'
    ).bind(now(), now(), row.checkout_id).run();
    throw new HttpError(403, 'La descarga se habilita cuando el pago está acreditado');
  }
  const item = items[index];
  if (!/^[A-Za-z0-9_-]{10,100}$/.test(item.drive_id)) throw new HttpError(503, 'Archivo no disponible');
  let file;
  try {
    file = await fetch('https://drive.google.com/uc?export=download&id=' + encodeURIComponent(item.drive_id),
      { redirect: 'follow', signal: AbortSignal.timeout(20000) });
  } catch (_) { throw new HttpError(502, 'No se pudo obtener la fotografía. Reintentá la descarga'); }
  const contentType = (file.headers.get('Content-Type') || '').split(';')[0].toLowerCase();
  if (!file.ok || !['image/jpeg','image/png','image/webp','application/octet-stream'].includes(contentType))
    throw new HttpError(502, 'El original de Drive no se pudo descargar. Tu pago sigue registrado');
  let body = file.body, mime = contentType;
  if (row.mode === 'validation') {
    // Evidencia real de bytes completos y firma de imagen; no marcar una página HTML como entrega.
    const reader = file.body.getReader(), chunks = [];
    let size = 0;
    for (;;) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.length;
      if (size > 20000000) { await reader.cancel(); throw new HttpError(502, 'La foto de validación supera 20 MB'); }
      chunks.push(part.value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const part of chunks) { bytes.set(part, offset); offset += part.length; }
    mime = imageMime(bytes);
    if (!mime || size < 100) throw new HttpError(502, 'Drive no devolvió una imagen válida');
    body = bytes;
    await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET download_verified_at=COALESCE(download_verified_at,?),updated_at=? WHERE checkout_id=?'
    ).bind(now(), now(), row.checkout_id).run();
  }
  const filename = String(item.name || 'foto.jpg').replace(/[\r\n/\\]/g, '_').slice(0,200);
  return new Response(body, { headers: {
    'Content-Type': mime, 'Content-Disposition': "attachment; filename*=UTF-8''" + encodeURIComponent(filename),
    'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'
  } });
}
async function signatureValid(request, url, secret) {
  if (!secret) return false;
  const sig = request.headers.get('x-signature') || '';
  const timestamp = sig.match(/(?:^|,)\s*ts=(\d+)(?:,|$)/)?.[1];
  const signed = sig.match(/(?:^|,)\s*v1=([a-f0-9]{64})(?:,|$)/i)?.[1];
  const requestId = request.headers.get('x-request-id') || '';
  const id = url.searchParams.get('data.id') || '';
  if (!timestamp || !signed || !requestId || !ORDER.test(id) || requestId.length > 180) return false;
  const ms = Number(timestamp) < 100000000000 ? Number(timestamp) * 1000 : Number(timestamp);
  if (!Number.isSafeInteger(ms) || Math.abs(Date.now() - ms) > 15 * 60000) return false;
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
  const bytes = new Uint8Array(signed.match(/../g).map(v => parseInt(v,16)));
  const text = 'id:' + id.toLowerCase() + ';request-id:' + requestId + ';ts:' + timestamp + ';';
  return crypto.subtle.verify('HMAC', key, bytes, new TextEncoder().encode(text));
}
async function webhook(request, env, url) {
  if (!await signatureValid(request, url, env.MP_WEBHOOK_SECRET_PROD))
    throw new HttpError(401, 'Firma de notificación inválida');
  const body = await readJSON(request);
  const id = url.searchParams.get('data.id');
  if (body.type !== 'order' || String(body.data?.id || '') !== id || body.live_mode !== true)
    throw new HttpError(400, 'Notificación incompatible con una compra real');
  const row = await env.LA_ORDERS_DB.prepare('SELECT * FROM la_mp_live_orders WHERE mp_order_id=?').bind(id).first();
  if (row) {
    const state=await refreshOrder(env, row); // Repeticiones y eventos fuera de orden consultan la fuente actual.
    if (state.paid) await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET webhook_verified_at=COALESCE(webhook_verified_at,?) WHERE checkout_id=?'
    ).bind(now(), row.checkout_id).run();
  }
  return { ok: true };
}
async function diagnostics(request, env) {
  requireAdmin(request, env);
  const orders = await env.LA_ORDERS_DB.prepare(
    "SELECT checkout_id,mp_order_id,amount,currency,mode,mp_status,status_detail,payment_valid,before_payment_blocked_at,paid_verified_at,webhook_verified_at,download_verified_at,updated_at FROM la_mp_live_orders WHERE mode='validation' ORDER BY created_at DESC LIMIT 10"
  ).all();
  return { ok: true, ...(await paymentConfig(env)), verified_validation: await verifiedValidation(env),
    production_token_configured: Boolean(env.MP_ACCESS_TOKEN_PROD),
    production_webhook_configured: Boolean(env.MP_WEBHOOK_SECRET_PROD), orders: orders.results || [] };
}
async function validationSample(request, env) {
  requireAdmin(request, env);
  const pricing = await env.LA_ORDERS_DB.prepare('SELECT updated_at FROM la_mp_pricing WHERE id=1').first();
  if (!pricing) throw new HttpError(409, 'Primero sincronizá el catálogo');
  const rows = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_catalog WHERE updated_at=? ORDER BY album_id LIMIT 1'
  ).bind(pricing.updated_at).all();
  const album = rows.results?.[0], photo = album && JSON.parse(album.photos_json)[0];
  if (!photo) throw new HttpError(409, 'No hay una fotografía válida en el catálogo');
  const selection = { kind: 'photos', items: [{ album_id: album.album_id, photo_id: photo.id }] };
  const quote = computePriceBasket(selection, [album], []);
  return { ok: true, selection, expected_total: quote.amount,
    name: photo.name, album_name: album.album_name, validation_amount: validationAmount(env) };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url), path = url.pathname, origin = request.headers.get('Origin') || '';
    if (path === '/validation' && request.method === 'GET') return new Response(validationPage, {
      headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
        'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        'X-Frame-Options': 'DENY' }
    });
    const livePath = path.startsWith('/api/live-') || path === '/api/payment-config' || path === '/webhook/mp/live';
    if (!livePath && path !== '/health') return trial.fetch(request, env);
    if (request.method === 'OPTIONS') return json({}, 200, origin);
    try {
      if (origin && origin !== APP_ORIGIN && origin !== url.origin)
        throw new HttpError(403, 'Origen no autorizado');
      if (path === '/health') return json({ ok: true, trial: true, database: Boolean(env.LA_ORDERS_DB),
        live_configured: liveReady(env), public_payments: (await paymentConfig(env)).public_enabled });
      if (path === '/api/payment-config' && request.method === 'GET')
        return json(await paymentConfig(env), 200, origin);
      if (!env.LA_ORDERS_DB || !env.MP_ACCESS_TOKEN_PROD)
        throw new HttpError(503, 'La integración real todavía no está configurada');
      if (path === '/api/live-checkout' && request.method === 'POST')
        return json(await createCheckout(request, env), 200, origin);
      if (path === '/api/live-status' && request.method === 'POST')
        return json(await checkoutStatus(request, env), 200, origin);
      if (path.startsWith('/api/live-download/') && request.method === 'GET') {
        const res = await download(request, env, url);
        if (origin === APP_ORIGIN) {
          res.headers.set('Access-Control-Allow-Origin', APP_ORIGIN);
          res.headers.set('Vary', 'Origin');
        }
        return res;
      }
      if (path === '/api/live-diagnostics' && request.method === 'POST')
        return json(await diagnostics(request, env), 200, origin);
      if (path === '/api/live-sample' && request.method === 'POST')
        return json(await validationSample(request, env), 200, origin);
      if (path === '/webhook/mp/live' && request.method === 'POST')
        return json(await webhook(request, env, url));
      throw new HttpError(404, 'Ruta inexistente');
    } catch (err) {
      // Nunca registrar cuerpos, URLs completas, headers, claves ni tokens de recibo.
      if (!(err instanceof HttpError)) console.error('LA_MP_LIVE_ERROR', { route: path });
      return json({ error: err instanceof HttpError ? err.message : 'Error interno. Tu compra sigue registrada' },
        err instanceof HttpError ? err.status : 500, origin);
    }
  }
};
