from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v85-admin-footer-club-logo','v86-resolved-admin-queue')

# Add persisted resolved IDs next to reviewed IDs state.
needle='''    const [adminReviewedIds, setAdminReviewedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_REVIEWED_ORDERS') || '[]'); } catch(e) { return []; } });'''
if needle not in s:
    # tolerate formatting variation; insert after first adminReviewedIds state occurrence
    marker='const [adminReviewedIds, setAdminReviewedIds]'
    i=s.find(marker)
    if i<0: raise SystemExit('adminReviewedIds state not found')
    line_start=s.rfind('\n',0,i)+1; line_end=s.find('\n',i)
    line=s[line_start:line_end]
    insert=line+'\n    const [adminResolvedIds, setAdminResolvedIds] = useState(() => { try { return JSON.parse(localStorage.getItem(\'LA_ADMIN_RESOLVED_ORDERS\') || \'[]\'); } catch(e) { return []; } });'
    s=s[:line_start]+insert+s[line_end:]
else:
    once(needle,needle+'''\n    const [adminResolvedIds, setAdminResolvedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_RESOLVED_ORDERS') || '[]'); } catch(e) { return []; } });''','resolved state')

# Strengthen resolved predicate.
once("const isResolvedOrder = (o) => isTruthyStatus(o === null || o === void 0 ? void 0 : o.delivered) || isTruthyStatus(o === null || o === void 0 ? void 0 : o.rejected) || ['entregado', 'cargado_y_entregado', 'rechazado', 'cancelado', 'resuelto'].includes(orderStatusText(o));",
     "const isResolvedOrder = (o) => isTruthyStatus(o === null || o === void 0 ? void 0 : o.delivered) || isTruthyStatus(o === null || o === void 0 ? void 0 : o.rejected) || isTruthyStatus(o === null || o === void 0 ? void 0 : o.cancelled) || ['entregado', 'cargado_y_entregado', 'rechazado', 'cancelado', 'anulado', 'no pagado', 'no_pagado', 'resuelto'].includes(orderStatusText(o));",
     'resolved predicate')

# Queue must also honor locally resolved IDs while remote persistence catches up.
once("const recentOrders = useMemo(() => mergeOrders(orders).filter(isPendingOrder).sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0, 10), [orders]);",
     "const recentOrders = useMemo(() => mergeOrders(orders).filter(o => isPendingOrder(o) && !adminResolvedIds.includes(normalizeOrderCode(o.id || o.orderId || o.codigo || o.code))).sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0, 10), [orders, adminResolvedIds]);",
     'recent queue')

# Persist resolved IDs.
marker="useEffect(() => { try { localStorage.setItem('LA_ADMIN_REVIEWED_ORDERS', JSON.stringify(adminReviewedIds)); } catch(e) {} }, [adminReviewedIds]);"
once(marker,marker+"\n    useEffect(() => { try { localStorage.setItem('LA_ADMIN_RESOLVED_ORDERS', JSON.stringify(adminResolvedIds)); } catch(e) {} }, [adminResolvedIds]);",'resolved persistence')

# Update local resolved set immediately when decision is made.
old="""        setOrders(localNext);\n        clearOrderBox();\n        focusOrderInput();\n        setAdminMessage(decision === 'delivered' ? 'Pedido marcado como cargado y entregado.' : decision === 'rejected' ? 'Pedido marcado como rechazado.' : 'Pedido reabierto como pendiente.');"""
new="""        setOrders(localNext);\n        const resolvedCode = normalizeOrderCode(order.id);\n        setAdminResolvedIds(prev => decision === 'pending' ? prev.filter(id => id !== resolvedCode) : (prev.includes(resolvedCode) ? prev : [...prev, resolvedCode].slice(-1500)));\n        clearOrderBox();\n        focusOrderInput();\n        setAdminMessage(decision === 'delivered' ? 'Pedido marcado como cargado y entregado. Se quitó de la cola.' : decision === 'rejected' ? 'Pedido marcado como rechazado. Se quitó de la cola.' : 'Pedido reabierto como pendiente y volvió a la cola.');"""
once(old,new,'decision local queue update')

p.write_text(s,encoding='utf-8')
print('v86 patched')
