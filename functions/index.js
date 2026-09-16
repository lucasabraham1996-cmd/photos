const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const { initializeApp } = require('firebase-admin/app');
const { getFirestore, FieldValue } = require('firebase-admin/firestore');
const crypto = require('crypto');

initializeApp();
const db = getFirestore();

const MP_ACCESS_TOKEN = defineSecret('MP_ACCESS_TOKEN');
const MP_WEBHOOK_SECRET = defineSecret('MP_WEBHOOK_SECRET');

const SITE_URL = 'https://lucasabraham1996-cmd.github.io/photos/';
const ORDERS_PATH = 'artifacts/lucasabraham-ph-db/orders';

function normalizeOrderCode(value) {
  return String(value || '')
    .toUpperCase()
    .replace(/OPERACI[ÓO]N|PEDIDO|CODIGO|C[ÓO]DIGO|N[°º]|#/g, '')
    .replace(/[^A-Z0-9]/g, '');
}

function cors(req, res) {
  const origin = req.get('origin') || '';
  const allowed = origin === SITE_URL.replace(/\/$/, '') || origin === 'https://lucasabraham1996-cmd.github.io' || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  if (allowed) res.set('Access-Control-Allow-Origin', origin);
  res.set('Vary', 'Origin');
  res.set('Access-Control-Allow-Headers', 'Content-Type');
  res.set('Access-Control-Allow-Methods', 'POST,OPTIONS');
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return true;
  }
  return false;
}

async function mercadoPagoFetch(path, options = {}) {
  const token = MP_ACCESS_TOKEN.value();
  const response = await fetch(`https://api.mercadopago.com${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch (_) { data = { raw: text }; }
  if (!response.ok) {
    const error = new Error(data.message || `Mercado Pago respondió ${response.status}`);
    error.status = response.status;
    error.details = data;
    throw error;
  }
  return data;
}

function validateWebhookSignature(req, dataId) {
  const secret = MP_WEBHOOK_SECRET.value();
  const xSignature = String(req.get('x-signature') || '');
  const xRequestId = String(req.get('x-request-id') || '');
  const pairs = Object.fromEntries(xSignature.split(',').map(part => {
    const [k, ...rest] = part.trim().split('=');
    return [k, rest.join('=')];
  }));
  const ts = pairs.ts;
  const received = pairs.v1;
  if (!secret || !ts || !received) return false;
  let manifest = '';
  if (dataId) manifest += `id:${dataId};`;
  if (xRequestId) manifest += `request-id:${xRequestId};`;
  if (ts) manifest += `ts:${ts};`;
  const expected = crypto.createHmac('sha256', secret).update(manifest).digest('hex');
  const a = Buffer.from(expected, 'utf8');
  const b = Buffer.from(received, 'utf8');
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

exports.createMercadoPagoPreference = onRequest({
  region: 'us-central1',
  secrets: [MP_ACCESS_TOKEN]
}, async (req, res) => {
  if (cors(req, res)) return;
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });

  try {
    const orderId = String(req.body?.orderId || '').trim();
    const normalizedId = normalizeOrderCode(orderId);
    if (!orderId || !normalizedId) return res.status(400).json({ error: 'invalid_order_id' });

    const orderRef = db.doc(`${ORDERS_PATH}/${normalizedId}`);
    const orderSnap = await orderRef.get();
    if (!orderSnap.exists) return res.status(404).json({ error: 'order_not_found' });

    const order = orderSnap.data() || {};
    const amount = Number(order.total);
    if (!Number.isFinite(amount) || amount <= 0) return res.status(400).json({ error: 'invalid_order_total' });

    const itemCount = Number(order.itemCount || (Array.isArray(order.items) ? order.items.length : 0)) || 1;
    const title = itemCount === 1 ? '1 foto digital · lucasabraham.ph' : `${itemCount} fotos digitales · lucasabraham.ph`;
    const notificationUrl = 'https://us-central1-lucasabraham-b84aa.cloudfunctions.net/mercadoPagoWebhook';

    const preference = await mercadoPagoFetch('/checkout/preferences', {
      method: 'POST',
      body: JSON.stringify({
        items: [{
          id: normalizedId,
          title,
          quantity: 1,
          currency_id: 'ARS',
          unit_price: amount
        }],
        external_reference: orderId,
        notification_url: notificationUrl,
        back_urls: {
          success: `${SITE_URL}?mp=success&order=${encodeURIComponent(orderId)}#/galeria`,
          pending: `${SITE_URL}?mp=pending&order=${encodeURIComponent(orderId)}#/galeria`,
          failure: `${SITE_URL}?mp=failure&order=${encodeURIComponent(orderId)}#/galeria`
        },
        auto_return: 'approved',
        statement_descriptor: 'LUCASABRAHAM PH',
        metadata: {
          order_id: orderId,
          normalized_order_id: normalizedId,
          item_count: itemCount
        }
      })
    });

    await orderRef.set({
      paymentProvider: 'mercadopago',
      paymentPreferenceId: preference.id || null,
      paymentStatus: 'pendiente',
      paid: false,
      paymentUpdatedAt: FieldValue.serverTimestamp()
    }, { merge: true });

    return res.status(200).json({
      preferenceId: preference.id,
      initPoint: preference.init_point,
      sandboxInitPoint: preference.sandbox_init_point || null,
      orderId
    });
  } catch (error) {
    console.error('createMercadoPagoPreference', error);
    return res.status(error.status && error.status < 500 ? error.status : 500).json({
      error: 'preference_creation_failed',
      message: error.message
    });
  }
});

