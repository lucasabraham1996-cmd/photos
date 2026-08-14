from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'v71-club-beneficios-print-select' in s:
    print('v71 already applied')
    raise SystemExit(0)

# Version
s = re.sub(r'<meta name="app-version" content="[^"]+"\s*/>', '<meta name="app-version" content="v71-club-beneficios-print-select" />', s, count=1)

# Styles
css = r'''
<style id="v71-club-benefits">
@keyframes clubSaveFlow{0%{background-position:0% 50%;box-shadow:0 10px 24px rgba(249,115,22,.20)}50%{background-position:100% 50%;box-shadow:0 12px 30px rgba(37,99,235,.28)}100%{background-position:0% 50%;box-shadow:0 10px 24px rgba(16,185,129,.20)}}
.save-customer-btn{background:linear-gradient(110deg,#f97316,#ef4444,#2563eb,#10b981,#f97316)!important;background-size:280% 280%!important;color:#fff!important;border:1px solid rgba(255,255,255,.25)!important;animation:clubSaveFlow 5s ease infinite!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.30),0 12px 28px rgba(37,99,235,.18)!important}
.club-benefits-shell{position:relative;overflow:hidden;border:1px solid rgba(249,115,22,.22);border-radius:26px;background:radial-gradient(circle at 10% 0%,rgba(249,115,22,.16),transparent 34%),linear-gradient(145deg,rgba(15,15,18,.98),rgba(5,5,8,.98));padding:18px;box-shadow:0 22px 55px rgba(0,0,0,.28)}
.club-benefits-shell:before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(120deg,transparent 0%,rgba(255,255,255,.035) 45%,transparent 70%)}
.club-points-btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:15px;padding:11px 15px;font-weight:950;color:#fff;background:linear-gradient(135deg,#f97316,#ef4444 62%,#fb7185);border:1px solid rgba(255,255,255,.22);box-shadow:inset 0 1px 0 rgba(255,255,255,.30),0 12px 28px rgba(239,68,68,.18)}
.club-product-card{border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(0,0,0,.34);overflow:hidden;display:flex;flex-direction:column;min-width:0}
.club-product-image{aspect-ratio:16/9;width:100%;object-fit:cover;background:#0a0a0d}
.club-product-placeholder{aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,rgba(249,115,22,.12),rgba(37,99,235,.09));font-size:30px;color:#fb923c}
.club-product-body{padding:12px;display:flex;flex-direction:column;gap:7px;flex:1}
.club-points-chip{display:inline-flex;align-items:center;gap:6px;width:max-content;border-radius:999px;padding:5px 9px;font-size:10px;font-weight:950;color:#fed7aa;background:rgba(249,115,22,.13);border:1px solid rgba(249,115,22,.23)}
.club-redeem-btn{width:100%;border-radius:12px;padding:9px 10px;font-size:11px;font-weight:950;background:rgba(249,115,22,.14);border:1px solid rgba(249,115,22,.28);color:#fed7aa}
.club-redeem-btn.ready{background:linear-gradient(135deg,#f97316,#ea580c);color:#fff;border-color:rgba(255,255,255,.18)}
.club-redeem-btn:disabled{opacity:.45}
.club-empty{border:1px dashed rgba(255,255,255,.13);border-radius:18px;padding:20px;text-align:center;color:#a3a3a3;background:rgba(0,0,0,.22)}
.club-account-card{border:1px solid rgba(249,115,22,.22);border-radius:17px;background:rgba(249,115,22,.08);padding:13px}
.print-photo-picker{border:1px solid rgba(96,165,250,.22);border-radius:16px;background:rgba(15,23,42,.55);padding:10px;margin:-3px 0 10px}
.print-photo-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;max-height:210px;overflow-y:auto;padding:2px}
.print-photo-option{display:grid;grid-template-columns:48px minmax(0,1fr) auto;align-items:center;gap:8px;text-align:left;border-radius:12px;padding:6px;background:rgba(0,0,0,.32);border:1px solid rgba(255,255,255,.08);min-width:0}
.print-photo-option.active{border-color:rgba(96,165,250,.68);background:rgba(37,99,235,.16);box-shadow:0 0 0 2px rgba(37,99,235,.08)}
.print-photo-option img{width:48px;height:48px;border-radius:9px;object-fit:cover;background:#050505}
.print-order-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 8px;font-size:10px;font-weight:950;background:rgba(59,130,246,.14);border:1px solid rgba(96,165,250,.30);color:#bfdbfe}
.club-order-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 8px;font-size:10px;font-weight:950;background:rgba(249,115,22,.14);border:1px solid rgba(251,146,60,.30);color:#fed7aa}
@media(max-width:640px){
 .club-benefits-shell{padding:13px;border-radius:20px}
 .club-product-body{padding:10px}
 .print-photo-grid{grid-template-columns:1fr;max-height:175px}
 .print-photo-option{grid-template-columns:42px minmax(0,1fr) auto}
 .print-photo-option img{width:42px;height:42px}
}
</style>
'''
if '</head>' not in s:
    raise SystemExit('head closing tag missing')
s = s.replace('</head>', css + '</head>', 1)

# State: print selection
anchor = '    const [checkoutPrint, setCheckoutPrint] = useState(false);\n'
if anchor not in s:
    raise SystemExit('checkoutPrint state anchor missing')
