from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
if 'v69-customer-benefits' in s:
    print('already applied')
    raise SystemExit(0)

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'missing {label}')
    s = s.replace(old, new, 1)

s = re.sub(r'<meta name="app-version" content="[^"]+"\s*/>', '<meta name="app-version" content="v69-customer-benefits" />', s, count=1)
s = s.replace('\\n<style id="la-v67-stable-ui">', '\n<style id="la-v67-stable-ui">').replace('</script>\\n</body>', '</script>\n</body>')

rep("""    const rowA2 = String(firstCellValue(rows[0]) || '').trim();
    const rowA3 = String(firstCellValue(rows[1]) || '').trim();""", """    const rowA2 = String(firstCellValue(rows[0]) || '').trim();
    const rowA3 = String(firstCellValue(rows[1]) || '').trim();
    const rowA4 = String(firstCellValue(rows[2]) || '').trim();
    const rowA5 = String(firstCellValue(rows[3]) || '').trim();""", 'rows A4/A5')

rep("""    const explicitA2 = String(sheet.A2 || sheet.a2 || '').trim();
    const explicitA3 = String(sheet.A3 || sheet.a3 || '').trim();""", """    const explicitA2 = String(sheet.A2 || sheet.a2 || '').trim();
    const explicitA3 = String(sheet.A3 || sheet.a3 || '').trim();
    const explicitA4 = String(sheet.A4 || sheet.a4 || '').trim();
    const explicitA5 = String(sheet.A5 || sheet.a5 || '').trim();""", 'explicit A4/A5')

rep("""    return {
        localRaw: rowA2 || explicitA2 || legacyLocal,
        visitorRaw: rowA3 || explicitA3 || legacyVisitor
    };""", """    return {
        localRaw: rowA2 || explicitA2 || legacyLocal,
        visitorRaw: rowA3 || explicitA3 || legacyVisitor,
        localFullRaw: rowA4 || explicitA4 || '',
        visitorFullRaw: rowA5 || explicitA5 || ''
    };""", 'team return')

rep("""    local.logo = local.logo || '';
    visitante.logo = visitante.logo || '';

    return [local, visitante];""", """    local.logo = local.logo || '';
    visitante.logo = visitante.logo || '';
    local.fullName = exactCells.localFullRaw || local.name;
    visitante.fullName = exactCells.visitorFullRaw || visitante.name;

    return [local, visitante];""", 'full names')

rep('function albumTeamSide(album, index) {', 'function albumTeamSide(album, index, useFullName = false) {', 'side signature')
rep("        name: entry.name || names[index] || (index === 0 ? album === null || album === void 0 ? void 0 : album.name : '') || '',", "        name: (useFullName && entry.fullName) || entry.name || names[index] || (index === 0 ? album === null || album === void 0 ? void 0 : album.name : '') || '',", 'full side name')
s = s.replace('renderVersusScene(albumTeamSide(currentAlbum, 0), albumTeamSide(currentAlbum, 1), {})', 'renderVersusScene(albumTeamSide(currentAlbum, 0, true), albumTeamSide(currentAlbum, 1, true), {})', 1)

rep('    const [couponMessage, setCouponMessage] = useState("");', '''    const [couponMessage, setCouponMessage] = useState("");
    const [checkoutCustomerName, setCheckoutCustomerName] = useState("");
    const [checkoutPhone, setCheckoutPhone] = useState("");
    const [checkoutDni, setCheckoutDni] = useState("");
    const [checkoutWantsPoints, setCheckoutWantsPoints] = useState(false);
    const [checkoutPrint, setCheckoutPrint] = useState(false);
    const [customerDetailsOpen, setCustomerDetailsOpen] = useState(true);
    const [customerDetailsSaved, setCustomerDetailsSaved] = useState(false);
    const [customerSavedMessage, setCustomerSavedMessage] = useState("");''', 'checkout states')

rep('''    const checkoutTotal = Math.round(total * (1 - couponPercent / 100));
    const couponSavings = total - checkoutTotal;
    const savings = regular - checkoutTotal;
    const effectiveDiscountPercent = regular > 0 ? Math.round((1 - (checkoutTotal / regular)) * 100) : 0;''', '''    const PRINT_SURCHARGE_PER_PHOTO = 3000;
    const checkoutDigitalTotal = Math.round(total * (1 - couponPercent / 100));
    const printSurcharge = checkoutPrint ? cart.length * PRINT_SURCHARGE_PER_PHOTO : 0;
    const checkoutTotal = checkoutDigitalTotal + printSurcharge;
    const couponSavings = total - checkoutDigitalTotal;
    const savings = regular - checkoutDigitalTotal;
    const effectiveDiscountPercent = regular > 0 ? Math.round((1 - (checkoutDigitalTotal / regular)) * 100) : 0;''', 'totals')

