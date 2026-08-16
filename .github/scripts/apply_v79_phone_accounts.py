from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v78-redemption-contact','v79-phone-club-accounts')

once('''    const [manualPointsDni, setManualPointsDni] = useState("");
    const [manualPointsAmount, setManualPointsAmount] = useState(1);
    const [manualPointsSaving, setManualPointsSaving] = useState(false);
    const [clubPointsOpen, setClubPointsOpen] = useState(false);
    const [clubLookupDni, setClubLookupDni] = useState("");''','''    const [manualPointsDni, setManualPointsDni] = useState("");
    const [manualPointsAmount, setManualPointsAmount] = useState(1);
    const [manualPointsSaving, setManualPointsSaving] = useState(false);
    const [pointsAdminOpen, setPointsAdminOpen] = useState(false);
    const [transferFromPhone, setTransferFromPhone] = useState("");
    const [transferToPhone, setTransferToPhone] = useState("");
    const [transferPointsAmount, setTransferPointsAmount] = useState(1);
    const [clubUsers, setClubUsers] = useState([]);
    const [clubSessionPhone, setClubSessionPhone] = useState(() => { try { return localStorage.getItem('LA_CLUB_PHONE') || ''; } catch(e) { return ''; } });
    const [clubRegisterName, setClubRegisterName] = useState("");
    const [clubRegisterSurname, setClubRegisterSurname] = useState("");
    const [clubPointsOpen, setClubPointsOpen] = useState(false);
    const [clubLookupDni, setClubLookupDni] = useState("");''','states')

once('''            if (Array.isArray(state.clubProducts))
                setClubProducts(withDefaultClubProducts(state.clubProducts));
            setSharedReady(true);''','''            if (Array.isArray(state.clubProducts))
                setClubProducts(withDefaultClubProducts(state.clubProducts));
            if (Array.isArray(state.clubUsers))
                setClubUsers(state.clubUsers);
            setSharedReady(true);''','load users')
once('''            if (Array.isArray(state.clubProducts))
                setClubProducts(withDefaultClubProducts(state.clubProducts));
        });''','''            if (Array.isArray(state.clubProducts))
                setClubProducts(withDefaultClubProducts(state.clubProducts));
            if (Array.isArray(state.clubUsers))
                setClubUsers(state.clubUsers);
        });''','sub users')
once('''    useEffect(() => {
        if (!sharedReady) return;
        const timer = setTimeout(() => {
            saveSharedAdminState({ clubProducts }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar el Club de beneficios.'); });
        }, 450);
        return () => clearTimeout(timer);
    }, [clubProducts, sharedReady]);''','''    useEffect(() => {
        if (!sharedReady) return;
        const timer = setTimeout(() => {
            saveSharedAdminState({ clubProducts }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar el Club de beneficios.'); });
        }, 450);
        return () => clearTimeout(timer);
    }, [clubProducts, sharedReady]);
    useEffect(() => {
        if (!sharedReady) return;
        const timer = setTimeout(() => saveSharedAdminState({ clubUsers }).catch(e => console.warn('No se pudieron sincronizar usuarios del Club.', e)), 450);
        return () => clearTimeout(timer);
    }, [clubUsers, sharedReady]);''','persist users')

