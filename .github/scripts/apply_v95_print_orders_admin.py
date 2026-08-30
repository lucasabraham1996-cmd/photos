from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 got {n}')
    s=s.replace(old,new,1)

# Version
s=s.replace('v92-checkout-mobile-inputs','v95-print-orders-admin',1)

# Preserve per-photo print markers when compacting orders for Apps Script.
old="""        return {
            albumName: item.albumName || '',
            subAlbumName: item.subAlbumName || '',
            name: item.name || '',
            code: item.code || '',
            price: Number(item.price) || 0,
            ...(driveId ? { driveId } : (rawLink ? { driveLink: String(rawLink).slice(0, 500) } : {}))
        };
"""
new="""        return {
            id: item.id || '',
            albumName: item.albumName || '',
            subAlbumName: item.subAlbumName || '',
            name: item.name || '',
            code: item.code || '',
            price: Number(item.price) || 0,
            printRequested: Boolean(item.printRequested),
            ...(driveId ? { driveId } : (rawLink ? { driveLink: String(rawLink).slice(0, 500) } : {}))
        };
"""
once(old,new,'compact print fields')

# Add robust print detector after compact helper.
needle="""    return { ...order, items, itemCount: items.length, compactTransport: true };
}
async function saveOrderRemote(order) {
"""
insert="""    return { ...order, items, itemCount: items.length, compactTransport: true };
}
function orderPrintInfo(order) {
    const o = order || {};
    const items = Array.isArray(o.items) ? o.items : [];
    const explicit = Array.isArray(o.printedItems) ? o.printedItems : [];
    const idSet = new Set((Array.isArray(o.printedPhotoIds) ? o.printedPhotoIds : []).map(String));
    const codeSet = new Set(explicit.map(x => String((x && x.code) || '')).filter(Boolean));
    const nameSet = new Set(explicit.map(x => `${String((x && x.albumName) || '').trim()}|${String((x && x.name) || '').trim()}`).filter(x => x !== '|'));
    const marked = items.filter(item => {
        if (!item) return false;
        if (item.printRequested === true) return true;
        if (item.id != null && idSet.has(String(item.id))) return true;
        if (item.code && codeSet.has(String(item.code))) return true;
        return nameSet.has(`${String(item.albumName || '').trim()}|${String(item.name || '').trim()}`);
    });
    const seen = new Set();
    const printed = [];
    [...marked, ...explicit].forEach(item => {
        if (!item) return;
        const key = String(item.id || item.code || `${item.albumName || ''}|${item.name || ''}`);
        if (!key || seen.has(key)) return;
        seen.add(key);
        const full = items.find(x => (item.id && x.id === item.id) || (item.code && x.code === item.code)) || item;
        printed.push(full);
    });
    const declared = Math.max(0, Number(o.printCount) || 0);
    const fallback = o.printRequested === true ? 1 : 0;
    const count = Math.max(declared, printed.length, fallback);
    return { has: count > 0, count, items: printed, format: o.printFormat || '10x15 cm' };
}
async function saveOrderRemote(order) {
"""
once(needle,insert,'print helper')

# Header badge uses robust detector.
old="""                            matchedOrder.printRequested && React.createElement(\"div\", { className:\"print-order-badge mt-2\" }, React.createElement(\"i\", { className:\"fas fa-print\" }), `IMPRESIÓN 10x15 · ${Number(matchedOrder.printCount) || (matchedOrder.printedItems || []).length || 1} foto${(Number(matchedOrder.printCount) || (matchedOrder.printedItems || []).length || 1) === 1 ? '' : 's'}`)),
"""
new="""                            orderPrintInfo(matchedOrder).has && React.createElement(\"div\", { className:\"print-order-badge mt-2\" }, React.createElement(\"i\", { className:\"fas fa-print\" }), `IMPRESIONES ${orderPrintInfo(matchedOrder).format} · ${orderPrintInfo(matchedOrder).count} foto${orderPrintInfo(matchedOrder).count === 1 ? '' : 's'}`)),
"""
once(old,new,'matched header badge')

