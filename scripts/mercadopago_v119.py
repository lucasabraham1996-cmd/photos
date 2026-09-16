from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'v119-mercadopago-checkout' in s:
    print('Mercado Pago v119 already applied')
    raise SystemExit(0)

s = s.replace('v118-team-dominant-colors', 'v119-mercadopago-checkout')

s = s.replace(
    "{ icon: 'fa-whatsapp', iconPrefix: 'fab', title: 'Enviá el pedido por WhatsApp', text: 'Al finalizar, la app genera un código único y abre WhatsApp con todo el detalle del pedido.' },",
    "{ icon: 'fa-credit-card', title: 'Pagá de forma segura', text: 'Al finalizar, la app genera un código único y abre Mercado Pago con el importe exacto de tu pedido.' },"
)

s = s.replace(
    'React.createElement(\"i\", { className: \"fab fa-whatsapp mr-2\" }),\n                    \"Finalizar compra\"),',
    'React.createElement(\"i\", { className: \"fas fa-wallet mr-2\" }),\n                    \"Pagar con Mercado Pago\"),'
)
s = s.replace(
    'React.createElement(\"p\", { className: \"text-center text-[11px] text-sky-100/65 leading-relaxed mt-3\" }, \"No necesitás registrarte para comprar. Se abre WhatsApp con el pedido listo; enviá el mensaje y adjuntá el comprobante.\")))',
    'React.createElement(\"p\", { className: \"text-center text-[11px] text-sky-100/65 leading-relaxed mt-3\" }, \"No necesitás registrarte. Mercado Pago procesa el cobro y la app conserva tu código de pedido.\")))'
)
s = s.replace(
    'className:\"checkout-floating-cta\" }, React.createElement(\"i\", { className:\"fab fa-whatsapp\" }), \"Finalizar compra\")',
    'className:\"checkout-floating-cta\" }, React.createElement(\"i\", { className:\"fas fa-wallet\" }), \"Pagar con Mercado Pago\")'
)

pattern = re.compile(r"    const sendOrder=async\(e\)=>\{.*?\n    \};\n\n    const addClubProduct", re.S)
replacement = r'''    const sendOrder=async(e)=>{
        if(e&&e.preventDefault)e.preventDefault();
        if(orderSavingRef.current)return;
        if(!cart.length||!selectedPhotos.length){alert('Seleccioná al menos una foto antes de comprar.');return}
        if(checkoutWantsPoints&&!customerDetailsSaved){setCustomerDetailsOpen(true);alert('Guardá los datos del Club o elegí continuar sin sumar puntos.');return}
        if(checkoutPrint&&!printSelectedPhotos.length){alert('Elegí al menos una foto para imprimir o desactivá la impresión.');return}
        const fixedCode=checkoutOrderCode||newOrderCode();
        if(!checkoutOrderCode)setCheckoutOrderCode(fixedCode);
        const pkg=buildOrderPackage(fixedCode);
        orderSavingRef.current=true;setCheckoutSaving(true);setCheckoutSaveError('');
        try{
            const status=await saveOrderRemote(pkg.orderData);
            const confirmed=status.firebase||status.script;
            if(!confirmed)throw new Error(`No se pudo guardar el pedido ${fixedCode}. Probá nuevamente antes de pagar.`);
            const endpoint='https://us-central1-lucasabraham-b84aa.cloudfunctions.net/createMercadoPagoPreference';
            const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({orderId:fixedCode})});
            const payment=await response.json().catch(()=>({}));
            if(!response.ok||!payment.initPoint)throw new Error(payment.message||'Mercado Pago no pudo iniciar el cobro.');
            try{localStorage.setItem('LA_LAST_ORDER_RECEIPT',JSON.stringify({id:fixedCode,date:pkg.orderData.date,itemCount:pkg.orderData.items.length,total:pkg.orderData.total,paymentUrl:payment.initPoint,confirmed:true,paymentProvider:'mercadopago'}));localStorage.setItem('LA_RECOVER_CART',JSON.stringify(cart))}catch(_e){}
            setAdminMessage(`Pedido ${fixedCode} guardado. Abriendo Mercado Pago...`);
            window.location.href=payment.initPoint;
        }catch(err){
            const message=`No pudimos abrir Mercado Pago para el pedido ${fixedCode}. ${String(err&&err.message||err)}`;
            setCheckoutSaveError(message);
            console.error('Mercado Pago:',err);
        }finally{orderSavingRef.current=false;setCheckoutSaving(false)}
    };

    const addClubProduct'''

s, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit('No se encontró la función sendOrder esperada; no se modificó index.html')

p.write_text(s, encoding='utf-8')
print('Mercado Pago v119 applied')