old='''    const clubAccountFromOrders = (list, rawDni) => {
        const dni = String(rawDni || '').replace(/\\D/g, '');
        const account = { dni, name:'', phone:'', purchases:0, spent:0, pending:0, cancelled:0, prints:0, redeemedPoints:0, redemptions:0, earnedPoints:0, directBonusPoints:0, manualPoints:0, points:0 };
        if (!dni) return account;
        mergeOrders(list || []).forEach(o => {
            if (String(o.dni || o.customerDni || '').replace(/\\D/g, '') !== dni) return;
            const status = norm(o.status || o.estado || '');
            const cancelled = isTruthyStatus(o.rejected) || ['rechazado','cancelado','anulado','no pagado','no_pagado'].includes(status);
            const isRedemption = o.type === 'benefit_redemption' || o.benefitRedemption === true;
            const isManualPoints = o.type === 'club_points_adjustment' || o.manualPointsAdjustment === true;
            account.name = String(o.customerName || o.nombreApellido || account.name || '').trim();
            account.phone = String(o.phone || o.celular || account.phone || '').replace(/\\D/g, '');
            if (isManualPoints) {
                if (!cancelled) account.manualPoints += Math.max(0, Math.round(Number(o.manualPoints || o.pointsAdjustment) || 0));
                return;
            }
            if (isRedemption) {
                if (!cancelled) {
                    account.redeemedPoints += Math.max(0, Number(o.redeemedPoints) || 0);
                    account.redemptions += 1;
                }
                return;
            }
            const confirmed = isTruthyStatus(o.delivered);
            if (cancelled) account.cancelled += 1;
            else if (confirmed) {
                account.purchases += 1;
                const purchaseAmount = Math.max(0, Number(o.total) || 0);
                account.spent += purchaseAmount;
                if (purchaseAmount >= 10000) account.directBonusPoints += 1;
                account.prints += Math.max(0, Number(o.printCount) || (o.printRequested ? 1 : 0));
            } else account.pending += 1;
        });
        account.earnedPoints = Math.floor(account.spent / 5000) + account.directBonusPoints + account.manualPoints;
        account.points = Math.max(0, account.earnedPoints - account.redeemedPoints);
        return account;
    };
    const customerDniStats = useMemo(() => {
        const dnis = new Set();
        mergeOrders(orders).forEach(o => {
            const dni = String(o.dni || o.customerDni || '').replace(/\\D/g, '');
            if (dni) dnis.add(dni);
        });
        return Array.from(dnis).map(dni => clubAccountFromOrders(orders, dni)).sort((a,b) => b.points - a.points || b.spent - a.spent || b.purchases - a.purchases);
    }, [orders]);
    const ADMIN_HISTORY_RESET_AT = Date.parse('2026-08-16T02:03:00Z');
    const adminOrderLedger = useMemo(() => mergeOrders(orders).filter(o => { const ts = Date.parse((o && o.date) || 0); return Number.isFinite(ts) && ts >= ADMIN_HISTORY_RESET_AT; }).sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0,200), [orders]);'''
new='''    const normalizeClubPhone = value => {
        let d = String(value || '').replace(/\\D/g, '');
        if (!d) return '';
        if (d.startsWith('00')) d = d.slice(2);
        if (d.startsWith('54')) d = d.slice(2);
        if (d.startsWith('9') && d.length === 11) d = d.slice(1);
        d = d.replace(/^0+/, '');
        if (d.length === 12) {
            for (const pos of [2,3,4]) if (d.slice(pos,pos+2) === '15') { d = d.slice(0,pos) + d.slice(pos+2); break; }
        }
        if (d.startsWith('15') && d.length === 9) d = '351' + d.slice(2);
        if (d.length === 7) d = '351' + d;
        return d;
    };
    const clubProfileForPhone = phone => clubUsers.find(u => normalizeClubPhone(u.phone) === normalizeClubPhone(phone)) || null;
    const clubAccountFromOrders = (list, rawPhone) => {
        const phone = normalizeClubPhone(rawPhone);
        const profile = clubProfileForPhone(phone);
        const account = { phone, name:profile ? `${profile.name || ''} ${profile.surname || ''}`.trim() : '', purchases:0, spent:0, pending:0, cancelled:0, prints:0, redeemedPoints:0, redemptions:0, earnedPoints:0, directBonusPoints:0, manualPoints:0, transferPoints:0, points:0 };
        if (!phone) return account;
        mergeOrders(list || []).forEach(o => {
            const orderPhone = normalizeClubPhone(o.phone || o.celular || o.customerPhone);
            const isTransfer = o.type === 'club_points_transfer';
            if (isTransfer) {
                if (normalizeClubPhone(o.fromPhone) === phone) account.transferPoints -= Math.max(0, Number(o.transferredPoints) || 0);
                if (normalizeClubPhone(o.toPhone) === phone) account.transferPoints += Math.max(0, Number(o.transferredPoints) || 0);
                return;
            }
            if (orderPhone !== phone) return;
            const status = norm(o.status || o.estado || '');
            const cancelled = isTruthyStatus(o.rejected) || ['rechazado','cancelado','anulado','no pagado','no_pagado'].includes(status);
            const isRedemption = o.type === 'benefit_redemption' || o.benefitRedemption === true;
            const isManualPoints = o.type === 'club_points_adjustment' || o.manualPointsAdjustment === true;
            account.name = String(o.customerName || o.nombreApellido || account.name || '').trim();
            if (isManualPoints) {
                if (!cancelled) account.manualPoints += Math.round(Number(o.manualPoints || o.pointsAdjustment) || 0);
                return;
            }
            if (isRedemption) {
                if (!cancelled) { account.redeemedPoints += Math.max(0, Number(o.redeemedPoints) || 0); account.redemptions += 1; }
                return;
            }
            const confirmed = isTruthyStatus(o.delivered);
            if (cancelled) account.cancelled += 1;
            else if (confirmed) {
                account.purchases += 1;
                const purchaseAmount = Math.max(0, Number(o.total) || 0);
                account.spent += purchaseAmount;
                if (purchaseAmount >= 10000) account.directBonusPoints += 1;
                account.prints += Math.max(0, Number(o.printCount) || (o.printRequested ? 1 : 0));
            } else account.pending += 1;
        });
        account.earnedPoints = Math.floor(account.spent / 5000) + account.directBonusPoints + account.manualPoints + account.transferPoints;
        account.points = Math.max(0, account.earnedPoints - account.redeemedPoints);
        return account;
    };
    const customerDniStats = useMemo(() => {
        const phones = new Set(clubUsers.map(u => normalizeClubPhone(u.phone)).filter(Boolean));
        mergeOrders(orders).forEach(o => { const phone = normalizeClubPhone(o.phone || o.celular || o.customerPhone); if (phone) phones.add(phone); });
        return Array.from(phones).map(phone => clubAccountFromOrders(orders, phone)).sort((a,b) => b.points - a.points || b.spent - a.spent || b.purchases - a.purchases);
    }, [orders, clubUsers]);
    const ADMIN_HISTORY_RESET_AT = Date.parse('2026-08-16T02:03:00Z');
    const adminOrderLedger = useMemo(() => mergeOrders(orders).filter(o => { const ts = Date.parse((o && o.date) || 0); return Number.isFinite(ts) && ts >= ADMIN_HISTORY_RESET_AT && !isTruthyStatus(o.delivered); }).sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0)).slice(0,200), [orders]);'''