rep('''        setCouponMessage("");
        setCheckoutOrderCode('LA-' + Math.floor(10000 + Math.random() * 90000));''', '''        setCouponMessage("");
        setCheckoutPrint(false);
        setCustomerDetailsOpen(true);
        setCustomerDetailsSaved(false);
        setCustomerSavedMessage("");
        setCheckoutOrderCode('LA-' + Math.floor(10000 + Math.random() * 90000));''', 'checkout reset')

rep('    const applyCoupon = () => {', '''    const normalizeDni = value => String(value || "").replace(/\D/g, "");
    const normalizePhone = value => String(value || "").replace(/\D/g, "");
    const saveCheckoutCustomer = () => {
        const name = String(checkoutCustomerName || "").trim().replace(/\s{2,}/g, " ");
        const phone = normalizePhone(checkoutPhone);
        const dni = normalizeDni(checkoutDni);
        if (!name) { alert("Ingresá nombre y apellido."); return; }
        if (!phone) { alert("Ingresá un celular de contacto."); return; }
        setCheckoutCustomerName(name);
        setCheckoutPhone(phone);
        setCheckoutDni(dni);
        setCustomerDetailsSaved(true);
        setCustomerSavedMessage("✓ Datos guardados correctamente");
        setTimeout(() => { setCustomerDetailsOpen(false); setCustomerSavedMessage(""); }, 900);
    };
    const applyCoupon = () => {''', 'helpers')

rep("""        if (!cart.length || !selectedPhotos.length) {
            alert('Seleccioná al menos una foto antes de comprar.');
            return;
        }""", """        if (!cart.length || !selectedPhotos.length) {
            alert('Seleccioná al menos una foto antes de comprar.');
            return;
        }
        if (!String(checkoutCustomerName || '').trim() || !normalizePhone(checkoutPhone)) {
            setCustomerDetailsOpen(true);
            alert('Antes de finalizar, guardá tu nombre y apellido y un celular de contacto.');
            return;
        }""", 'send validation')

rep('        selectedPhotos.forEach(p => msg += `${EM.dot} ${p.albumName} - ${p.name} - ${formatPrice(p.price)} - Código ${p.code}\n`);', '''        const cleanDni = normalizeDni(checkoutDni);
        const cleanPhone = normalizePhone(checkoutPhone);
        msg += `${EM.point} *Cliente:* ${String(checkoutCustomerName || "").trim()}\n`;
        msg += `${EM.point} *Celular:* ${cleanPhone}\n`;
        if (cleanDni) msg += `${EM.point} *DNI:* ${cleanDni}${checkoutWantsPoints ? " · Suma puntos" : ""}\n`;
        if (checkoutPrint) msg += `${EM.image} *Fotos impresas:* Sí · ${cart.length} x ${formatPrice(PRINT_SURCHARGE_PER_PHOTO)} = ${formatPrice(printSurcharge)}\n`;
        msg += `\n`;
        selectedPhotos.forEach(p => msg += `${EM.dot} ${p.albumName} - ${p.name} - ${formatPrice(p.price)} - Código ${p.code}\n`);''', 'whatsapp customer')

rep('''            total: checkoutTotal,
            items: selectedPhotos.map(p => ({ id: p.id, albumName: p.albumName, subAlbumName: p.subAlbumName || '', name: p.name, code: p.code, url: p.url, driveLink: p.rawUrl || p.fullUrl || p.url, price: p.price })),
            delivered: false''', '''            total: checkoutTotal,
            digitalTotal: checkoutDigitalTotal,
            customerName: String(checkoutCustomerName || "").trim(),
            dni: normalizeDni(checkoutDni),
            phone: normalizePhone(checkoutPhone),
            wantsPoints: Boolean(checkoutWantsPoints && normalizeDni(checkoutDni)),
            printRequested: Boolean(checkoutPrint),
            printSurchargePerPhoto: PRINT_SURCHARGE_PER_PHOTO,
            printSurcharge,
            items: selectedPhotos.map(p => ({ id: p.id, albumName: p.albumName, subAlbumName: p.subAlbumName || '', name: p.name, code: p.code, url: p.url, driveLink: p.rawUrl || p.fullUrl || p.url, price: p.price })),
            delivered: false,
            status: 'pendiente' ''', 'order data')

