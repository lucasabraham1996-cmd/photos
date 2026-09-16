from pathlib import Path
import re

path = Path('index.html')
s = path.read_text(encoding='utf-8')

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
        const whatsappUrl=safeOrderWhatsappUrl(pkg);
        orderSavingRef.current=true;setCheckoutSaving(true);setCheckoutSaveError('');
        try{
            // v120: conservar una copia síncrona antes de salir de la app.
            // Así Finalizar compra no depende de la latencia de Firebase/Apps Script.
            try{
                saveLocalOrders(mergeOrders(readLocalOrders(),[pkg.orderData]));
                savePendingOrders(mergeOrders(readPendingOrders(),[compactOrderForScript(pkg.orderData)]));
                localStorage.setItem('LA_LAST_ORDER_RECEIPT',JSON.stringify({id:fixedCode,date:pkg.orderData.date,itemCount:pkg.orderData.items.length,total:pkg.orderData.total,whatsappUrl,confirmed:false,pendingSync:true}));
                localStorage.setItem('LA_RECOVER_CART',JSON.stringify(cart));
            }catch(localErr){console.warn('No se pudo preparar el respaldo local del pedido.',localErr)}

            // Abrir el destino inmediatamente mientras seguimos en el gesto del usuario.
            // Esto evita que los navegadores móviles bloqueen la apertura y elimina la espera percibida.
            const opened=window.open(whatsappUrl,'_blank');
            if(!opened) window.location.href=whatsappUrl;

            // La sincronización remota continúa sin bloquear la apertura de WhatsApp.
            saveOrderRemote(pkg.orderData).then(status=>{
                const confirmed=status&&Boolean(status.firebase||status.script);
                try{
                    localStorage.setItem('LA_LAST_ORDER_RECEIPT',JSON.stringify({id:fixedCode,date:pkg.orderData.date,itemCount:pkg.orderData.items.length,total:pkg.orderData.total,whatsappUrl,confirmed,pendingSync:!confirmed}));
                    if(confirmed)localStorage.removeItem('LA_RECOVER_CART');
                }catch(_e){}
                if(confirmed){
                    setAdminMessage(`Pedido ${fixedCode} guardado correctamente.`);
                    setCart([]);setCheckoutOpen(false);setAppliedCoupon(null);setCheckoutCoupon('');setCouponMessage('');setCheckoutPrint(false);setPrintedPhotoIds([]);
                }else{
                    setCheckoutSaveError(`El pedido ${fixedCode} quedó guardado en este dispositivo y se sincronizará automáticamente cuando haya conexión disponible.`);
                }
            }).catch(err=>{
                console.warn('Sincronización diferida del pedido:',err);
                setCheckoutSaveError(`El pedido ${fixedCode} quedó guardado en este dispositivo y pendiente de sincronización.`);
            }).finally(()=>{orderSavingRef.current=false;setCheckoutSaving(false)});
        }catch(err){
            orderSavingRef.current=false;setCheckoutSaving(false);
            const message=`No se pudo preparar el pedido ${fixedCode}. Tus fotos siguen seleccionadas. ${String(err&&err.message||err)}`;
            setCheckoutSaveError(message);alert(message);
        }
    };

    const addClubProduct'''

new_s, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit(f'No se encontró sendOrder exactamente una vez (encontrado: {count}).')

new_s = new_s.replace('v118-team-dominant-colors', 'v120-fast-checkout', 1)
path.write_text(new_s, encoding='utf-8')
print('Fast checkout v120 aplicado.')