once(old,new,'account model')

once('''    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;
        return `${base || (location.href || '').split('#')[0]}#/galeria`;
    };''','''    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;
        const target = route === '#/admin' ? '#/admin' : '#/galeria';
        try { localStorage.setItem('LA_INSTALL_START_ROUTE', target); } catch(e) {}
        return `${base || (location.href || '').split('#')[0]}${target}`;
    };''','install url')

once('''    useEffect(() => { const h = () => { const hash = location.hash || "#/galeria"; setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);''','''    useEffect(() => { const h = () => { let hash = location.hash || "#/galeria"; try { const standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; const saved = localStorage.getItem('LA_INSTALL_START_ROUTE'); if (standalone && saved === '#/admin' && (!location.hash || location.hash === '#/galeria')) { location.hash = '#/admin'; hash = '#/admin'; } if (hash === '#/admin') localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);''','standalone admin')

start=s.index('    const normalizeDni = value =>')
end=s.index('    const applyCoupon = () =>', start)
replacement='''    const normalizeDni = value => String(value || "").replace(/\\D/g, "");
    const normalizePhone = value => normalizeClubPhone(value);
    const customerWhatsappUrl = rawPhone => {
        const local = normalizeClubPhone(rawPhone);
        if (!local) return '';
        return `https://api.whatsapp.com/send?phone=549${local}&text=${encodeURIComponent('Hola! Te escribo de lucasabraham.ph por tu pedido o canje para coordinar la entrega.')}`;
    };
    const saveCheckoutCustomer = async () => {
        const name = String(checkoutCustomerName || "").trim().replace(/\\s{2,}/g, " ");
        const phone = normalizeClubPhone(checkoutPhone);
        if (!name) { alert("Ingresá nombre y apellido."); return; }
        if (!phone || phone.length < 10) { alert("Ingresá un celular válido. Es obligatorio y se usa para identificar tus puntos."); return; }
        setCheckoutCustomerName(name); setCheckoutPhone(phone); setCheckoutDni(''); setCheckoutWantsPoints(true);
        setCustomerDetailsSaved(true); setCustomerSavedMessage("✓ Datos guardados · tus puntos quedan asociados a este celular");
        const parts=name.split(/\\s+/); const profile={ phone, name:parts.shift() || name, surname:parts.join(' '), updatedAt:new Date().toISOString() };
        setClubUsers(prev => { const rest=prev.filter(u => normalizeClubPhone(u.phone)!==phone); return [{...(prev.find(u=>normalizeClubPhone(u.phone)===phone)||{}),...profile},...rest]; });
        try { localStorage.setItem('LA_CLUB_PHONE', phone); } catch(e) {} setClubSessionPhone(phone);
        setCheckoutPointsLoading(true);
        try { const history=await loadClubOrdersForPhone(phone); setCheckoutPriorClubAccount(clubAccountFromOrders(history,phone)); } catch(e) { console.warn(e); } finally { setCheckoutPointsLoading(false); }
        setTimeout(() => { setCustomerDetailsOpen(false); setCustomerSavedMessage(""); }, 900);
    };
'''
s=s[:start]+replacement+s[end:]