s = s.replace(anchor, anchor + '    const [printedPhotoIds, setPrintedPhotoIds] = useState([]);\n', 1)

# Club state
anchor = '    const [priceSettings, setPriceSettings] = useState(defaultPriceSettings());\n'
club_states = '''    const [clubProducts, setClubProducts] = useState([]);\n    const [newClubProductName, setNewClubProductName] = useState("");\n    const [newClubProductDescription, setNewClubProductDescription] = useState("");\n    const [newClubProductPoints, setNewClubProductPoints] = useState(3);\n    const [newClubProductImage, setNewClubProductImage] = useState("");\n    const [clubPointsOpen, setClubPointsOpen] = useState(false);\n    const [clubLookupDni, setClubLookupDni] = useState("");\n    const [clubLookupLoading, setClubLookupLoading] = useState(false);\n    const [clubLookupResult, setClubLookupResult] = useState(null);\n    const [clubMessage, setClubMessage] = useState("");\n    const [clubRedeeming, setClubRedeeming] = useState("");\n'''
if anchor not in s:
    raise SystemExit('priceSettings state anchor missing')
s = s.replace(anchor, anchor + club_states, 1)

# Load shared club products in both initial load and subscription
needle = '''            if (Array.isArray(state.highlightIds))\n                setHighlightIds(state.highlightIds);'''
if s.count(needle) < 2:
    raise SystemExit(f'highlight shared anchors too few: {s.count(needle)}')
s = s.replace(needle, needle + '''\n            if (Array.isArray(state.clubProducts))\n                setClubProducts(state.clubProducts);''')

# Persist club products centrally
anchor = '''    useEffect(() => { saveDiscountSettings(discountSettings); if (sharedReady)\n        saveSharedAdminState({ discountSettings }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar el descuento.'); }); }, [discountSettings, sharedReady]);\n'''
club_effect = '''    useEffect(() => {\n        if (!sharedReady) return;\n        const timer = setTimeout(() => {\n            saveSharedAdminState({ clubProducts }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar el Club de beneficios.'); });\n        }, 450);\n        return () => clearTimeout(timer);\n    }, [clubProducts, sharedReady]);\n'''
if anchor not in s:
    raise SystemExit('discount effect anchor missing')
s = s.replace(anchor, anchor + club_effect, 1)

