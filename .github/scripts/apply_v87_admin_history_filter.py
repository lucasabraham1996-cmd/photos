from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v86-resolved-admin-queue','v87-admin-history-pending-only')

old="""    const adminOrderLedger = useMemo(() => mergeOrders(orders).filter(o => { const ts = Date.parse((o && o.date) || 0); return Number.isFinite(ts) && ts >= ADMIN_HISTORY_RESET_AT && !isTruthyStatus(o.delivered); }).sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0,200), [orders]);"""
new="""    const adminOrderLedger = useMemo(() => mergeOrders(orders).filter(o => {
        const ts = Date.parse((o && o.date) || 0);
        const id = normalizeOrderCode(o && (o.id || o.orderId || o.codigo || o.code));
        return Number.isFinite(ts) && ts >= ADMIN_HISTORY_RESET_AT && isPendingOrder(o) && !adminResolvedIds.includes(id);
    }).sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0,200), [orders, adminResolvedIds]);"""
once(old,new,'admin history pending filter')

# Clarify section label so behavior is explicit.
once('React.createElement("h3", { className:"font-black text-lg mt-5 mb-3" }, "Historial de pedidos y canjes"),',
     'React.createElement("h3", { className:"font-black text-lg mt-5 mb-1" }, "Pedidos y canjes pendientes"),\n                React.createElement("p", { className:"text-xs text-neutral-500 mb-3" }, "Al entregar o rechazar, desaparecen de esta lista automáticamente."),',
     'ledger heading')

p.write_text(s,encoding='utf-8')
print('v87 patched')