s=s.replace('''        const cleanDni = normalizeDni(checkoutDni);
        const cleanPhone = normalizePhone(checkoutPhone);''','''        const cleanPhone = normalizeClubPhone(checkoutPhone);''')
s=s.replace('''        if (cleanDni) msg += `${EM.point} *DNI:* ${cleanDni}${checkoutWantsPoints ? " · Acumula puntos del Club" : ""}\n`;''','''        msg += `${EM.point} *Club:* puntos asociados al celular ${cleanPhone}\n`;''')
s=s.replace('''            dni: normalizeDni(checkoutDni),
            phone: normalizePhone(checkoutPhone),
            wantsPoints: Boolean(checkoutWantsPoints && normalizeDni(checkoutDni)),''','''            dni: '',
            phone: normalizeClubPhone(checkoutPhone),
            wantsPoints: true,''')

start=s.index('    async function addManualClubPoints()')
end=s.index('    const addCoupon = () => {', start)
replacement='''    async function addManualClubPoints() {
        const phone = normalizeClubPhone(manualPointsDni);
        const amount = Math.max(1, Math.round(Number(manualPointsAmount) || 0));
        if (!phone || phone.length < 10) { setAdminMessage('Ingresá un celular válido para sumar puntos.'); return; }
        setManualPointsSaving(true);
        try {
            const account = clubAccountFromOrders(orders, phone); const profile=clubProfileForPhone(phone); const now = new Date().toISOString();
            const adjustment = { id:'CP-' + Date.now().toString(36).toUpperCase() + '-' + Math.floor(100 + Math.random()*900), date:now, type:'club_points_adjustment', manualPointsAdjustment:true, manualPoints:amount, pointsAdjustment:amount, phone, customerName:account.name || (profile ? `${profile.name||''} ${profile.surname||''}`.trim() : ''), subtotal:0, total:0, delivered:true, rejected:false, status:'acreditado', paid:true, source:'admin_manual_points' };
            const saved=await saveOrderRemote(adjustment); if(!saved.firebase&&!saved.script) throw new Error(saved.error||'No se pudo guardar');
            const next=mergeOrders(readLocalOrders(),orders,[adjustment]); saveLocalOrders(next); setOrders(next); setManualPointsAmount(1); setAdminMessage(`Se añadieron ${amount} punto${amount===1?'':'s'} al celular ${phone}.`);
        } catch(e) { console.error(e); setAdminMessage('No se pudieron guardar los puntos manuales.'); } finally { setManualPointsSaving(false); }
    }
    async function transferClubPoints() {
        const from=normalizeClubPhone(transferFromPhone), to=normalizeClubPhone(transferToPhone), amount=Math.max(1,Math.round(Number(transferPointsAmount)||0));
        if(!from||!to||from===to) { setAdminMessage('Ingresá dos celulares distintos y válidos.'); return; }
        const account=clubAccountFromOrders(orders,from); if(account.points<amount){ setAdminMessage(`El origen tiene ${account.points} puntos; no alcanza para transferir ${amount}.`); return; }
        const movement={ id:'CT-'+Date.now().toString(36).toUpperCase()+'-'+Math.floor(100+Math.random()*900), date:new Date().toISOString(), type:'club_points_transfer', fromPhone:from, toPhone:to, transferredPoints:amount, delivered:true, status:'acreditado', subtotal:0,total:0 };
        try { const saved=await saveOrderRemote(movement); if(!saved.firebase&&!saved.script) throw new Error(saved.error||'No se pudo guardar'); const next=mergeOrders(readLocalOrders(),orders,[movement]); saveLocalOrders(next); setOrders(next); setTransferPointsAmount(1); setAdminMessage(`Transferidos ${amount} puntos de ${from} a ${to}.`); } catch(e){ console.error(e); setAdminMessage('No se pudo completar la transferencia.'); }
    }
    const toggleClubProduct = (id) => setClubProducts(prev => prev.map(p => p.id === id ? { ...p, active:p.active === false ? true : false } : p));
    const deleteClubProduct = (id) => setClubProducts(prev => prev.filter(p => p.id !== id));
    async function loadClubOrdersForPhone(rawPhone) {
        const phone=normalizeClubPhone(rawPhone); if(!phone) return [];
        try { const all=await loadOrdersRemote(); return mergeOrders(all).filter(o => normalizeClubPhone(o.phone||o.celular||o.customerPhone)===phone || (o.type==='club_points_transfer' && [normalizeClubPhone(o.fromPhone),normalizeClubPhone(o.toPhone)].includes(phone))); } catch(e){ console.warn(e); }
        return mergeOrders(readLocalOrders()).filter(o => normalizeClubPhone(o.phone||o.celular||o.customerPhone)===phone || (o.type==='club_points_transfer' && [normalizeClubPhone(o.fromPhone),normalizeClubPhone(o.toPhone)].includes(phone)));
    }
    async function lookupClubPoints() {
        const phone=normalizeClubPhone(clubLookupDni); if(!phone||phone.length<10){ setClubMessage('Ingresá un celular válido.'); return; }
        const profile=clubProfileForPhone(phone); if(!profile){ setClubLookupResult(null); setClubMessage('Ese celular todavía no está registrado. Completá nombre y apellido para crear tu cuenta.'); return; }
        setClubLookupDni(phone); setClubLookupLoading(true); setClubMessage('');
        try { const list=await loadClubOrdersForPhone(phone); const account=clubAccountFromOrders(list,phone); setClubLookupResult(account); setClubSessionPhone(phone); try{localStorage.setItem('LA_CLUB_PHONE',phone);}catch(e){} setClubMessage(account.points>0?`Tenés ${account.points} puntos disponibles.`:'Todavía no tenés puntos disponibles.'); } catch(e){ setClubMessage('No pudimos consultar tus puntos ahora.'); } finally { setClubLookupLoading(false); }
    }
    async function registerClubUser() {
        const phone=normalizeClubPhone(clubLookupDni); const name=String(clubRegisterName||'').trim(); const surname=String(clubRegisterSurname||'').trim();
        if(!name||!surname||!phone||phone.length<10){ setClubMessage('Completá nombre, apellido y un celular válido.'); return; }
        const user={phone,name,surname,createdAt:new Date().toISOString()}; setClubUsers(prev=>[user,...prev.filter(u=>normalizeClubPhone(u.phone)!==phone)]); setClubSessionPhone(phone); try{localStorage.setItem('LA_CLUB_PHONE',phone);}catch(e){} setClubMessage('✓ Cuenta creada. Tus compras con este celular sumarán puntos.');
        try { const list=await loadClubOrdersForPhone(phone); setClubLookupResult(clubAccountFromOrders(list,phone)); } catch(e){}
    }
    const logoutClub=()=>{ setClubSessionPhone(''); setClubLookupResult(null); setClubLookupDni(''); try{localStorage.removeItem('LA_CLUB_PHONE');}catch(e){} };
    async function redeemClubProduct(product) {
        if(!product||product.active===false) return; const phone=normalizeClubPhone(clubSessionPhone||clubLookupDni); const profile=clubProfileForPhone(phone);
        if(!phone||!profile){ setClubPointsOpen(true); setClubMessage('Primero iniciá sesión con tu celular o registrate.'); return; }
        setClubRedeeming(product.id);
        try { const latest=await loadClubOrdersForPhone(phone); const account=clubAccountFromOrders(latest,phone); if(account.points<Number(product.points||0)){setClubLookupResult(account);setClubMessage(`Necesitás ${product.points} puntos y tenés ${account.points}.`);return;} if(!confirm(`¿Canjear ${product.name} por ${product.points} puntos?`))return; const redemption={id:'CB-'+Date.now().toString(36).toUpperCase()+'-'+Math.floor(100+Math.random()*900),date:new Date().toISOString(),type:'benefit_redemption',benefitRedemption:true,rewardId:product.id,rewardName:product.name,redeemedPoints:Number(product.points)||0,phone,customerName:`${profile.name||''} ${profile.surname||''}`.trim(),subtotal:0,total:0,items:[],delivered:false,rejected:false,status:'canje_pendiente'}; const status=await saveOrderRemote(redemption); if(!status.firebase&&!status.script)throw new Error(status.error||'No se pudo guardar'); const next={...account,redeemedPoints:account.redeemedPoints+redemption.redeemedPoints,redemptions:account.redemptions+1,points:Math.max(0,account.points-redemption.redeemedPoints)}; setClubLookupResult(next);setClubMessage(`✓ Canje solicitado: ${product.name}. Te quedan ${next.points} puntos.`); } catch(e){console.error(e);setClubMessage('No pudimos registrar el canje.');} finally{setClubRedeeming('');}
    }
'''
s=s[:start]+replacement+s[end:]