# Customer stats / points engine
pattern = re.compile(r'''    const customerDniStats = useMemo\(\(\) => \{.*?    const adminOrderLedger = useMemo''', re.S)
replacement = r'''    const clubAccountFromOrders = (list, rawDni) => {
        const dni = String(rawDni || '').replace(/\D/g, '');
        const account = { dni, name:'', phone:'', purchases:0, spent:0, pending:0, cancelled:0, prints:0, redeemedPoints:0, redemptions:0, earnedPoints:0, points:0 };
        if (!dni) return account;
        mergeOrders(list || []).forEach(o => {
            if (String(o.dni || o.customerDni || '').replace(/\D/g, '') !== dni) return;
            const status = norm(o.status || o.estado || '');
            const cancelled = isTruthyStatus(o.rejected) || ['rechazado','cancelado','anulado','no pagado','no_pagado'].includes(status);
            const isRedemption = o.type === 'benefit_redemption' || o.benefitRedemption === true;
            account.name = String(o.customerName || o.nombreApellido || account.name || '').trim();
            account.phone = String(o.phone || o.celular || account.phone || '').replace(/\D/g, '');
            if (isRedemption) {
                if (!cancelled) {
                    account.redeemedPoints += Math.max(0, Number(o.redeemedPoints) || 0);
                    account.redemptions += 1;
                }
                return;
            }
            const confirmed = isTruthyStatus(o.delivered) || ['entregado','cargado_y_entregado','pagado'].includes(status);
            if (cancelled) account.cancelled += 1;
            else if (confirmed) {
                account.purchases += 1;
                account.spent += Math.max(0, Number(o.total) || 0);
                account.prints += Math.max(0, Number(o.printCount) || (o.printRequested ? 1 : 0));
            } else account.pending += 1;
        });
        account.earnedPoints = Math.floor(account.spent / 10000) * 3;
        account.points = Math.max(0, account.earnedPoints - account.redeemedPoints);
        return account;
    };
    const customerDniStats = useMemo(() => {
        const dnis = new Set();
        mergeOrders(orders).forEach(o => {
            const dni = String(o.dni || o.customerDni || '').replace(/\D/g, '');
            if (dni) dnis.add(dni);
        });
        return Array.from(dnis).map(dni => clubAccountFromOrders(orders, dni)).sort((a,b) => b.points - a.points || b.spent - a.spent || b.purchases - a.purchases);
    }, [orders]);
    const adminOrderLedger = useMemo'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit(f'customer stats replacement count {n}')

# Print totals select only specific photos
old = '''    const checkoutDigitalTotal = Math.round(total * (1 - couponPercent / 100));\n    const printSurcharge = checkoutPrint ? cart.length * PRINT_SURCHARGE_PER_PHOTO : 0;\n    const checkoutTotal = checkoutDigitalTotal + printSurcharge;'''
new = '''    const checkoutDigitalTotal = Math.round(total * (1 - couponPercent / 100));\n    const printSelectedPhotos = selectedPhotos.filter(p => printedPhotoIds.includes(p.id));\n    const printSurcharge = checkoutPrint ? printSelectedPhotos.length * PRINT_SURCHARGE_PER_PHOTO : 0;\n    const checkoutTotal = checkoutDigitalTotal + printSurcharge;'''
if old not in s:
    raise SystemExit('print totals anchor missing')
s = s.replace(old, new, 1)

# Cart toggle also removes a print selection
old = '''    const toggle = (id) => setCart(c => c.includes(id) ? c.filter(x => x !== id) : [...c, id]);'''
new = '''    const toggle = (id) => {\n        const removing = cart.includes(id);\n        setCart(c => c.includes(id) ? c.filter(x => x !== id) : [...c, id]);\n        if (removing) setPrintedPhotoIds(ids => ids.filter(x => x !== id));\n    };\n    const togglePrintedPhoto = (id) => setPrintedPhotoIds(ids => ids.includes(id) ? ids.filter(x => x !== id) : [...ids, id]);'''
if old not in s:
    raise SystemExit('toggle cart anchor missing')
s = s.replace(old, new, 1)

# Reset print selection when opening checkout
old = '''        setCheckoutPrint(false);\n        setCustomerDetailsOpen(false);'''
new = '''        setCheckoutPrint(false);\n        setPrintedPhotoIds([]);\n        setCustomerDetailsOpen(false);'''
if old not in s:
    raise SystemExit('openCheckout print reset anchor missing')
s = s.replace(old, new, 1)

# WhatsApp print detail
old = '''        if (cleanDni) msg += `${EM.point} *DNI:* ${cleanDni}${checkoutWantsPoints ? " · Suma puntos" : ""}\n`;\n        if (checkoutPrint) msg += `${EM.image} *Fotos impresas:* Sí · ${cart.length} x ${formatPrice(PRINT_SURCHARGE_PER_PHOTO)} = ${formatPrice(printSurcharge)}\n`;\n        msg += `\n`;'''
new = '''        if (cleanDni) msg += `${EM.point} *DNI:* ${cleanDni}${checkoutWantsPoints ? " · Acumula puntos del Club" : ""}\n`;\n        if (printSelectedPhotos.length) {\n            msg += `${EM.image} *IMPRESIÓN 10x15:* ${printSelectedPhotos.length} foto${printSelectedPhotos.length === 1 ? '' : 's'} · ${formatPrice(PRINT_SURCHARGE_PER_PHOTO)} c/u = ${formatPrice(printSurcharge)}\n`;\n            printSelectedPhotos.forEach(p => { msg += `   ↳ ${p.albumName} - ${p.name} - Código ${p.code}\n`; });\n        }\n        msg += `\n`;'''
if old not in s:
    raise SystemExit('whatsapp print anchor missing')
s = s.replace(old, new, 1)

# Order print data
old = '''            printRequested: Boolean(checkoutPrint),\n            printSurchargePerPhoto: PRINT_SURCHARGE_PER_PHOTO,\n            printSurcharge,\n            items: selectedPhotos.map(p => ({ id: p.id, albumName: p.albumName, subAlbumName: p.subAlbumName || '', name: p.name, code: p.code, url: p.url, driveLink: p.rawUrl || p.fullUrl || p.url, price: p.price })),'''
new = '''            printRequested: printSelectedPhotos.length > 0,\n            printFormat: '10x15 cm',\n            printCount: printSelectedPhotos.length,\n            printedPhotoIds: printSelectedPhotos.map(p => p.id),\n            printedItems: printSelectedPhotos.map(p => ({ id:p.id, albumName:p.albumName, name:p.name, code:p.code })),\n            printSurchargePerPhoto: PRINT_SURCHARGE_PER_PHOTO,\n            printSurcharge,\n            items: selectedPhotos.map(p => ({ id: p.id, albumName: p.albumName, subAlbumName: p.subAlbumName || '', name: p.name, code: p.code, url: p.url, driveLink: p.rawUrl || p.fullUrl || p.url, price: p.price, printRequested: printedPhotoIds.includes(p.id) })),'''
if old not in s:
    raise SystemExit('order print data anchor missing')
s = s.replace(old, new, 1)

# Validate print selection before sending
anchor = '''        if (!String(checkoutCustomerName || '').trim() || !normalizePhone(checkoutPhone)) {\n            setCustomerDetailsOpen(true);\n            alert('Antes de finalizar, guardá tu nombre y apellido y un celular de contacto.');\n            return;\n        }\n'''
extra = '''        if (checkoutPrint && !printSelectedPhotos.length) {\n            alert('Elegí al menos una de las fotos seleccionadas para imprimir en 10x15, o desactivá la opción de impresión.');\n            return;\n        }\n'''
if anchor not in s:
    raise SystemExit('sendOrder customer validation anchor missing')
s = s.replace(anchor, anchor + extra, 1)

# Clear print state after purchase
old = '''            setCheckoutOrderCode('');\n        }'''
new = '''            setCheckoutOrderCode('');\n            setCheckoutPrint(false);\n            setPrintedPhotoIds([]);\n        }'''
if old not in s:
    raise SystemExit('sendOrder reset anchor missing')
s = s.replace(old, new, 1)

# Club helper/admin actions before coupon actions
anchor = '''    const addCoupon = () => {\n'''
club_functions = r'''    const addClubProduct = () => {
        const name = String(newClubProductName || '').trim();
        const points = Math.max(1, Math.round(Number(newClubProductPoints) || 0));
        if (!name) { setAdminMessage('Ingresá el nombre del producto del Club.'); return; }
        if (!points) { setAdminMessage('Ingresá un puntaje válido.'); return; }
        const item = { id:'club-' + Date.now().toString(36) + '-' + Math.floor(Math.random()*9999), name, description:String(newClubProductDescription || '').trim(), points, imageUrl:String(newClubProductImage || '').trim(), active:true, createdAt:new Date().toISOString() };
        setClubProducts(prev => [item, ...prev]);
        setNewClubProductName('');
        setNewClubProductDescription('');
        setNewClubProductPoints(3);
        setNewClubProductImage('');
        setAdminMessage('Producto agregado al Club de beneficios.');
    };
    const toggleClubProduct = (id) => setClubProducts(prev => prev.map(p => p.id === id ? { ...p, active:p.active === false ? true : false } : p));
    const deleteClubProduct = (id) => setClubProducts(prev => prev.filter(p => p.id !== id));
    async function loadClubOrdersForDni(rawDni) {
        const dni = normalizeDni(rawDni);
        if (!dni) return [];
        if (sessionStorage.getItem('LA_FIRESTORE_QUOTA_EXHAUSTED') !== '1') {
            try {
                const db = await getFirebaseDb();
                if (db) {
                    const snap = await db.collection(ORDERS_COLLECTION_PATH).where('dni','==',dni).limit(500).get({ source:'server' });
                    const direct = snap.docs.map(d => ({ id:d.data().id || d.id, ...d.data() }));
                    if (direct.length) return mergeOrders(direct);
                }
            } catch (e) {
                if (String(e && e.message || e).includes('resource-exhausted')) sessionStorage.setItem('LA_FIRESTORE_QUOTA_EXHAUSTED','1');
                console.warn('No se pudo consultar el DNI directamente en Firebase.', e);
            }
        }
        try {
            const all = await loadOrdersRemote();
            return mergeOrders(all).filter(o => normalizeDni(o.dni || o.customerDni) === dni);
        } catch (e) {
            console.warn('No se pudo consultar el Club en pedidos remotos.', e);
        }
        return mergeOrders(readLocalOrders()).filter(o => normalizeDni(o.dni || o.customerDni) === dni);
    }
    async function lookupClubPoints() {
        const dni = normalizeDni(clubLookupDni);
        if (!dni) { setClubMessage('Ingresá tu DNI para consultar los puntos.'); return; }
        setClubLookupDni(dni);
        setClubLookupLoading(true);
        setClubMessage('');
        try {
            const list = await loadClubOrdersForDni(dni);
            const account = clubAccountFromOrders(list, dni);
            setClubLookupResult(account);
            setClubMessage(account.points > 0 ? `Tenés ${account.points} puntos disponibles.` : 'Todavía no tenés puntos disponibles. Tus compras entregadas los irán acumulando.');
        } catch (e) {
            setClubMessage('No pudimos consultar tus puntos ahora. Probá nuevamente.');
        } finally {
            setClubLookupLoading(false);
        }
    }
    async function redeemClubProduct(product) {
        if (!product || product.active === false) return;
        const dni = normalizeDni(clubLookupDni || (clubLookupResult && clubLookupResult.dni));
        if (!dni || !clubLookupResult) {
            setClubPointsOpen(true);
            setClubMessage('Primero consultá tus puntos con tu DNI para poder canjear.');
            return;
        }
        setClubRedeeming(product.id);
        try {
            const latest = await loadClubOrdersForDni(dni);
            const account = clubAccountFromOrders(latest, dni);
            if (account.points < Number(product.points || 0)) {
                setClubLookupResult(account);
                setClubMessage(`Necesitás ${product.points} puntos y tenés ${account.points}.`);
                return;
            }
            if (!confirm(`¿Canjear ${product.name} por ${product.points} puntos?`)) return;
            const now = new Date().toISOString();
            const redemption = {
                id:'CB-' + Date.now().toString(36).toUpperCase() + '-' + Math.floor(100 + Math.random()*900),
                date:now,
                type:'benefit_redemption',
                benefitRedemption:true,
                rewardId:product.id,
                rewardName:product.name,
                redeemedPoints:Number(product.points) || 0,
                dni,
                customerName:account.name || '',
                phone:account.phone || '',
                subtotal:0,
                total:0,
                items:[],
                delivered:false,
                rejected:false,
                status:'canje_pendiente'
            };
            const status = await saveOrderRemote(redemption);
            if (!status.firebase && !status.script) throw new Error(status.error || 'No se pudo guardar el canje');
            const next = { ...account, redeemedPoints:account.redeemedPoints + redemption.redeemedPoints, redemptions:account.redemptions + 1, points:Math.max(0, account.points - redemption.redeemedPoints) };
            setClubLookupResult(next);
            setClubMessage(`✓ Canje solicitado: ${product.name}. Te quedan ${next.points} puntos. Lucas verá el canje en el Admin.`);
        } catch (e) {
            console.error('No se pudo guardar el canje del Club.', e);
            setClubMessage('No pudimos registrar el canje. Tus puntos no se descontaron; probá nuevamente.');
        } finally {
            setClubRedeeming('');
        }
    }
'''
if anchor not in s:
    raise SystemExit('addCoupon anchor missing')
s = s.replace(anchor, club_functions + anchor, 1)

# DNI field text
s = s.replace('placeholder:"DNI (opcional)"', 'placeholder:"DNI (opcional · para acumular puntos)"', 1)
s = s.replace('"Ingresalo sin puntos. Si escribís puntos, espacios o guiones, se unifica automáticamente."', '"El DNI se solicita para acumular puntos del Club. Ingresalo sin puntos; si escribís puntos, espacios o guiones, se unifica automáticamente."', 1)

# Checkout summary print row
old = '''                    checkoutPrint && React.createElement("div", { className: "checkout-simple-row" },\n                        React.createElement("span", { className:"text-sky-100/70" }, `Impresión (${cart.length} × $3.000)`),\n                        React.createElement("b", { className:"text-blue-200" }, `+${formatPrice(printSurcharge)}`)),'''
new = '''                    checkoutPrint && React.createElement("div", { className: "checkout-simple-row" },\n                        React.createElement("span", { className:"text-sky-100/70" }, `Impresión 10x15 (${printSelectedPhotos.length} × $3.000)`),\n                        React.createElement("b", { className:"text-blue-200" }, `+${formatPrice(printSurcharge)}`)),'''
if old not in s:
    raise SystemExit('checkout print summary anchor missing')
s = s.replace(old, new, 1)

# Checkout print picker replaces current print button block
old = '''                React.createElement("button", { type:"button", onClick:() => setCheckoutPrint(v => !v), className:`print-order-btn mb-3 ${checkoutPrint ? 'active' : ''}` },\n                    React.createElement("i", { className:"fas fa-print" }),\n                    React.createElement("span", null, React.createElement("b", null, "Quiero la foto impresa"), React.createElement("small", null, `+$3.000 por foto seleccionada${checkoutPrint ? ` · +${formatPrice(printSurcharge)}` : ''}`)),\n                    React.createElement("i", { className:`fas ${checkoutPrint ? 'fa-circle-check' : 'fa-circle-plus'}` })),\n                React.createElement("details", { className: "checkout-simple-card checkout-simple-coupon mb-3" },'''
new = '''                React.createElement("button", { type:"button", onClick:() => setCheckoutPrint(v => { const next=!v; if(!next) setPrintedPhotoIds([]); return next; }), className:`print-order-btn mb-3 ${checkoutPrint ? 'active' : ''}` },\n                    React.createElement("i", { className:"fas fa-print" }),\n                    React.createElement("span", null, React.createElement("b", null, "Quiero impresión de fotos 10x15"), React.createElement("small", null, `+$3.000 por cada foto que elijas${checkoutPrint ? ` · ${printSelectedPhotos.length} seleccionada${printSelectedPhotos.length === 1 ? '' : 's'} · +${formatPrice(printSurcharge)}` : ''}`)),\n                    React.createElement("i", { className:`fas ${checkoutPrint ? 'fa-circle-check' : 'fa-circle-plus'}` })),\n                checkoutPrint && React.createElement("div", { className:"print-photo-picker" },\n                    React.createElement("div", { className:"flex items-center justify-between gap-2 mb-2" },\n                        React.createElement("div", null,\n                            React.createElement("p", { className:"text-xs font-black text-blue-100" }, "Elegí cuáles querés impresas"),\n                            React.createElement("p", { className:"text-[10px] text-blue-200/65" }, "Formato 10x15 cm · $3.000 por unidad")),\n                        React.createElement("span", { className:"print-order-badge" }, `${printSelectedPhotos.length} elegida${printSelectedPhotos.length === 1 ? '' : 's'}`)),\n                    React.createElement("div", { className:"print-photo-grid" }, selectedPhotos.map(p => React.createElement("button", { key:p.id, type:"button", onClick:() => togglePrintedPhoto(p.id), className:`print-photo-option ${printedPhotoIds.includes(p.id) ? 'active' : ''}` },\n                        React.createElement("img", { src:p.url, loading:"lazy", alt:p.name || p.code }),\n                        React.createElement("span", { className:"min-w-0" },\n                            React.createElement("b", { className:"block text-[10px] text-white truncate" }, p.name || p.code),\n                            React.createElement("small", { className:"block text-[9px] text-blue-200/65 truncate" }, `Código ${p.code}`)),\n                        React.createElement("i", { className:`fas ${printedPhotoIds.includes(p.id) ? 'fa-circle-check text-blue-300' : 'fa-circle text-white/25'}` }))))),\n                React.createElement("details", { className: "checkout-simple-card checkout-simple-coupon mb-3" },'''
if old not in s:
    raise SystemExit('checkout print button anchor missing')
s = s.replace(old, new, 1)

# Public Club section before purchase help
anchor = '''                !currentAlbum && activeAlbums.length > 0 && React.createElement(MainHeaderBanners, { bannerSettings: bannerSettings })),\n            React.createElement("div", { className: "mb-3 sm:mb-5" },'''
club_ui = r'''                !currentAlbum && activeAlbums.length > 0 && React.createElement(MainHeaderBanners, { bannerSettings: bannerSettings })),
            !currentAlbum && React.createElement("section", { className:"club-benefits-shell mb-4 sm:mb-5" },
                React.createElement("div", { className:"relative z-[1]" },
                    React.createElement("div", { className:"flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4" },
                        React.createElement("div", null,
                            React.createElement("p", { className:"text-[10px] uppercase tracking-[.18em] text-orange-300 font-black mb-1" }, "Club lucasabraham.ph"),
                            React.createElement("h2", { className:"text-xl sm:text-2xl font-black text-white" }, "Club de beneficios"),
                            React.createElement("p", { className:"text-xs sm:text-sm text-neutral-300 mt-1 leading-relaxed" }, "Sumás 3 puntos por cada $10.000 acumulados en compras entregadas. Canjealos por los productos disponibles.")),
                        React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn shrink-0" }, React.createElement("i", { className:"fas fa-coins" }), "Ver puntos acumulados")),
                    clubPointsOpen && React.createElement("div", { className:"club-account-card mb-4" },
                        React.createElement("p", { className:"text-xs font-black text-orange-100 mb-2" }, "Consultá con tu DNI"),
                        React.createElement("div", { className:"flex flex-col sm:flex-row gap-2" },
                            React.createElement("input", { value:clubLookupDni, inputMode:"numeric", onChange:e => { setClubLookupDni(e.target.value); setClubLookupResult(null); }, placeholder:"DNI sin puntos", className:"customer-compact-input flex-1" }),
                            React.createElement("button", { type:"button", onClick:lookupClubPoints, disabled:clubLookupLoading, className:"club-points-btn sm:min-w-[150px]" }, clubLookupLoading ? "Consultando..." : "Ver mis puntos")),
                        clubLookupResult && React.createElement("div", { className:"grid grid-cols-3 gap-2 mt-3 text-center" },
                            React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-orange-300" }, clubLookupResult.points), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "disponibles")),
                            React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.earnedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "ganados")),
                            React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.redeemedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "canjeados"))),
                        clubMessage && React.createElement("p", { className:"text-[11px] text-orange-100/85 mt-2 leading-relaxed" }, clubMessage)),
                    React.createElement("div", { className:"grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" },
                        clubProducts.filter(p => p.active !== false).length === 0 && React.createElement("div", { className:"club-empty col-span-full" },
                            React.createElement("i", { className:"fas fa-gift text-2xl text-orange-300 mb-2" }),
                            React.createElement("p", { className:"font-black text-white" }, "Aún no hay productos"),
                            React.createElement("p", { className:"text-xs mt-1" }, "Podés consultar tus puntos igualmente. Los productos aparecerán acá cuando estén disponibles.")),
                        clubProducts.filter(p => p.active !== false).map(product => React.createElement("article", { key:product.id, className:"club-product-card" },
                            product.imageUrl ? React.createElement("img", { src:product.imageUrl, className:"club-product-image", loading:"lazy", alt:product.name }) : React.createElement("div", { className:"club-product-placeholder" }, React.createElement("i", { className:"fas fa-gift" })),
                            React.createElement("div", { className:"club-product-body" },
                                React.createElement("span", { className:"club-points-chip" }, React.createElement("i", { className:"fas fa-coins" }), `${product.points} puntos`),
                                React.createElement("h3", { className:"font-black text-sm text-white leading-tight" }, product.name),
                                product.description && React.createElement("p", { className:"text-[10px] text-neutral-400 leading-relaxed flex-1" }, product.description),
                                React.createElement("button", { type:"button", disabled:clubRedeeming === product.id || Boolean(clubLookupResult && clubLookupResult.points < product.points), onClick:() => redeemClubProduct(product), className:`club-redeem-btn ${clubLookupResult && clubLookupResult.points >= product.points ? 'ready' : ''}` }, clubRedeeming === product.id ? "Canjeando..." : !clubLookupResult ? "Consultar puntos para canjear" : clubLookupResult.points >= product.points ? "Canjear ahora" : `Te faltan ${product.points - clubLookupResult.points} pts`))))))),
            React.createElement("div", { className: "mb-3 sm:mb-5" },'''
if anchor not in s:
    raise SystemExit('public club insertion anchor missing')
s = s.replace(anchor, club_ui, 1)

# Admin Club block replace old Beneficios por DNI section
pattern = re.compile(r'''            React\.createElement\("div", \{ className: "bg-neutral-900 border border-neutral-800 rounded-3xl p-5 mb-6" \},\n                React\.createElement\("h2", \{ className: "text-xl font-black" \}, "Beneficios por DNI"\),.*?            React\.createElement\("div", \{ id: "order-search-panel",''', re.S)
admin_club = r'''            React.createElement("div", { className: "bg-neutral-900 border border-neutral-800 rounded-3xl p-5 mb-6" },
                React.createElement("div", { className:"flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3 mb-4" },
                    React.createElement("div", null,
                        React.createElement("h2", { className: "text-xl font-black" }, React.createElement("i", { className:"fas fa-gift mr-2 text-orange-300" }), "Club de beneficios"),
                        React.createElement("p", { className: "text-neutral-400 text-sm mt-1" }, "Regla: 3 puntos por cada $10.000 acumulados en pedidos entregados. Los canjes descuentan puntos y quedan registrados como pedidos del Club.")),
                    React.createElement("span", { className:"club-order-badge" }, `${clubProducts.filter(p => p.active !== false).length} productos activos`)),
                React.createElement("div", { className:"bg-black/30 border border-orange-500/15 rounded-2xl p-4 mb-5" },
                    React.createElement("h3", { className:"font-black text-sm mb-3" }, "Productos y premios del Club"),
                    React.createElement("div", { className:"grid md:grid-cols-4 gap-2" },
                        React.createElement("input", { value:newClubProductName, onChange:e => setNewClubProductName(e.target.value), placeholder:"Nombre del producto", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm outline-none" }),
                        React.createElement("input", { value:newClubProductDescription, onChange:e => setNewClubProductDescription(e.target.value), placeholder:"Descripción", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm outline-none" }),
                        React.createElement("input", { value:newClubProductImage, onChange:e => setNewClubProductImage(e.target.value), placeholder:"URL de imagen (opcional)", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm outline-none" }),
                        React.createElement("div", { className:"flex gap-2" },
                            React.createElement("input", { type:"number", min:"1", value:newClubProductPoints, onChange:e => setNewClubProductPoints(e.target.value), placeholder:"Puntos", className:"w-24 bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm outline-none" }),
                            React.createElement("button", { onClick:addClubProduct, className:"flex-1 bg-orange-500 hover:bg-orange-400 text-black rounded-xl px-3 py-3 text-xs font-black" }, "Agregar"))),
                    React.createElement("div", { className:"grid sm:grid-cols-2 lg:grid-cols-3 gap-2 mt-3" },
                        clubProducts.length === 0 && React.createElement("p", { className:"text-xs text-neutral-500" }, "Aún no hay productos cargados. En la app igualmente se verá el Club y el mensaje ‘Aún no hay productos’."),
                        clubProducts.map(product => React.createElement("div", { key:product.id, className:"bg-neutral-950 border border-neutral-800 rounded-xl p-3 flex items-center gap-3" },
                            product.imageUrl ? React.createElement("img", { src:product.imageUrl, className:"w-12 h-12 rounded-lg object-cover" }) : React.createElement("div", { className:"w-12 h-12 rounded-lg bg-orange-500/10 flex items-center justify-center text-orange-300" }, React.createElement("i", { className:"fas fa-gift" })),
                            React.createElement("div", { className:"min-w-0 flex-1" }, React.createElement("b", { className:"text-xs block truncate" }, product.name), React.createElement("span", { className:"text-[10px] text-orange-300" }, `${product.points} puntos · ${product.active === false ? 'Pausado' : 'Activo'}`)),
                            React.createElement("button", { onClick:() => toggleClubProduct(product.id), className:"bg-neutral-800 px-2 py-2 rounded-lg text-[10px] font-black" }, product.active === false ? "Activar" : "Pausar"),
                            React.createElement("button", { onClick:() => deleteClubProduct(product.id), className:"bg-red-500/15 text-red-200 px-2 py-2 rounded-lg text-[10px]" }, React.createElement("i", { className:"fas fa-trash" }))))),
                React.createElement("div", { className: "overflow-x-auto" },
                    React.createElement("table", { className: "w-full text-sm min-w-[1050px]" },
                        React.createElement("thead", null, React.createElement("tr", { className: "text-left text-neutral-500 border-b border-neutral-800" }, ["DNI","Nombre y apellido","Celular","Compras","Gastado","Puntos","Canjeados","Pendientes","Anulados","Imp. 10x15"].map(x => React.createElement("th", { key:x, className:"py-2 pr-4 text-xs" }, x)))),
                        React.createElement("tbody", null, customerDniStats.map(r => React.createElement("tr", { key:r.dni, className:"border-b border-neutral-800/70" },
                            React.createElement("td", { className:"py-3 pr-4 font-black" }, r.dni),
                            React.createElement("td", { className:"py-3 pr-4" }, r.name || '—'),
                            React.createElement("td", { className:"py-3 pr-4" }, r.phone || '—'),
                            React.createElement("td", { className:"py-3 pr-4" }, r.purchases),
                            React.createElement("td", { className:"py-3 pr-4 font-black text-emerald-300" }, formatPrice(r.spent)),
                            React.createElement("td", { className:"py-3 pr-4 font-black text-orange-300" }, r.points),
                            React.createElement("td", { className:"py-3 pr-4" }, r.redeemedPoints),
                            React.createElement("td", { className:"py-3 pr-4" }, r.pending),
                            React.createElement("td", { className:"py-3 pr-4" }, r.cancelled),
                            React.createElement("td", { className:"py-3" }, r.prints)))))),
                React.createElement("h3", { className:"font-black text-lg mt-5 mb-3" }, "Historial acumulado de pedidos y canjes"),
                React.createElement("div", { className:"grid gap-2 max-h-[440px] overflow-auto" }, adminOrderLedger.map(o => {
                    const isRedemption = o.type === 'benefit_redemption' || o.benefitRedemption === true;
                    const printCount = Number(o.printCount) || ((o.printedItems || []).length) || (o.printRequested ? 1 : 0);
                    return React.createElement("div", { key:o.id, className:"bg-neutral-950 border border-neutral-800 rounded-2xl p-3 flex flex-col sm:flex-row sm:items-center gap-3" },
                        React.createElement("button", { onClick:() => openOrderFromQueue(o), className:"text-left min-w-0 flex-1" },
                            React.createElement("div", { className:"flex flex-wrap items-center gap-2" }, React.createElement("b", null, "#", o.id), isRedemption && React.createElement("span", { className:"club-order-badge" }, "CANJE CLUB"), printCount > 0 && React.createElement("span", { className:"print-order-badge" }, `IMPRESIÓN 10x15 × ${printCount}`)),
                            React.createElement("p", { className:"text-xs text-neutral-400 mt-1" }, (o.customerName || 'Sin nombre'), " · DNI ", (o.dni || '—'), " · ", (o.phone || '—'), isRedemption ? ` · ${o.rewardName || 'Beneficio'} · -${o.redeemedPoints || 0} pts` : ` · ${formatPrice(o.total)}`)),
                        React.createElement("button", { onClick:() => openOrderFromQueue(o), className:"bg-neutral-800 px-3 py-2 rounded-xl text-xs font-bold" }, "Abrir"),
                        !o.rejected && React.createElement("button", { onClick:() => { if (confirm(isRedemption ? '¿Anular este canje y devolver los puntos?' : '¿Marcar este pedido como cancelado/no pagado?')) setOrderDecisionAndClose(o,'rejected'); }, className:"bg-red-500/15 border border-red-500/30 text-red-200 px-3 py-2 rounded-xl text-xs font-black" }, isRedemption ? "Anular canje" : "Anular / no pagado"));
                }))),
            React.createElement("div", { id: "order-search-panel",'''
s, n = pattern.subn(admin_club, s, count=1)
if n != 1:
    raise SystemExit(f'admin club replacement count {n}')

# Matched order detail: add club/print callouts after total line block
anchor = '''                                ((_c = matchedOrder.items) === null || _c === void 0 ? void 0 : _c.length) || 0,\n                                " fotos")),'''
extra = '''                                ((_c = matchedOrder.items) === null || _c === void 0 ? void 0 : _c.length) || 0,\n                                " fotos"),\n                            (matchedOrder.type === 'benefit_redemption' || matchedOrder.benefitRedemption === true) && React.createElement("div", { className:"club-order-badge mt-2" }, React.createElement("i", { className:"fas fa-gift" }), `CANJE CLUB · ${matchedOrder.rewardName || 'Beneficio'} · -${matchedOrder.redeemedPoints || 0} puntos`),\n                            matchedOrder.printRequested && React.createElement("div", { className:"print-order-badge mt-2" }, React.createElement("i", { className:"fas fa-print" }), `IMPRESIÓN 10x15 · ${Number(matchedOrder.printCount) || (matchedOrder.printedItems || []).length || 1} foto${(Number(matchedOrder.printCount) || (matchedOrder.printedItems || []).length || 1) === 1 ? '' : 's'}`)),'''
if anchor not in s:
    raise SystemExit('matched order callout anchor missing')
s = s.replace(anchor, extra, 1)

# Add printed badge to individual admin item rows after code/price line
anchor = '''                                    formatPrice(item.price)),\n                                React.createElement("p", { className: "text-[11px] text-neutral-500 truncate mt-1" }, link || 'Sin link guardado')),'''
extra = '''                                    formatPrice(item.price)),\n                                (item.printRequested || (matchedOrder.printedPhotoIds || []).includes(item.id) || (matchedOrder.printedItems || []).some(x => x.id === item.id || (x.code && x.code === item.code))) && React.createElement("span", { className:"print-order-badge mt-1" }, React.createElement("i", { className:"fas fa-print" }), "IMPRESA 10x15"),\n                                React.createElement("p", { className: "text-[11px] text-neutral-500 truncate mt-1" }, link || 'Sin link guardado')),'''
if anchor not in s:
    raise SystemExit('admin item print badge anchor missing')
s = s.replace(anchor, extra, 1)

# Pending queue badges: after order id/age chip flex block
anchor = '''                                        React.createElement("p", { className: "font-black truncate" }, "#", o.id),\n                                        React.createElement("span", { className: `order-age-chip ${orderAgeInfo(o.date).tone}` }, React.createElement("i", { className: "fas fa-stopwatch" }), orderAgeInfo(o.date).text)),'''
extra = '''                                        React.createElement("p", { className: "font-black truncate" }, "#", o.id),\n                                        React.createElement("span", { className: `order-age-chip ${orderAgeInfo(o.date).tone}` }, React.createElement("i", { className: "fas fa-stopwatch" }), orderAgeInfo(o.date).text),\n                                        (o.type === 'benefit_redemption' || o.benefitRedemption === true) && React.createElement("span", { className:"club-order-badge" }, "CANJE CLUB"),\n                                        o.printRequested && React.createElement("span", { className:"print-order-badge" }, `10x15 × ${Number(o.printCount) || (o.printedItems || []).length || 1}`)),'''
if anchor not in s:
    raise SystemExit('pending badge anchor missing')
s = s.replace(anchor, extra, 1)

p.write_text(s, encoding='utf-8')
print('v71 patch applied')
