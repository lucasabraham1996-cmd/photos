# Compra digital de prueba — lucasabraham.ph

**Estado: piloto técnico, NO apto para ventas reales.** La rama `feature/mercadopago-descarga-prueba` no cambia la web pública y conserva el flujo WhatsApp. El botón nuevo aparece solamente con `?mp_trial=1` (antes del fragmento `#/galeria`). Solo admite **una foto digital de $2.000**, sin descuentos, cupones o impresiones.

## Qué cambia
- Checkout Pro en test desde el carrito existente. El precio de $2.000 se fija en el Worker, **no** se acepta el precio que manda el navegador.
- Orden persistida en D1 vinculada al ID de foto, al ID de Google Drive y al token privado del comprador (almacenado como SHA-256).
- Webhook con firma HMAC (ID original o minúsculas; ambas variantes se verifican con la clave).
- Consulta a Mercado Pago del estado de la orden. Solo si `processed/accredited`, el comprador puede acceder a la descarga.
- Se mantienen las marcas de agua, las carpetas existentes y el proceso por WhatsApp.
- **Advertencia:** las imágenes de Drive siguen públicas, por decisión actual de negocio. La descarga sólo está condicionada dentro del circuito de compra; cualquiera que obtenga el enlace público original aún puede descargarlo.

## Requisitos antes de probar
1. Crear en Cloudflare → D1 una base de datos (p. ej. `la-ventas-prueba`).
2. Ejecutar en la consola SQL de D1 el contenido de `docs/mp-test-schema.sql`.
3. En `lucasabraham-ph-api` agregar binding de D1 con nombre exacto `LA_ORDERS_DB`.
4. Mantener los secretos `MP_ACCESS_TOKEN_TEST`, `MP_WEBHOOK_SECRET_TEST` y `MP_SETUP_KEY` existentes. **No subirlos a GitHub**.
5. Reemplazar el código de Cloudflare Worker por `cloudflare/worker-mp-trial.js` solo cuando se esté listo para probar. Hacer copia del Worker actual antes: este archivo sustituye la página anterior de diagnóstico por un endpoint `/health`.
6. En Mercado Pago, modo prueba, mantener Webhook `https://lucasabraham-ph-api.lucasantonioabraham.workers.dev/webhook/mp`, evento Order.
7. Para probar la interfaz sin publicar: usar vista previa de la rama, o fusionar tras revisar que el marcador `mp_trial=1` sigue ocultando el piloto al público.

## Funcionamiento
- El comprador elige una foto digital de $2.000 (sin promoción), abre el carrito y usa la acción piloto.
- La página solicita la clave `MP_SETUP_KEY` **solo a quien está probando**. No queda almacenada.
- El Worker crea la orden, guarda la selección y devuelve un link de checkout. El usuario abre Mercado Pago en otra pestaña con comprador ficticio.
- De vuelta en la app, `Verificar pago` consulta al servidor. Si hay acreditación, aparece `Descargar foto`. La sesión de prueba puede recuperarse desde localStorage.
- La API solo libera el redireccionamiento para el token vinculado a esa orden y si verificó la acreditación directamente en Mercado Pago.

## Limitaciones y trabajo pendiente
- No habilitar sin integrar la emisión de **factura C** a ARCA y revisar el número de IIBB.
- Antes de producción, validar promociones, descuentos web, cupones, combos por cantidad, impresiones y álbum completo del lado servidor.
- Proteger el modo productivo con medidas antiabuso/rate limit, registros de auditoría, recuperación de compra por email, soporte de ZIP para varias fotos y test completo móvil/escritorio.
- La API de Google Drive no está integrada: en piloto se usa el enlace de un original **público** ya presente en la galería. El botón puede pasar por confirmación/intersticial de Drive en archivos grandes.
- Las pruebas no emitirán factura ni generan ingresos reales.
- No modificar permisos actuales de Drive mientras la app siga usando las URLs públicas.

## Smoke tests
- Sin `?mp_trial=1`: sólo WhatsApp.
- Con `?mp_trial=1`: para una foto sin descuentos aparece el botón piloto.
- Código `MP_SETUP_KEY` incorrecto: HTTP 401.
- El cliente intenta cambiar el importe: el Worker fija $2.000.
- Orden no pagada: no entrega descarga.
- Orden `processed/accredited`: habilita redirección al original.
- Firma de webhook incorrecta: HTTP 401.
- Verificar que las galerías y las marcas de agua siguen visibles.

