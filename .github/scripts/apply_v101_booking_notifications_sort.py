from pathlib import Path

idx=Path('index.html')
con=Path('contrataciones.html')
s=idx.read_text(encoding='utf-8')
c=con.read_text(encoding='utf-8')

def once(text,old,new,label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 got {n}')
    return text.replace(old,new,1)

# Main Admin can read public match requests from the same Firebase booking collection.
s=once(s,
'''const ORDERS_COLLECTION_PATH = `artifacts/${FIREBASE_APP_DOC_ID}/orders`;
const LEGACY_ORDERS_COLLECTION_PATH = "la_orders";
const SHARED_STATE_DOC_PATH = `artifacts/${FIREBASE_APP_DOC_ID}/config/shared_state`;''',
'''const ORDERS_COLLECTION_PATH = `artifacts/${FIREBASE_APP_DOC_ID}/orders`;
const LEGACY_ORDERS_COLLECTION_PATH = "la_orders";
const SHARED_STATE_DOC_PATH = `artifacts/${FIREBASE_APP_DOC_ID}/config/shared_state`;
const BOOKINGS_COLLECTION_PATH = `artifacts/${FIREBASE_APP_DOC_ID}/bookings`;''',
'bookings collection constant')

s=once(s,
'''.admin-notif-kind.order{background:rgba(59,130,246,.15);color:#bfdbfe}.admin-notif-kind.club{background:rgba(249,115,22,.15);color:#fed7aa}''',
'''.admin-notif-kind.order{background:rgba(59,130,246,.15);color:#bfdbfe}.admin-notif-kind.club{background:rgba(249,115,22,.15);color:#fed7aa}.admin-notif-kind.request{background:rgba(34,197,94,.15);color:#bbf7d0}''',
'booking notification css')

s=once(s,
'''    const [adminNotificationsOpen, setAdminNotificationsOpen] = useState(false);
    const [adminReviewedIds, setAdminReviewedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_REVIEWED_ORDERS') || '[]'); } catch(e) { return []; } });
    const [adminResolvedIds, setAdminResolvedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_RESOLVED_ORDERS') || '[]'); } catch(e) { return []; } });''',
'''    const [adminNotificationsOpen, setAdminNotificationsOpen] = useState(false);
    const [adminReviewedIds, setAdminReviewedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_REVIEWED_ORDERS') || '[]'); } catch(e) { return []; } });
    const [adminResolvedIds, setAdminResolvedIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_RESOLVED_ORDERS') || '[]'); } catch(e) { return []; } });
    const [adminBookingRequests, setAdminBookingRequests] = useState([]);
    const [adminReviewedBookingIds, setAdminReviewedBookingIds] = useState(() => { try { return JSON.parse(localStorage.getItem('LA_ADMIN_REVIEWED_BOOKING_REQUESTS') || '[]'); } catch(e) { return []; } });''',
'booking notification states')

old='''    const markAdminReviewed = (id) => {
        const clean = normalizeOrderCode(id);
        if (!clean) return;
        setAdminReviewedIds(prev => prev.includes(clean) ? prev : [...prev, clean].slice(-1200));
    };
    const markAllAdminReviewed = () => setAdminReviewedIds(prev => Array.from(new Set([...prev, ...unseenAdminOrders.map(o => normalizeOrderCode(o.id))])).slice(-1200));
    useEffect(() => { try { localStorage.setItem('LA_ADMIN_REVIEWED_ORDERS', JSON.stringify(adminReviewedIds)); } catch(e) {} }, [adminReviewedIds]);
    useEffect(() => { try { localStorage.setItem('LA_ADMIN_RESOLVED_ORDERS', JSON.stringify(adminResolvedIds)); } catch(e) {} }, [adminResolvedIds]);'''
new='''    const unseenAdminBookingRequests = useMemo(() => (adminBookingRequests || []).filter(b => b && b.id && b.requestSource === 'public' && b.status === 'pendiente' && !adminReviewedBookingIds.includes(String(b.id))).sort((a,b) => new Date(b.createdAt || b.updatedAt || 0) - new Date(a.createdAt || a.updatedAt || 0)), [adminBookingRequests, adminReviewedBookingIds]);
    const unseenAdminTotal = unseenAdminOrders.length + unseenAdminBookingRequests.length;
    const markAdminReviewed = (id) => {
        const clean = normalizeOrderCode(id);
        if (!clean) return;
        setAdminReviewedIds(prev => prev.includes(clean) ? prev : [...prev, clean].slice(-1200));
    };
    const markAdminBookingReviewed = (id) => { const clean=String(id||'').trim(); if(!clean)return; setAdminReviewedBookingIds(prev => prev.includes(clean) ? prev : [...prev,clean].slice(-1200)); };
    const markAllAdminReviewed = () => { setAdminReviewedIds(prev => Array.from(new Set([...prev, ...unseenAdminOrders.map(o => normalizeOrderCode(o.id))])).slice(-1200)); setAdminReviewedBookingIds(prev => Array.from(new Set([...prev, ...unseenAdminBookingRequests.map(b => String(b.id))])).slice(-1200)); };
    const openBookingRequestFromNotification = (b) => { if(!b)return; markAdminBookingReviewed(b.id); try { sessionStorage.setItem('la_booking_admin','1'); } catch(e) {} window.location.href=new URL('contrataciones.html#/admin',location.href).href; };
    useEffect(() => { try { localStorage.setItem('LA_ADMIN_REVIEWED_ORDERS', JSON.stringify(adminReviewedIds)); } catch(e) {} }, [adminReviewedIds]);
    useEffect(() => { try { localStorage.setItem('LA_ADMIN_RESOLVED_ORDERS', JSON.stringify(adminResolvedIds)); } catch(e) {} }, [adminResolvedIds]);
    useEffect(() => { try { localStorage.setItem('LA_ADMIN_REVIEWED_BOOKING_REQUESTS', JSON.stringify(adminReviewedBookingIds)); } catch(e) {} }, [adminReviewedBookingIds]);
    useEffect(() => {
        if (route !== "#/admin" || !admin) return;
        let active=true;
        const loadRequests=async()=>{ try { const db=await getFirebaseDb(); if(!db||!active)return; const snap=await db.collection(BOOKINGS_COLLECTION_PATH).where('requestSource','==','public').limit(50).get(); if(!active)return; const list=snap.docs.map(d=>({id:d.id,...d.data()})).filter(b=>b.status==='pendiente'&&b.formCompleted===true).sort((a,b)=>new Date(b.createdAt||b.updatedAt||0)-new Date(a.createdAt||a.updatedAt||0)); setAdminBookingRequests(list); } catch(e) { console.warn('No se pudieron leer solicitudes de partidos.',e); } };
        loadRequests();
        const timer=setInterval(loadRequests,120000);
        return ()=>{active=false;clearInterval(timer)};
    }, [route,admin]);'''
s=once(s,old,new,'booking notification logic')

# Make the quick-copy button explicit.
s=s.replace('React.createElement("i", { className: "fas fa-link mr-2" }), "Solicitudes")','React.createElement("i", { className: "fas fa-link mr-2" }), "Copiar link solicitudes")',1)

old_ui='''                        React.createElement("div", { className:"admin-notif-icon" }, React.createElement("i", { className:"fas fa-bell" }), unseenAdminOrders.length > 0 && React.createElement("span", { className:"admin-notif-count" }, unseenAdminOrders.length > 99 ? '99+' : unseenAdminOrders.length)),
                        React.createElement("div", { className:"min-w-0 text-left" }, React.createElement("b", { className:"block text-sm" }, "Notificaciones"), React.createElement("span", { className:"block text-[11px] text-neutral-400 truncate" }, unseenAdminOrders.length ? `${unseenAdminOrders.length} pedido${unseenAdminOrders.length===1?'':'s'} o canje${unseenAdminOrders.length===1?'':'s'} sin revisar` : "No hay novedades sin revisar"))),
                    React.createElement("i", { className:`fas ${adminNotificationsOpen ? 'fa-chevron-up' : 'fa-chevron-down'} text-neutral-400` })),
                adminNotificationsOpen && React.createElement("div", { className:"admin-notif-panel" },
                    React.createElement("div", { className:"flex items-center justify-between gap-2 mb-2 px-1" }, React.createElement("b", { className:"text-xs" }, "Nuevos pedidos y canjes"), unseenAdminOrders.length > 0 && React.createElement("button", { onClick:markAllAdminReviewed, className:"text-[10px] text-orange-300 font-black" }, "Marcar todo revisado")),
                    unseenAdminOrders.length === 0 && React.createElement("p", { className:"text-xs text-neutral-500 p-2" }, "Cuando llegue un pedido o un canje nuevo, aparecerá acá."),
                    unseenAdminOrders.slice(0,12).map(o => { const isClub=o.type==='benefit_redemption'||o.benefitRedemption===true; return React.createElement("button", { key:o.id, onClick:() => openOrderFromQueue(o), className:"admin-notif-item" }, React.createElement("div", { className:"min-w-0" }, React.createElement("div", { className:"flex items-center gap-2" }, React.createElement("span", { className:`admin-notif-kind ${isClub?'club':'order'}` }, isClub?'CANJE CLUB':'PEDIDO'), React.createElement("b", { className:"text-xs truncate" }, `#${o.id}`)), React.createElement("p", { className:"text-[10px] text-neutral-500 mt-1 truncate" }, `${o.customerName||'Sin nombre'} · ${isClub ? (o.rewardName||'Beneficio') : formatPrice(o.total)}`)), React.createElement("i", { className:"fas fa-chevron-right text-neutral-600 text-xs" })); })) ),'''
new_ui='''                        React.createElement("div", { className:"admin-notif-icon" }, React.createElement("i", { className:"fas fa-bell" }), unseenAdminTotal > 0 && React.createElement("span", { className:"admin-notif-count" }, unseenAdminTotal > 99 ? '99+' : unseenAdminTotal)),
                        React.createElement("div", { className:"min-w-0 text-left" }, React.createElement("b", { className:"block text-sm" }, "Notificaciones"), React.createElement("span", { className:"block text-[11px] text-neutral-400 truncate" }, unseenAdminTotal ? `${unseenAdminTotal} novedad${unseenAdminTotal===1?'':'es'} sin revisar` : "No hay novedades sin revisar"))),
                    React.createElement("i", { className:`fas ${adminNotificationsOpen ? 'fa-chevron-up' : 'fa-chevron-down'} text-neutral-400` })),
                adminNotificationsOpen && React.createElement("div", { className:"admin-notif-panel" },
                    React.createElement("div", { className:"flex items-center justify-between gap-2 mb-2 px-1" }, React.createElement("b", { className:"text-xs" }, "Nuevos pedidos, canjes y partidos"), unseenAdminTotal > 0 && React.createElement("button", { onClick:markAllAdminReviewed, className:"text-[10px] text-orange-300 font-black" }, "Marcar todo revisado")),
                    unseenAdminTotal === 0 && React.createElement("p", { className:"text-xs text-neutral-500 p-2" }, "Cuando llegue un pedido, un canje o una solicitud de partido, aparecerá acá."),
                    unseenAdminBookingRequests.slice(0,8).map(b => React.createElement("button", { key:`booking-${b.id}`, onClick:() => openBookingRequestFromNotification(b), className:"admin-notif-item" }, React.createElement("div", { className:"min-w-0" }, React.createElement("div", { className:"flex items-center gap-2" }, React.createElement("span", { className:"admin-notif-kind request" }, "PARTIDO"), React.createElement("b", { className:"text-xs truncate" }, `${b.home||'Local'} vs ${b.away||'Visitante'}`)), React.createElement("p", { className:"text-[10px] text-neutral-500 mt-1 truncate" }, `${b.date||'Sin fecha'} · ${b.category||'Sin categoría'} · ${b.clientName||'Sin nombre'}`)), React.createElement("i", { className:"fas fa-calendar-days text-emerald-400 text-xs" }))),
                    unseenAdminOrders.slice(0,12).map(o => { const isClub=o.type==='benefit_redemption'||o.benefitRedemption===true; return React.createElement("button", { key:o.id, onClick:() => openOrderFromQueue(o), className:"admin-notif-item" }, React.createElement("div", { className:"min-w-0" }, React.createElement("div", { className:"flex items-center gap-2" }, React.createElement("span", { className:`admin-notif-kind ${isClub?'club':'order'}` }, isClub?'CANJE CLUB':'PEDIDO'), React.createElement("b", { className:"text-xs truncate" }, `#${o.id}`)), React.createElement("p", { className:"text-[10px] text-neutral-500 mt-1 truncate" }, `${o.customerName||'Sin nombre'} · ${isClub ? (o.rewardName||'Beneficio') : formatPrice(o.total)}`)), React.createElement("i", { className:"fas fa-chevron-right text-neutral-600 text-xs" })); })) ),'''
s=once(s,old_ui,new_ui,'notification panel requests')

idx.write_text(s,encoding='utf-8')

# Agenda: upcoming matches first, from closest to farthest. Recent past matches remain afterwards, newest first.
old_sort="""async function listBookings(){const snap=await db.collection(BOOKINGS_PATH).limit(500).get();let items=snap.docs.map(d=>({id:d.id,...d.data()}));items=await purgeExpiredBookings(items);items=items.filter(isAgendaBooking);return items.sort((a,b)=>{const am=bookingDateMs(a),bm=bookingDateMs(b);if(Number.isFinite(am)&&Number.isFinite(bm)&&bm!==am)return bm-am;if(Number.isFinite(bm)&&!Number.isFinite(am))return 1;if(Number.isFinite(am)&&!Number.isFinite(bm))return -1;return String(b.updatedAt||b.createdAt||'').localeCompare(String(a.updatedAt||a.createdAt||''))})}"""
new_sort="""async function listBookings(){const snap=await db.collection(BOOKINGS_PATH).limit(500).get();let items=snap.docs.map(d=>({id:d.id,...d.data()}));items=await purgeExpiredBookings(items);items=items.filter(isAgendaBooking);const now=Date.now();return items.sort((a,b)=>{const am=bookingDateMs(a),bm=bookingDateMs(b),af=Number.isFinite(am)&&am>=now,bf=Number.isFinite(bm)&&bm>=now;if(af!==bf)return af?-1:1;if(af&&bf&&am!==bm)return am-bm;if(Number.isFinite(am)&&Number.isFinite(bm)&&am!==bm)return bm-am;if(Number.isFinite(am)!==Number.isFinite(bm))return Number.isFinite(am)?-1:1;return String(b.updatedAt||b.createdAt||'').localeCompare(String(a.updatedAt||a.createdAt||''))})}"""
c=once(c,old_sort,new_sort,'chronological agenda sorting')
con.write_text(c,encoding='utf-8')
print('v101 booking notifications + chronological agenda sorting patched')