# Hide delivered from notifications too
s=s.replace("return id && Number.isFinite(ts) && ts >= ADMIN_NOTIFICATION_START && !adminReviewedIds.includes(id);","return id && Number.isFinite(ts) && ts >= ADMIN_NOTIFICATION_START && !isTruthyStatus(o.delivered) && !isTruthyStatus(o.rejected) && !adminReviewedIds.includes(id);")

# Checkout UI: phone is mandatory identity, remove DNI
old='''                            React.createElement("b", null, customerDetailsSaved ? "Datos listos para sumar puntos" : "Quiero sumar puntos con esta compra"),
                            React.createElement("small", null, customerDetailsSaved ? "Se acreditan cuando el pedido quede entregado" : "El DNI identifica tu cuenta y permite acumular los puntos")),'''
new='''                            React.createElement("b", null, customerDetailsSaved ? "Datos listos para sumar puntos" : "Identificate para sumar puntos"),
                            React.createElement("small", null, customerDetailsSaved ? "Se acreditan cuando el pedido quede entregado" : "Tu celular es obligatorio y funciona como tu cuenta del Club")),'''
once(old,new,'checkout intro')
old='''                            React.createElement("input", { value:checkoutPhone, inputMode:"tel", onChange:e => { setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"Celular", className:"customer-compact-input" }),
                            React.createElement("div", null,
                                React.createElement("input", { value:checkoutDni, inputMode:"numeric", onChange:e => { setCheckoutDni(e.target.value); setCustomerDetailsSaved(false); setCheckoutPriorClubAccount(null); }, placeholder:"DNI (opcional · para acumular puntos)", className:"customer-compact-input" }),
                                React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "El DNI es el dato que identifica tu cuenta para acumular puntos del Club.")),
                            React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-coins mr-2" }), "Guardar y sumar puntos con la compra"),'''
