# Mercado Pago: carrito completo y álbumes, solo modo PRUEBA

**Actualización:** la preparación para una compra real privada está en
[`mp-live-validation.md`](mp-live-validation.md). Este documento conserva las
instrucciones del sandbox; no describe la configuración productiva nueva.

**No fusionar ni usar con compradores reales todavía.** La web pública sigue en `main`, sin cambios. El botón experimental aparece únicamente si abrís la app con `?mp_trial=1` antes del hash (por ejemplo, `/photos/?mp_trial=1#/galeria`).

## Opciones implementadas

| Modalidad | Importe calculado por Cloudflare |
| --- | --- |
| Foto individual | $2.000 |
| 3–4 fotos | 10% OFF en cada foto |
| 5 o más fotos | 15% OFF en cada foto |
| Descuento web | porcentaje vigente, por álbum, sin aplicar a las excepciones del administrador |
| Cupón | porcentaje válido y activo, hasta 90% OFF, aplicado al total digital |
| Impresión 10×15 | +$3.000 por cada foto señalada para imprimir, sumado después de descuentos digitales |
| Álbum completo | `fullPrice` indicado en la galería, con descuento web si corresponde |
| Compras digitales mixtas | Fotos seleccionadas en el carrito, incluso de distintos álbumes |

Los cupones **no** se aplican al álbum completo porque el checkout de álbum vigente en la app tampoco los ofrece allí. Las tarifas de cobertura, sesión y fotografía fuera del carrito siguen siendo **solicitudes de reserva**, no ventas de archivos descargables.

## Protección del precio

El navegador **solo manda IDs de fotos, ID de álbum, código de cupón y selección de impresiones**. Cloudflare calcula el precio usando el catálogo sincronizado por el administrador en D1. El total mostrado debe coincidir con el calculado; en caso contrario, se rechaza la orden sin cobrarla.

## Preparación en Cloudflare

1. Crear una base de datos Cloudflare D1 (por ejemplo, `la-fotos-pedidos-test`).
2. Ejecutar **ambos** esquemas: `docs/mp-test-schema.sql` y **después** `docs/mp-multi-schema.sql`.
3. En Workers → `lucasabraham-ph-api` → Bindings, agregar D1 binding de nombre exacto `LA_ORDERS_DB` apuntando a la base creada.
4. Conservar los secretos existentes `MP_ACCESS_TOKEN_TEST`, `MP_WEBHOOK_SECRET_TEST`, `MP_SETUP_KEY` (nunca pegarlos en GitHub).
5. Guardar una copia del Worker actual y desplegar `cloudflare/worker-mp-trial.js`.
6. Mantener el webhook de Orders en modo prueba a `/webhook/mp`.

## Preparación en el administrador de la app

1. Probar la rama de desarrollo (no la pública) en una vista previa con `?mp_trial=1`.
2. Ingresar al administrador y presionar **Sincronizar catálogo con Mercado Pago**.
3. Escribir `MP_SETUP_KEY` cuando se solicite. El secreto se envía por HTTPS, no se guarda localmente.
4. Si cambiás galerías, cupones o descuentos, **volvé a sincronizar** antes de cobrar con la versión piloto.

El servidor rechazará catálogos sin enlaces de Google Drive válidos o con fotos duplicadas. Revisa los mensajes en el panel para detectar archivos faltantes.

## Probar distintos escenarios
- Una foto digital a $2.000.
- 3 fotos con 10% OFF (total $5.400).
- 5 fotos con 15% OFF (total $8.500).
- 3 fotos con descuento web de 10% más cupón del 20% (total $3.888).
- 3 fotos con descuento web de 10%, cupón 20% y 2 impresiones (total $9.888).
- Álbum de $60.000, o $54.000 si lleva descuento web del 10%.
- Cupón inexistente, foto que no pertenece a un álbum y precio manipulado: deben rechazarse.
- Sin pago, el botón de descarga no aparece. Con estado `processed/accredited`, se muestra el listado de archivos autorizados.

**Nota sobre entregas:** para compras de muchas fotos o álbum completo, se entrega una **lista individual de enlaces de descarga**, no un ZIP único. Para impresión física, Mercado Pago cobra el adicional pero la entrega/retiro se coordina manualmente. Las imágenes de Drive siguen públicas por la decisión del usuario: el control del checkout no impide descargar un original a quien ya conozca su enlace.

## Pendientes antes de vender de verdad
- Integración de facturación automática C con ARCA y verificación de datos de Ingresos Brutos.
- Pasar a credenciales productivas, webhook productivo, pruebas reales y política de reembolsos.
- Sustituir `MP_SETUP_KEY` de piloto (no apto para público) por autenticación/checkout público con rate limiting, antifraude, idempotencia y recuperación de compras por email.
- Sincronizar automáticamente cambios del administrador o mostrar advertencia cuando los precios no coincidan.
- ZIP por álbum para descarga masiva, considerando límites de Google Drive/Cloudflare.
- Registrar órdenes e impresiones en el administrador y coordinar entregas físicas.
- Resguardar privacidad de compradores y auditar controles de acceso.

## Estado de pruebas
El JS de la app y del Worker pasan validación sintáctica. 12 casos de cálculo del servidor evaluados, todos correctos; no equivalen a una prueba real de usuario final. No se desplegó esta rama en Cloudflare ni GitHub Pages.
