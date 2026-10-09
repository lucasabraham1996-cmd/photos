-- Aplicar en Cloudflare D1 después del esquema de prueba inicial.
-- Catálogo controlado por administrador. Compradores no pueden escribir precios.
CREATE TABLE IF NOT EXISTS la_mp_catalog (
 album_id TEXT PRIMARY KEY,
 album_name TEXT NOT NULL,
 full_price INTEGER NOT NULL,
 discount_percent REAL NOT NULL DEFAULT 0,
 photos_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS la_mp_pricing (
 id INTEGER PRIMARY KEY CHECK(id=1),
 coupons_json TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS la_mp_bundle_orders (
 mp_order_id TEXT PRIMARY KEY,
 receipt_hash TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('photos','album')),
 amount INTEGER NOT NULL CHECK(amount>0),
 mp_status TEXT NOT NULL,
 status_detail TEXT NOT NULL DEFAULT '',
 items_json TEXT NOT NULL,
 print_ids_json TEXT NOT NULL DEFAULT '[]',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mp_bundle_updated ON la_mp_bundle_orders(updated_at);
