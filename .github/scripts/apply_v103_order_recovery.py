from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def replace_between(start,end,new):
    global s
    assert s.count(start)==1, (start,s.count(start))
    a=s.index(start); b=s.index(end,a+len(start))
    s=s[:a]+new+'\n'+s[b:]

# Keep transport metadata out of the immutable order fingerprint. A retry must
# not turn the same order into a different order merely because it was hydrated.
s=s.replace("'storageIncomplete','_firebasePath','appVersion'", "'storageIncomplete','_firebasePath','appVersion','compactTransport'",1)

# An Apps Script acknowledgement is not proof of persistence. Conversely, an
# unfamiliar acknowledgement is not proof of failure: verify the saved record.
replace_between('async function saveOrderRemote(order){','async function loadOrdersRemote(){', '''async function saveOrderRemote(order){
    const clean={...order,id:order.id||order.orderId||order.codigo||order.code,date:order.date||new Date().toISOString(),items:Array.isArray(order.items)?order.items:[]};
    if(!clean.id)throw new Error('Falta el código del pedido');
    const key=normalizeOrderCode(clean.id);
    if(LA_ORDER_SAVE_INFLIGHT.has(key))return LA_ORDER_SAVE_INFLIGHT.get(key);
    const work=(async()=>{
        await LAOrderOutbox.put(clean);
        saveLocalOrders(mergeOrders(readLocalOrders(),[clean]));
        const status={firebase:false,script:false,error:'',id:clean.id};
        try{await orderDeadline(saveOrderFirebase(clean));status.firebase=true}
        catch(e){status.error=String(e&&e.message||e);console.warn('Firebase no confirmó el pedido:',clean.id,e)}
        if(!status.firebase){
            const compact=compactOrderForScript(clean);
            const params={action:'createOrder',order:JSON.stringify(compact)};
            const encoded=new URLSearchParams(params).toString();
            if(encoded.length<=7000){
                try{
                    const response=await apiAction(params);
                    if(response&&(response.error||response.ok===false||response.success===false))throw new Error(String(response.error||'El respaldo rechazó el pedido'));
                    const verify=await apiAction({action:'getOrder',orderId:clean.id});
                    const found=verify&&verify.order;
                    const count=found?(Array.isArray(found.items)?found.items.length:Number(found.itemCount)||0):0;
                    if(!found||!sameOrderCode(found.id||found.orderId,clean.id)||count!==clean.items.length||Number(found.total)!==Number(clean.total))throw new Error('El respaldo no devolvió el pedido completo');
                    status.script=true;
                }catch(e){status.error=String(e&&e.message||e);console.warn('Apps Script no confirmó el pedido:',clean.id,e)}
            }else status.error='El respaldo alternativo no admite este tamaño; el pedido quedó conservado para reintentar Firebase.';
        }
        if(status.firebase||status.script){
            await LAOrderOutbox.remove(clean.id);
            savePendingOrders(readPendingOrders().filter(o=>!sameOrderCode(o.id,clean.id)));
        }else savePendingOrders(mergeOrders(readPendingOrders(),[compactOrderForScript(clean)]));
        window.LA_LAST_ORDER_SAVE_STATUS={...status,ordersPath:ORDERS_COLLECTION_PATH,at:new Date().toISOString(),appVersion:APP_VERSION};
        return status;
    })().finally(()=>LA_ORDER_SAVE_INFLIGHT.delete(key));
    LA_ORDER_SAVE_INFLIGHT.set(key,work);
    return work;
}''')

# Never strand a buyer at a blocking alert when both remote services are down.
# The WhatsApp message carries the actual selected-photo detail and the same ID.
replace_between('    const sendOrder=async(e)=>{','    const addClubProduct = () => {', '''    const sendOrder=async(e)=>{
        if(e&&e.preventDefault)e.preventDefault();
        if(orderSavingRef.current)return;
        if(!cart.length||!selectedPhotos.length){alert('Seleccioná al menos una foto antes de comprar.');return}
        if(!String(checkoutCustomerName||'').trim()||!normalizePhone(checkoutPhone)){setCustomerDetailsOpen(true);alert('Antes de finalizar, guardá tu nombre y apellido y un celular de contacto.');return}
        if(checkoutPrint&&!printSelectedPhotos.length){alert('Elegí al menos una foto para imprimir o desactivá la impresión.');return}
        const fixedCode=checkoutOrderCode||newOrderCode();
        if(!checkoutOrderCode)setCheckoutOrderCode(fixedCode);
        const pkg=buildOrderPackage(fixedCode);
        orderSavingRef.current=true;setCheckoutSaving(true);setCheckoutSaveError('');
        try{
            const status=await saveOrderRemote(pkg.orderData);
            const confirmed=status.firebase||status.script;
            const message=confirmed?'':`No se pudo confirmar el guardado automático del pedido ${fixedCode}. Podés enviarlo igualmente por WhatsApp con el detalle de las fotos. Conservá este código para evitar duplicados.`;
            if(!confirmed)setCheckoutSaveError(message);
            const whatsappUrl=confirmed?safeOrderWhatsappUrl(pkg):`https://api.whatsapp.com/send?phone=${SELLER_PHONE}&text=${encodeURIComponent(pkg.msg+'\\n\\n⚠️ El guardado automático quedó pendiente de confirmación. Conservá este código para evitar duplicados.')}`;
            try{localStorage.setItem('LA_LAST_ORDER_RECEIPT',JSON.stringify({id:fixedCode,date:pkg.orderData.date,itemCount:pkg.orderData.items.length,total:pkg.orderData.total,whatsappUrl,confirmed}));if(confirmed)localStorage.removeItem('LA_RECOVER_CART')}catch(e){}
            if(confirmed){setAdminMessage(`Pedido ${fixedCode} guardado correctamente.`);setCart([]);setCheckoutOpen(false);setAppliedCoupon(null);setCheckoutCoupon('');setCouponMessage('');setCheckoutPrint(false);setPrintedPhotoIds([])}
            window.location.href=whatsappUrl;
        }catch(err){const message=`No se pudo conservar el pedido ${fixedCode}. Tus fotos siguen seleccionadas. ${String(err&&err.message||err)}`;setCheckoutSaveError(message);alert(message)}
        finally{orderSavingRef.current=false;setCheckoutSaving(false)}
    };
''')
s=s.replace('const APP_VERSION = "v102-reliable-orders";', 'const APP_VERSION = "v103-order-recovery";',1)
s=s.replace('<meta name="app-version" content="v102-reliable-orders" />','<meta name="app-version" content="v103-order-recovery" />',1)
p.write_text(s,encoding='utf-8')
print('v103 order recovery patched')
