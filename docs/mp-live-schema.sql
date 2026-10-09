-- Migración aditiva: conserva catálogo, pedidos de prueba y el binding LA_ORDERS_DB.
-- No contiene DROP, cambios de secretos ni sustitución de la base existente.
CREATE TABLE IF NOT EXISTS la_mp_live_orders (
  checkout_id TEXT PRIMARY KEY,
  mp_order_id TEXT UNIQUE,
  receipt_hash TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  external_reference TEXT NOT NULL UNIQUE,
  mode TEXT NOT NULL CHECK(mode IN ('validation','public')),
  kind TEXT NOT NULL CHECK(kind IN ('photos','album')),
  amount INTEGER NOT NULL CHECK(amount > 0),
  catalog_amount INTEGER NOT NULL CHECK(catalog_amount > 0),
  currency TEXT NOT NULL DEFAULT 'ARS',
  seller_id TEXT NOT NULL DEFAULT '',
  application_id TEXT NOT NULL DEFAULT '',
  items_json TEXT NOT NULL,
  print_ids_json TEXT NOT NULL DEFAULT '[]',
  checkout_url TEXT NOT NULL DEFAULT '',
  return_url TEXT NOT NULL,
  mp_status TEXT NOT NULL DEFAULT 'creating',
  status_detail TEXT NOT NULL DEFAULT '',
  payment_valid INTEGER NOT NULL DEFAULT 0 CHECK(payment_valid IN (0,1)),
  before_payment_blocked_at TEXT,
  paid_verified_at TEXT,
  webhook_verified_at TEXT,
  download_verified_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_la_mp_live_status ON la_mp_live_orders(mp_status, updated_at);
CREATE TABLE IF NOT EXISTS la_mp_live_rate_limits (
  bucket_hash TEXT PRIMARY KEY,
  attempts INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_la_mp_live_rate_expiry ON la_mp_live_rate_limits(expires_at);