# Insert a prominent printed-photo panel before the full item list.
needle="""                    React.createElement(\"div\", { className: \"grid gap-3\" }, (matchedOrder.items || []).map((item, i) => {
"""
new="""                    orderPrintInfo(matchedOrder).has && React.createElement(\"div\", { className:\"mb-4 rounded-3xl border border-sky-400/40 bg-sky-500/10 p-4\" },
                        React.createElement(\"div\", { className:\"flex items-center justify-between gap-3 mb-3\" },
                            React.createElement(\"div\", null,
                                React.createElement(\"p\", { className:\"text-[10px] uppercase tracking-[.18em] text-sky-300 font-black\" }, \"PEDIDO CON IMPRESIONES\"),
                                React.createElement(\"h4\", { className:\"text-lg font-black text-white mt-1\" }, `${orderPrintInfo(matchedOrder).count} foto${orderPrintInfo(matchedOrder).count === 1 ? '' : 's'} para imprimir · ${orderPrintInfo(matchedOrder).format}`)),
                            React.createElement(\"div\", { className:\"w-11 h-11 rounded-2xl bg-sky-400 text-black flex items-center justify-center shrink-0\" }, React.createElement(\"i\", { className:\"fas fa-print text-lg\" }))),
                        orderPrintInfo(matchedOrder).items.length > 0
                            ? React.createElement(\"div\", { className:\"grid sm:grid-cols-2 gap-2\" }, orderPrintInfo(matchedOrder).items.map((item,i) => React.createElement(\"div\", { key:`print-${i}`, className:\"rounded-2xl bg-black/35 border border-sky-300/20 p-3 flex items-center gap-3\" },
                                orderItemPreviewUrl(item) && React.createElement(\"img\", { src:orderItemPreviewUrl(item), loading:\"lazy\", className:\"w-14 h-14 rounded-xl object-cover border border-white/10 shrink-0\", onError:e=>{e.currentTarget.style.display='none';} }),
                                React.createElement(\"div\", { className:\"min-w-0\" },
                                    React.createElement(\"b\", { className:\"block text-sm text-white truncate\" }, item.name || item.code || `Foto ${i+1}`),
                                    React.createElement(\"span\", { className:\"block text-xs text-sky-200/75 truncate\" }, `${item.albumName || ''}${item.code ? ` · Código ${item.code}` : ''}`)))))
                            : React.createElement(\"p\", { className:\"text-sm text-sky-100/80\" }, \"Este pedido incluye impresiones. Revisá las fotos marcadas como IMPRESA 10x15 en el detalle inferior.\")),
                    React.createElement(\"div\", { className: \"grid gap-3\" }, (matchedOrder.items || []).map((item, i) => {
"""
once(needle,new,'printed panel')

# Individual badge use helper membership, including old orders.
old="""                                (item.printRequested || (matchedOrder.printedPhotoIds || []).includes(item.id) || (matchedOrder.printedItems || []).some(x => x.id === item.id || (x.code && x.code === item.code))) && React.createElement(\"span\", { className:\"print-order-badge mt-1\" }, React.createElement(\"i\", { className:\"fas fa-print\" }), \"IMPRESA 10x15\"),
"""
new="""                                orderPrintInfo(matchedOrder).items.some(x => (x.id && item.id && x.id === item.id) || (x.code && item.code && x.code === item.code) || (x.albumName === item.albumName && x.name === item.name)) && React.createElement(\"span\", { className:\"print-order-badge mt-1\" }, React.createElement(\"i\", { className:\"fas fa-print\" }), `IMPRESA ${orderPrintInfo(matchedOrder).format}`),
"""
once(old,new,'item print badge')

# Queue badge robust for old orders.
old="""                                        o.printRequested && React.createElement(\"span\", { className:\"print-order-badge\" }, `10x15 × ${Number(o.printCount) || (o.printedItems || []).length || 1}`)),
"""
new="""                                        orderPrintInfo(o).has && React.createElement(\"span\", { className:\"print-order-badge\" }, React.createElement(\"i\", { className:\"fas fa-print mr-1\" }), `${orderPrintInfo(o).format} × ${orderPrintInfo(o).count}`)),
"""
once(old,new,'queue print badge')

# History/list count robust.
old="""                    const printCount = Number(o.printCount) || ((o.printedItems || []).length) || (o.printRequested ? 1 : 0);
"""
new="""                    const printCount = orderPrintInfo(o).count;
"""
once(old,new,'ledger print count')

p.write_text(s,encoding='utf-8')
print('v95 print orders admin patched')