new='''                            React.createElement("input", { value:checkoutPhone, inputMode:"tel", required:true, onChange:e => { setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false); setCheckoutPriorClubAccount(null); }, placeholder:"Celular obligatorio · ej. 351 1234567", className:"customer-compact-input" }),
                            React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "Usamos tu celular para tu cuenta y tus puntos. 351, 0351, 15, +54 9 y formatos equivalentes se unifican automáticamente."),
                            React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-coins mr-2" }), "Guardar datos y sumar puntos"),'''
once(old,new,'checkout inputs')
s=s.replace('customerDetailsSaved && normalizeDni(checkoutDni) && React.createElement','customerDetailsSaved && normalizeClubPhone(checkoutPhone) && React.createElement',1)

# Canje detail and queue: remove DNI
s=s.replace('''                                        React.createElement("span", null, React.createElement("i", { className:"fas fa-id-card mr-2 text-emerald-300" }), `DNI ${matchedOrder.dni || matchedOrder.customerDni || 'Sin DNI'}`),
                                        React.createElement("span", null, React.createElement("i", { className:"fas fa-phone mr-2 text-emerald-300" }), matchedOrder.phone || matchedOrder.celular || 'Sin teléfono')),''','''                                        React.createElement("span", null, React.createElement("i", { className:"fas fa-phone mr-2 text-emerald-300" }), matchedOrder.phone || matchedOrder.celular || 'Sin teléfono')),''')
s=s.replace("`DNI ${o.dni || o.customerDni || 'Sin DNI'} · ${o.phone || o.celular || 'Sin teléfono'} · ${o.rewardName || 'Beneficio'}`","`${o.phone || o.celular || 'Sin teléfono'} · ${o.rewardName || 'Beneficio'}`")