rep("    const userFriendlyError = String(error || '').includes('Google Sheets bloqueó la lectura directa')", '''    const customerDniStats = useMemo(() => {
        const map = new Map();
        mergeOrders(orders).forEach(o => {
            const dni = String(o.dni || o.customerDni || '').replace(/\D/g, '');
            if (!dni) return;
            const status = norm(o.status || o.estado || '');
            const cancelled = isTruthyStatus(o.rejected) || ['rechazado','cancelado','anulado','no pagado','no_pagado'].includes(status);
            const confirmed = isTruthyStatus(o.delivered) || ['entregado','cargado_y_entregado','pagado'].includes(status);
            const row = map.get(dni) || { dni, name:'', phone:'', purchases:0, spent:0, pending:0, cancelled:0, prints:0 };
            row.name = String(o.customerName || o.nombreApellido || row.name || '').trim();
            row.phone = String(o.phone || o.celular || row.phone || '').replace(/\D/g, '');
            if (cancelled) row.cancelled += 1;
            else if (confirmed) {
                row.purchases += 1;
                row.spent += Number(o.total) || 0;
                if (o.printRequested) row.prints += 1;
            } else row.pending += 1;
            map.set(dni, row);
        });
        return Array.from(map.values()).sort((a,b) => b.spent - a.spent || b.purchases - a.purchases);
    }, [orders]);
    const adminOrderLedger = useMemo(() => mergeOrders(orders).sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0,200), [orders]);
    const userFriendlyError = String(error || '').includes('Google Sheets bloqueó la lectura directa')''', 'admin stats')

admin_anchor = '            React.createElement("div", { id: "order-search-panel", className: "bg-neutral-900 border border-neutral-800 rounded-3xl p-5 mb-6" },'
if admin_anchor not in s:
    raise SystemExit('missing admin anchor')
panel = '''            React.createElement("div", { className: "bg-neutral-900 border border-neutral-800 rounded-3xl p-5 mb-6" },
                React.createElement("h2", { className: "text-xl font-black" }, "Beneficios por DNI"),
                React.createElement("p", { className: "text-neutral-400 text-sm mt-1 mb-4" }, "Solo pedidos entregados/pagados suman compras y gasto."),
                React.createElement("div", { className: "overflow-x-auto" },
                    React.createElement("table", { className: "w-full text-sm min-w-[820px]" },
                        React.createElement("thead", null, React.createElement("tr", { className: "text-left text-neutral-500 border-b border-neutral-800" }, ["DNI","Nombre y apellido","Celular","Compras","Gastado","Pendientes","Anulados","Impresas"].map(x => React.createElement("th", { key:x, className:"py-2 pr-4 text-xs" }, x)))),
                        React.createElement("tbody", null, customerDniStats.map(r => React.createElement("tr", { key:r.dni, className:"border-b border-neutral-800/70" },
                            React.createElement("td", { className:"py-3 pr-4 font-black" }, r.dni),
                            React.createElement("td", { className:"py-3 pr-4" }, r.name || '—'),
                            React.createElement("td", { className:"py-3 pr-4" }, r.phone || '—'),
                            React.createElement("td", { className:"py-3 pr-4" }, r.purchases),
                            React.createElement("td", { className:"py-3 pr-4 font-black text-emerald-300" }, formatPrice(r.spent)),
                            React.createElement("td", { className:"py-3 pr-4" }, r.pending),
                            React.createElement("td", { className:"py-3 pr-4" }, r.cancelled),
                            React.createElement("td", { className:"py-3" }, r.prints)))))),
                React.createElement("h3", { className:"font-black text-lg mt-5 mb-3" }, "Historial acumulado de pedidos"),
                React.createElement("div", { className:"grid gap-2 max-h-[420px] overflow-auto" }, adminOrderLedger.map(o => React.createElement("div", { key:o.id, className:"bg-neutral-950 border border-neutral-800 rounded-2xl p-3 flex flex-col sm:flex-row sm:items-center gap-3" },
                    React.createElement("button", { onClick:() => openOrderFromQueue(o), className:"text-left min-w-0 flex-1" },
                        React.createElement("b", null, "#", o.id),
                        React.createElement("p", { className:"text-xs text-neutral-400 mt-1" }, (o.customerName || 'Sin nombre'), " · DNI ", (o.dni || '—'), " · ", (o.phone || '—'), " · ", formatPrice(o.total))),
                    React.createElement("button", { onClick:() => openOrderFromQueue(o), className:"bg-neutral-800 px-3 py-2 rounded-xl text-xs font-bold" }, "Abrir"),
                    !o.rejected && React.createElement("button", { onClick:() => { if (confirm('¿Marcar este pedido como cancelado/no pagado?')) setOrderDecisionAndClose(o,'rejected'); }, className:"bg-red-500/15 border border-red-500/30 text-red-200 px-3 py-2 rounded-xl text-xs font-black" }, "Anular / no pagado"))))),
            ),
'''
s = s.replace(admin_anchor, panel + admin_anchor, 1)

