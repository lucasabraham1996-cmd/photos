# Mercado Pago · lucasabraham.ph

La integración está preparada para Checkout Pro y Firebase Functions.

## Seguridad

Nunca pegues el Access Token de Mercado Pago dentro de `index.html`, GitHub ni archivos públicos.
Las credenciales se guardan como secretos de Firebase Functions.

## 1. Crear/usar una aplicación de Mercado Pago

Desde Mercado Pago Developers > Tus integraciones, usa una aplicación con Checkout Pro.
Necesitarás:

- Access Token de producción.
- Clave secreta de Webhooks.

## 2. Configurar secretos en Firebase

Con Firebase CLI autenticado en el proyecto `lucasabraham-b84aa`:

```bash
firebase functions:secrets:set MP_ACCESS_TOKEN
firebase functions:secrets:set MP_WEBHOOK_SECRET
```

Pega cada valor únicamente cuando Firebase CLI lo solicite.

## 3. Desplegar Functions

```bash
cd functions
npm install
cd ..
firebase deploy --only functions:createMercadoPagoPreference,functions:mercadoPagoWebhook
```

Endpoints esperados:

- `https://us-central1-lucasabraham-b84aa.cloudfunctions.net/createMercadoPagoPreference`
- `https://us-central1-lucasabraham-b84aa.cloudfunctions.net/mercadoPagoWebhook`

## 4. Webhook de Mercado Pago

En Mercado Pago Developers > Tu integración > Webhooks:

- URL de producción: `https://us-central1-lucasabraham-b84aa.cloudfunctions.net/mercadoPagoWebhook`
- Evento: Pagos.

La Function valida `x-signature` usando la clave `MP_WEBHOOK_SECRET` y consulta el pago directamente a Mercado Pago antes de marcar el pedido.

## Flujo implementado

1. El cliente selecciona fotos y toca **Pagar con Mercado Pago**.
2. La app guarda primero el pedido en Firebase.
3. La Function lee el total real desde `artifacts/lucasabraham-ph-db/orders`.
4. La Function crea una preferencia de Checkout Pro.
5. El navegador abre Mercado Pago.
6. Mercado Pago envía el Webhook.
7. La Function verifica la firma y consulta el pago por API.
8. Si el pago está `approved` y el importe coincide con el pedido, Firebase se actualiza con `paid: true` y `paymentStatus: "pagado"`.

## Antes de pasar a producción

Realiza una compra de prueba y verifica en Firebase que el pedido cambie de `paymentStatus: "pendiente"` a `paymentStatus: "pagado"` solamente después de la aprobación real del pago.