# Admin manual points/table/history section
start=s.index('                React.createElement("div", { className:"bg-black/30 border border-emerald-500/20 rounded-2xl p-4 mb-5" },')
end=s.index('                React.createElement("h3", { className:"font-black text-lg mt-5 mb-3" }, "Historial de pedidos y canjes")',start)
adminblock='''                React.createElement("div", { className:"bg-black/30 border border-emerald-500/20 rounded-2xl p-4 mb-5" },
                    React.createElement("h3", { className:"font-black text-sm mb-3" }, React.createElement("i", { className:"fas fa-coins mr-2 text-emerald-300" }), "Gestión de puntos por celular"),
                    React.createElement("div", { className:"grid sm:grid-cols-[1fr,110px,auto] gap-2 mb-3" },
                        React.createElement("input", { value:manualPointsDni, inputMode:"tel", onChange:e=>setManualPointsDni(e.target.value), placeholder:"Celular del usuario", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm" }),
                        React.createElement("input", { type:"number", min:"1", value:manualPointsAmount, onChange:e=>setManualPointsAmount(e.target.value), placeholder:"Puntos", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm" }),
                        React.createElement("button", { onClick:addManualClubPoints, disabled:manualPointsSaving, className:"bg-emerald-500 text-black rounded-xl px-4 py-3 text-xs font-black" }, manualPointsSaving?"Guardando...":"Añadir puntos")),
                    React.createElement("div", { className:"grid sm:grid-cols-[1fr,1fr,90px,auto] gap-2" },
                        React.createElement("input", { value:transferFromPhone, inputMode:"tel", onChange:e=>setTransferFromPhone(e.target.value), placeholder:"Celular origen", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm" }),
                        React.createElement("input", { value:transferToPhone, inputMode:"tel", onChange:e=>setTransferToPhone(e.target.value), placeholder:"Celular destino", className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm" }),
                        React.createElement("input", { type:"number", min:"1", value:transferPointsAmount, onChange:e=>setTransferPointsAmount(e.target.value), className:"bg-black border border-neutral-700 rounded-xl px-3 py-3 text-sm" }),
                        React.createElement("button", { onClick:transferClubPoints, className:"bg-sky-500 text-black rounded-xl px-4 py-3 text-xs font-black" }, "Transferir"))),
                React.createElement("button", { type:"button", onClick:()=>setPointsAdminOpen(v=>!v), className:"w-full mb-3 bg-neutral-800 rounded-xl px-4 py-3 text-sm font-black flex items-center justify-between" }, React.createElement("span", null, React.createElement("i", { className:"fas fa-users mr-2" }), "Usuarios y puntos"), React.createElement("i", { className:`fas ${pointsAdminOpen?'fa-chevron-up':'fa-chevron-down'}` })),
                pointsAdminOpen && React.createElement("div", { className:"grid gap-2 mb-4" },
                    customerDniStats.length===0 && React.createElement("p", { className:"text-sm text-neutral-500" }, "Todavía no hay usuarios con teléfono registrado."),
                    customerDniStats.map(r=>React.createElement("div", { key:r.phone, className:"bg-neutral-950 border border-neutral-800 rounded-2xl p-3 grid grid-cols-[1fr,auto] gap-3 items-center" },
                        React.createElement("div", { className:"min-w-0" }, React.createElement("b", { className:"block text-sm truncate" }, r.name||'Sin nombre'), React.createElement("span", { className:"block text-xs text-neutral-400" }, r.phone), React.createElement("span", { className:"block text-[10px] text-neutral-500 mt-1" }, `${r.purchases} compras · ${formatPrice(r.spent)} · ${r.redeemedPoints} canjeados`)),
                        React.createElement("div", { className:"text-right" }, React.createElement("b", { className:"block text-2xl text-orange-300" }, r.points), React.createElement("span", { className:"text-[9px] text-neutral-500" }, "puntos"))))),
'''
s=s[:start]+adminblock+s[end:]
# History display no DNI
s=s.replace('''                            React.createElement("p", { className:"text-xs text-neutral-400 mt-1" }, (o.customerName || 'Sin nombre'), " · DNI ", (o.dni || '—'), " · ", (o.phone || '—'), isRedemption ? ` · ${o.rewardName || 'Beneficio'} · -${o.redeemedPoints || 0} pts` : ` · ${formatPrice(o.total)}`)),''','''                            React.createElement("p", { className:"text-xs text-neutral-400 mt-1" }, (o.customerName || 'Sin nombre'), " · ", (o.phone || '—'), isRedemption ? ` · ${o.rewardName || 'Beneficio'} · -${o.redeemedPoints || 0} pts` : ` · ${formatPrice(o.total)}`)),''')