checkout_anchor = '                React.createElement("div", { className: "checkout-simple-total mb-3" },'
if checkout_anchor not in s:
    raise SystemExit('missing checkout anchor')
customer = '''                React.createElement("div", { className: "checkout-simple-card customer-data-card mb-3" },
                    React.createElement("button", { type:"button", onClick:() => setCustomerDetailsOpen(v => !v), className:"w-full flex items-center justify-between gap-3 text-left" },
                        React.createElement("div", null,
                            React.createElement("p", { className:"text-[11px] uppercase tracking-[.16em] text-sky-100/70 font-black" }, "Datos del comprador"),
                            React.createElement("p", { className:"text-sm font-black text-white mt-1" }, customerDetailsSaved ? `${checkoutCustomerName} · ${checkoutPhone}` : "Nombre, celular y beneficios")),
                        React.createElement("i", { className:`fas ${customerDetailsOpen ? 'fa-chevron-up' : 'fa-chevron-down'} text-sky-200` })),
                    customerDetailsOpen && React.createElement("div", { className:"mt-3 grid gap-2" },
                        React.createElement("input", { value:checkoutCustomerName, onChange:e => { setCheckoutCustomerName(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"Nombre y apellido", className:"customer-compact-input" }),
                        React.createElement("input", { value:checkoutPhone, inputMode:"tel", onChange:e => { setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"Celular", className:"customer-compact-input" }),
                        React.createElement("button", { type:"button", onClick:() => setCheckoutWantsPoints(v => !v), className:`benefits-glass-btn ${checkoutWantsPoints ? 'active' : ''}` },
                            React.createElement("i", { className:"fas fa-gift" }),
                            React.createElement("span", null, React.createElement("b", null, "Quiero sumar puntos para beneficios"), React.createElement("small", null, "Futuros descuentos, fotos impresas y beneficios"))),
                        checkoutWantsPoints && React.createElement("div", null,
                            React.createElement("input", { value:checkoutDni, inputMode:"numeric", onChange:e => { setCheckoutDni(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"DNI", className:"customer-compact-input" }),
                            React.createElement("p", { className:"text-[11px] text-amber-200/80 mt-1 px-1" }, "Ingresalo sin puntos. Si escribís puntos, espacios o guiones, se unifica automáticamente.")),
                        React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-floppy-disk mr-2" }), "Guardar datos"),
                        customerSavedMessage && React.createElement("p", { className:"customer-saved-msg" }, customerSavedMessage)),
                    !customerDetailsOpen && customerDetailsSaved && React.createElement("button", { type:"button", onClick:() => setCustomerDetailsOpen(true), className:"text-xs text-sky-200 mt-2" }, "Editar datos")),
'''
s = s.replace(checkout_anchor, customer + checkout_anchor, 1)

coupon_anchor = '                React.createElement("details", { className: "checkout-simple-card checkout-simple-coupon mb-3" },'
if coupon_anchor not in s:
    raise SystemExit('missing coupon anchor')
printui = '''                React.createElement("button", { type:"button", onClick:() => setCheckoutPrint(v => !v), className:`print-order-btn mb-3 ${checkoutPrint ? 'active' : ''}` },
                    React.createElement("i", { className:"fas fa-print" }),
                    React.createElement("span", null, React.createElement("b", null, "Quiero la foto impresa"), React.createElement("small", null, `+$3.000 por foto seleccionada${checkoutPrint ? ` · +${formatPrice(printSurcharge)}` : ''}`)),
                    React.createElement("i", { className:`fas ${checkoutPrint ? 'fa-circle-check' : 'fa-circle-plus'}` })),
'''
s = s.replace(coupon_anchor, printui + coupon_anchor, 1)

