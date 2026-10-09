# Mercado Pago real: preparación y validación privada

## Estado de esta rama

Preparada y probada **localmente**. No se modificó `main`, no se desplegó este nuevo
Worker y no se realizó ninguna compra real desde esta sesión.

El Worker existente respondió `/health` con `trial: true` y `database: true`.
El panel de Cloudflare bloqueó el acceso con “There was a problem with verification”
y el botón de ingreso deshabilitado. Por ese motivo todavía no se pudieron inspeccionar
sus versiones, identificador D1, bindings ni nombres de secretos productivos.
No se modificó la base remota ni sus secretos.

## Archivos y compatibilidad

- `cloudflare/worker-mp.js`: entrada del Worker real.
- `cloudflare/worker-mp-trial.js`: conserva las rutas, credenciales y pedidos del piloto.
- `docs/mp-live-schema.sql`: tablas nuevas, sin borrar o sustituir tablas existentes.
- `cloudflare/mp-validation-page.js`: verificación privada de una foto desde `/validation`.
- `index.html`: integración con el carrito, álbumes y revisión automática del pago.
- `scripts/build-mp-worker.mjs`: genera un único módulo para pegar en el editor de Cloudflare.

WhatsApp, descuentos actuales, cupones e impresión siguen disponibles. En modo público,
la venta pagada se guarda en el historial existente de Firebase/Apps Script.
La confirmación habitual de entrega y Club no se reemplaza.
Las ventas de validación no acumulan puntos. Las impresiones se coordinan por WhatsApp.
El álbum completo entrega la lista de fotos, sin añadir un ZIP.

## Configuración del Worker existente

Antes de escribir en Cloudflare:

1. Resguardar el código y la versión desplegada. Registrar el binding y la base D1
   existentes; exportar la base o registrar su punto de restauración.
2. Confirmar que `LA_ORDERS_DB` sigue apuntando **a la misma D1**.
3. Conservar `MP_SETUP_KEY`, `MP_ACCESS_TOKEN_TEST`, `MP_WEBHOOK_SECRET_TEST`,
   `MP_TEST_BUYER_EMAIL` si existe, y cualquier otro secreto o binding.
4. Inspeccionar los **nombres** de los secretos productivos ya guardados. Este módulo
   usa `MP_ACCESS_TOKEN_PROD` y `MP_WEBHOOK_SECRET_PROD`. Si están guardados bajo otros
   nombres, adaptar las referencias del módulo antes de desplegar. No reemplazar ni
   regenerar secretos existentes.
5. Ejecutar únicamente `docs/mp-live-schema.sql` en la misma D1. No recrear la base,
   ni volver a cargar el catálogo si el vigente ya está sincronizado.
6. Generar el módulo y comprobarlo:

   ```sh
   node scripts/build-mp-worker.mjs
   node --check /tmp/lucasabraham-mp-deploy.mjs
   ```

7. Desplegar ese módulo en el Worker existente manteniendo sus bindings y secretos.
   Al guardar código desde el editor no pegar credenciales en el fuente.
8. Agregar estas variables no secretas:

   | Variable | Valor inicial |
   | --- | --- |
   | `MP_LIVE_MODE` | `validation` |
   | `MP_VALIDATION_AMOUNT` | `200` |
   | `MP_APP_URL` | `https://lucasabraham1996-cmd.github.io/photos/` |

9. En la integración productiva de Mercado Pago, configurar el evento
   **Order (Mercado Pago)** para:
   `https://lucasabraham-ph-api.lucasantonioabraham.workers.dev/webhook/mp/live`.
   Conservar el webhook de prueba `/webhook/mp` y su secreto.

Si falta alguna credencial productiva, los cobros permanecen cerrados.
No utilizar valores de prueba en las variables productivas.
Las credenciales permanecen dentro de Cloudflare; no van a GitHub ni al navegador.

## Compra real de $200

1. Abrir `/validation` en el Worker. No publicar la rama en GitHub Pages.
2. Ingresar la clave de administración allí; solo se usa en memoria para ese intento.
3. Preparar la foto. El servidor elige una del catálogo vigente y valida su precio.
   Solo para esta validación aplica $200, sin modificar los precios del catálogo.
4. Confirmar el bloqueo previo (HTTP 403, sin entregar bytes de la foto).
5. Completar personalmente el pago con una cuenta real diferente de la vendedora.
   El agente no pulsa el pago final ni ingresa tarjetas.
6. Volver a la página. Comprueba automáticamente el pago y descarga la fotografía
   cuando la order está `processed/accredited`, con el importe íntegro pagado.
7. Confirmar que el archivo abrió correctamente y la notificación productiva llegó.
   No registrar la verificación como completada si falta alguna de estas evidencias.

`POST /api/live-diagnostics`, autorizado mediante `X-Setup-Key`, muestra los últimos
pedidos de validación y su evidencia, sin revelar claves ni tokens de descarga.
D1 registra bloqueo previo, comprobación de pago, webhook autenticado y recepción
completa de una imagen válida de Drive.

## Control de apertura

El backend comienza con `disabled` si `MP_LIVE_MODE` no está definido.
Con `validation`, crear un cobro requiere `MP_SETUP_KEY`; solo permite una foto de
$100 a $500 (por defecto $200). Un parámetro de URL no autoriza cobros.

Incluso si se configura `MP_LIVE_MODE=public` antes de tiempo, el Worker mantiene
los cobros públicos bloqueados si no existe una validación en D1 con estas pruebas:

- descarga bloqueada antes del pago;
- pago real acreditado, referencia, vendedor, aplicación, moneda e importe coincidentes;
- webhook productivo autenticado de una orden acreditada;
- fotografía completa recibida con firma de imagen válida.

Solo después de revisar el circuito real y el archivo descargado: publicar la rama
revisada de la aplicación y habilitar el modo público. El botón de WhatsApp permanece.
No se ejecutó esta apertura en esta sesión.

## Seguridad y límites actuales

- El servidor calcula los precios desde D1 y conserva el UUID de idempotencia y el
  pedido antes de contactar Mercado Pago. Reintentar no cambia la orden ni su importe.
- La clave de administración no se solicita en el checkout público.
- Cada comprador tiene un recibo aleatorio de 256 bits; D1 guarda solamente su hash.
  No incluir ese recibo en el historial de Firebase/Apps Script.
- Cada descarga consulta de nuevo el pago; pendientes, rechazos, reembolsos y datos
  que no coinciden bloquean la entrega. Los parámetros de retorno no acreditan pagos.
- Los originales de Drive siguen públicos, tal como están en la web existente.
  Este control protege las descargas de este checkout; no restringe enlaces de Drive
  que ya sean conocidos. Cambiar esa accesibilidad requeriría otra migración.
- La recuperación automática usa el mismo navegador. Conservar su recibo local;
  no se agregó envío de recibos por email.

## Verificación local

```sh
node scripts/check-app-js.cjs
node --test tests/mercadopago-*.test.*
node scripts/build-mp-worker.mjs
node --check /tmp/lucasabraham-mp-deploy.mjs
```

34 pruebas correctas: 13 de precios y 21 de flujo, firma, SQLite, idempotencia,
rechazos, reembolsos y aplicación → Worker → SQLite.
Mercado Pago y Drive se simulan en estas pruebas. **No prueban un cobro real.**

Referencias oficiales utilizadas:
- https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/create-order
- https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/notifications
- https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/web-integration/configure-back-urls
- https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/payment-management/status/order-status