# Club modal login/register replacing DNI lookup
old='''                React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-coins" }), clubPointsOpen ? "Ocultar mis puntos" : "Ver puntos acumulados"),
                clubPointsOpen && React.createElement("div", { className:"club-account-card mb-4" },
                    React.createElement("p", { className:"text-xs font-black text-orange-100 mb-2" }, "Consultá con tu DNI"),
                    React.createElement("div", { className:"flex flex-col sm:flex-row gap-2" }, React.createElement("input", { value:clubLookupDni, inputMode:"numeric", onChange:e => { setClubLookupDni(e.target.value); setClubLookupResult(null); }, placeholder:"DNI sin puntos", className:"customer-compact-input flex-1" }), React.createElement("button", { type:"button", onClick:lookupClubPoints, disabled:clubLookupLoading, className:"club-points-btn sm:min-w-[150px]" }, clubLookupLoading ? "Consultando..." : "Ver mis puntos")),
                    clubLookupResult && React.createElement("div", { className:"grid grid-cols-3 gap-2 mt-3 text-center" }, React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-orange-300" }, clubLookupResult.points), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "disponibles")), React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.earnedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "ganados")), React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.redeemedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "canjeados"))),
                    clubMessage && React.createElement("p", { className:"text-[11px] text-orange-100/85 mt-2 leading-relaxed" }, clubMessage)),'''
new='''                React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-user" }), clubPointsOpen ? "Ocultar mi cuenta" : (clubSessionPhone ? "Mi cuenta y puntos" : "Ingresar / registrarme")),
                clubPointsOpen && React.createElement("div", { className:"club-account-card mb-4" },
                    !clubSessionPhone ? React.createElement(React.Fragment,null,
                        React.createElement("p", { className:"text-xs font-black text-orange-100 mb-2" }, "Ingresá solamente con tu celular"),
                        React.createElement("div", { className:"flex flex-col sm:flex-row gap-2 mb-3" }, React.createElement("input", { value:clubLookupDni, inputMode:"tel", onChange:e=>{setClubLookupDni(e.target.value);setClubLookupResult(null);}, placeholder:"351 1234567", className:"customer-compact-input flex-1" }), React.createElement("button", { type:"button", onClick:lookupClubPoints, disabled:clubLookupLoading, className:"club-points-btn sm:min-w-[130px]" }, clubLookupLoading?"Ingresando...":"Ingresar")),
                        React.createElement("details", { className:"bg-black/20 rounded-xl p-3" }, React.createElement("summary", { className:"text-xs font-black cursor-pointer" }, "¿Primera vez? Crear cuenta"), React.createElement("div", { className:"grid gap-2 mt-3" }, React.createElement("input", { value:clubRegisterName,onChange:e=>setClubRegisterName(e.target.value),placeholder:"Nombre",className:"customer-compact-input" }),React.createElement("input", { value:clubRegisterSurname,onChange:e=>setClubRegisterSurname(e.target.value),placeholder:"Apellido",className:"customer-compact-input" }),React.createElement("button", { type:"button",onClick:registerClubUser,className:"club-points-btn" },"Registrarme con este celular"))))
                    : React.createElement(React.Fragment,null,
                        React.createElement("div", { className:"flex items-center justify-between gap-2" }, React.createElement("div",null,React.createElement("b", { className:"block text-sm" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || 'Mi cuenta'),React.createElement("span", { className:"text-[10px] text-neutral-400" },clubSessionPhone)),React.createElement("button", { type:"button",onClick:logoutClub,className:"text-[10px] text-neutral-400" },"Salir")),
                        React.createElement("button", { type:"button",onClick:()=>{setClubLookupDni(clubSessionPhone);lookupClubPoints();},className:"club-points-btn w-full mt-3" },"Actualizar puntos")),
                    clubLookupResult && React.createElement("div", { className:"grid grid-cols-3 gap-2 mt-3 text-center" }, React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-orange-300" }, clubLookupResult.points), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "disponibles")), React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.earnedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "ganados")), React.createElement("div", { className:"bg-black/25 rounded-xl p-2" }, React.createElement("b", { className:"block text-xl text-white" }, clubLookupResult.redeemedPoints), React.createElement("span", { className:"text-[9px] text-neutral-400" }, "canjeados"))),
                    clubMessage && React.createElement("p", { className:"text-[11px] text-orange-100/85 mt-2 leading-relaxed" }, clubMessage)),'''
once(old,new,'club modal')

# Header rule copy references phone
s=s.replace('"Sumás 1 punto por cada $5.000 acumulados. Si una compra individual llega a $10.000 o más, suma 1 punto extra: una compra de $10.000 genera 3 puntos."','"Tu cuenta se identifica por celular. Sumás 1 punto por cada $5.000 acumulados y una compra individual de $10.000 o más suma 1 punto extra."')

p.write_text(s,encoding='utf-8')
print('v79 patched')