summary_anchor = '''                    React.createElement("div", { className: "checkout-simple-row" },
                        React.createElement("span", { className: "text-sky-100/70" }, "Entrega"),'''
if summary_anchor in s:
    s = s.replace(summary_anchor, '''                    checkoutPrint && React.createElement("div", { className: "checkout-simple-row" },
                        React.createElement("span", { className:"text-sky-100/70" }, `Impresión (${cart.length} × $3.000)`),
                        React.createElement("b", { className:"text-blue-200" }, `+${formatPrice(printSurcharge)}`)),
''' + summary_anchor, 1)

css = '''
<style id="v69-customer-benefits">
@media(max-width:768px),(hover:none),(pointer:coarse){
 .la-insta-topbar{position:-webkit-sticky!important;position:sticky!important;top:max(0px,env(safe-area-inset-top))!important;z-index:999!important;transform:translateZ(0)!important}
 .subalbum-panel{overflow:visible!important;padding:12px!important;border-radius:22px!important}
 .subalbum-showcase{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px!important;overflow:visible!important;padding:1px!important;scroll-snap-type:none!important}
 .subalbum-visual-card{width:100%!important;min-width:0!important;max-width:none!important;height:50px!important;min-height:50px!important;margin:0!important;padding:0 7px!important;border-radius:16px!important;clip-path:none!important;display:flex!important;align-items:center!important;justify-content:center!important}
 .subalbum-thumb-wrap,.subalbum-copy-meta,.subalbum-floating-badge{display:none!important}
 .subalbum-copy-wrap{width:100%!important;min-width:0!important;padding:0!important;text-align:center!important}
 .subalbum-copy-title,.subalbum-visual-card.active .subalbum-copy-title{margin:0!important;padding:0!important;font-size:clamp(8px,2.8vw,11px)!important;line-height:1!important;text-align:center!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
 .subalbum-visual-card.active:after{display:none!important}
}
.customer-compact-input{width:100%;background:rgba(0,0,0,.48);border:1px solid rgba(125,211,252,.2);border-radius:13px;padding:10px 12px;color:#fff;outline:none;font-size:14px}
.customer-compact-input:focus{border-color:rgba(56,189,248,.7);box-shadow:0 0 0 3px rgba(56,189,248,.1)}
.benefits-glass-btn{width:100%;display:flex;align-items:center;gap:11px;text-align:left;padding:12px 14px;border-radius:16px;color:#fff;border:1px solid rgba(255,255,255,.24);background:linear-gradient(135deg,#f97316,#ef4444 58%,#fb7185);box-shadow:inset 0 1px 0 rgba(255,255,255,.35),0 12px 28px rgba(239,68,68,.18)}
.benefits-glass-btn.active{box-shadow:inset 0 1px 0 rgba(255,255,255,.45),0 0 0 2px rgba(251,146,60,.28),0 14px 30px rgba(239,68,68,.24)}
.benefits-glass-btn span{display:flex;flex-direction:column}.benefits-glass-btn small{font-size:10px;opacity:.78;font-weight:600;margin-top:2px}
.save-customer-btn{width:100%;border-radius:13px;padding:11px 14px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.16);font-weight:900;color:#fff}
.customer-saved-msg{text-align:center;font-size:12px;font-weight:900;color:#86efac;padding:5px}
.print-order-btn{width:100%;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px;text-align:left;padding:13px 15px;border-radius:17px;border:1px solid rgba(255,255,255,.55);background:linear-gradient(135deg,#f8fafc,#cbd5e1 52%,#94a3b8);color:#0756a8;box-shadow:inset 0 1px 0 #fff,0 12px 25px rgba(15,23,42,.2)}
.print-order-btn span{display:flex;flex-direction:column}.print-order-btn small{font-size:10px;opacity:.72;margin-top:2px}
.print-order-btn.active{box-shadow:inset 0 1px 0 #fff,0 0 0 3px rgba(59,130,246,.25),0 12px 28px rgba(37,99,235,.2)}
</style>
'''
if '</head>' not in s:
    raise SystemExit('missing head')
s = s.replace('</head>', css + '</head>', 1)

p.write_text(s, encoding='utf-8')
print('patched index.html')
