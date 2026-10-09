-- Cloudflare D1, database binding: LA_ORDERS_DB
-- Solo pruebas de Mercado Pago. No almacena contraseñas ni tokens en claro.
CREATE TABLE IF NOT EXISTS la_mp_test_orders (
  mp_order_id TEXT PRIMARY KEY,
  receipt_hash TEXT NOT NULL,
  photo_id TEXT NOT NULL,
  photo_name TEXT NOT NULL,
  drive_id TEXT NOT NULL,
  amount INTEGER NOT NULL CHECK(amount > 0),
  mp_status TEXT NOT NULL DEFAULT 'created',
  status_detail TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_la_mp_test_orders_status ON la_mp_test_orders(mp_status, updated_at);