exports.mercadoPagoWebhook = onRequest({
  region: 'us-central1',
  secrets: [MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET]
}, async (req, res) => {
  if (req.method !== 'POST') return res.status(405).end();

  const dataId = String(req.query['data.id'] || req.body?.data?.id || '');
  if (!validateWebhookSignature(req, dataId)) return res.status(401).end();

  // Confirm receipt quickly; processing stays small and idempotent because we write by order ID.
  try {
    const type = String(req.query.type || req.body?.type || '');
    if (type !== 'payment' || !dataId) return res.status(200).end();

    const payment = await mercadoPagoFetch(`/v1/payments/${encodeURIComponent(dataId)}`);
    const orderId = String(payment.external_reference || payment.metadata?.order_id || '').trim();
    const normalizedId = normalizeOrderCode(orderId);
    if (!normalizedId) return res.status(200).end();

    const orderRef = db.doc(`${ORDERS_PATH}/${normalizedId}`);
    const orderSnap = await orderRef.get();
    if (!orderSnap.exists) return res.status(200).end();

    const order = orderSnap.data() || {};
    const expectedTotal = Number(order.total);
    const receivedTotal = Number(payment.transaction_amount);
    const amountMatches = Number.isFinite(expectedTotal) && Number.isFinite(receivedTotal) && Math.abs(expectedTotal - receivedTotal) < 0.01;
    const approved = payment.status === 'approved' && amountMatches;

    await orderRef.set({
      paymentProvider: 'mercadopago',
      paymentStatus: approved ? 'pagado' : String(payment.status || 'pendiente'),
      paid: approved,
      paymentAmountMatches: amountMatches,
      paymentId: String(payment.id || dataId),
      paymentPreferenceId: payment.preference_id || order.paymentPreferenceId || null,
      paymentMethodId: payment.payment_method_id || null,
      paymentTypeId: payment.payment_type_id || null,
      paymentTransactionAmount: receivedTotal,
      paymentApprovedAt: approved ? (payment.date_approved || new Date().toISOString()) : null,
      paymentUpdatedAt: FieldValue.serverTimestamp()
    }, { merge: true });

    return res.status(200).end();
  } catch (error) {
    console.error('mercadoPagoWebhook', error);
    // Returning 500 makes Mercado Pago retry the notification.
    return res.status(500).end();
  }
});
