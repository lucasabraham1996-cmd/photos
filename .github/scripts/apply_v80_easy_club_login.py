from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v79-phone-club-accounts','v80-easy-club-login')

once('''    const [clubRegisterName, setClubRegisterName] = useState("");
    const [clubRegisterSurname, setClubRegisterSurname] = useState("");''','''    const [clubRegisterName, setClubRegisterName] = useState("");
    const [clubRegisterSurname, setClubRegisterSurname] = useState("");
    const [clubRegisterOpen, setClubRegisterOpen] = useState(false);''','register state')

start=s.index('    async function lookupClubPoints() {')
end=s.index('    async function registerClubUser() {',start)
new='''    async function lookupClubPoints(rawPhone = '') {
        const phone = normalizeClubPhone(rawPhone || clubLookupDni);
        if (!phone || phone.length < 10) {
            setClubMessage('Escribí un celular válido. Por ejemplo: 351 5580770.');
            setClubRegisterOpen(false);
            return;
        }
        setClubLookupDni(phone);
        setClubLookupLoading(true);
        setClubMessage('Buscando tu cuenta...');
        setClubLookupResult(null);
        try {
            let users = clubUsers;
            let profile = users.find(u => normalizeClubPhone(u.phone) === phone) || null;
            if (!profile) {
                try {
                    const fresh = await loadSharedAdminState();
                    if (fresh && Array.isArray(fresh.clubUsers)) {
                        users = fresh.clubUsers;
                        setClubUsers(fresh.clubUsers);
                        profile = fresh.clubUsers.find(u => normalizeClubPhone(u.phone) === phone) || null;
                    }
                } catch(e) { console.warn('No se pudo refrescar la lista de usuarios del Club.', e); }
            }
            if (!profile) {
                setClubRegisterOpen(true);
                setClubMessage('Es tu primera vez. Completá nombre y apellido y tu cuenta queda lista.');
                return;
            }
            const list = await loadClubOrdersForPhone(phone);
            const account = clubAccountFromOrders(list, phone);
            setClubLookupResult(account);
            setClubSessionPhone(phone);
            setClubRegisterOpen(false);
            try { localStorage.setItem('LA_CLUB_PHONE', phone); } catch(e) {}
            setClubMessage(account.points > 0 ? `¡Hola, ${profile.name || ''}! Tenés ${account.points} puntos disponibles.` : `¡Hola, ${profile.name || ''}! Tu cuenta está lista. Todavía no tenés puntos disponibles.`);
        } catch(e) {
            console.error('No se pudo ingresar al Club.', e);
            setClubMessage('No pudimos ingresar ahora. Revisá tu conexión y tocá Continuar nuevamente.');
        } finally {
            setClubLookupLoading(false);
        }
    }
'''
s=s[:start]+new+s[end:]

start=s.index('    async function registerClubUser() {')
end=s.index('    const logoutClub=',start)
new='''    async function registerClubUser() {
        const phone = normalizeClubPhone(clubLookupDni);
        const name = String(clubRegisterName || '').trim();
        const surname = String(clubRegisterSurname || '').trim();
        if (!phone || phone.length < 10) { setClubMessage('Escribí un celular válido.'); return; }
        if (!name) { setClubMessage('Escribí tu nombre.'); return; }
        if (!surname) { setClubMessage('Escribí tu apellido.'); return; }
        setClubLookupLoading(true);
        setClubMessage('Creando tu cuenta...');
        try {
            const user = { phone, name, surname, createdAt:new Date().toISOString() };
            let baseUsers = clubUsers;
            try {
                const fresh = await loadSharedAdminState();
                if (fresh && Array.isArray(fresh.clubUsers)) baseUsers = fresh.clubUsers;
            } catch(e) {}
            const nextUsers = [user, ...baseUsers.filter(u => normalizeClubPhone(u.phone) !== phone)];
            setClubUsers(nextUsers);
            await saveSharedAdminState({ clubUsers: nextUsers });
            setClubSessionPhone(phone);
            setClubRegisterOpen(false);
            try { localStorage.setItem('LA_CLUB_PHONE', phone); } catch(e) {}
            const list = await loadClubOrdersForPhone(phone);
            setClubLookupResult(clubAccountFromOrders(list, phone));
            setClubMessage(`¡Listo, ${name}! Ya estás dentro del Club.`);
        } catch(e) {
            console.error('No se pudo crear la cuenta del Club.', e);
            setClubMessage('No pudimos crear la cuenta. Revisá tu conexión y probá de nuevo.');
        } finally {
            setClubLookupLoading(false);
        }
    }
'''
s=s[:start]+new+s[end:]

old_ui='''                    !clubSessionPhone ? React.createElement(React.Fragment,null,
                        React.createElement("p", { className:"text-xs font-black text-orange-100 mb-2" }, "Ingresá solamente con tu celular"),
                        React.createElement("div", { className:"flex flex-col sm:flex-row gap-2 mb-3" }, React.createElement("input", { value:clubLookupDni, inputMode:"tel", onChange:e=>{setClubLookupDni(e.target.value);setClubLookupResult(null);}, placeholder:"351 1234567", className:"customer-compact-input flex-1" }), React.createElement("button", { type:"button", onClick:lookupClubPoints, disabled:clubLookupLoading, className:"club-points-btn sm:min-w-[130px]" }, clubLookupLoading?"Ingresando...":"Ingresar")),
                        React.createElement("details", { className:"bg-black/20 rounded-xl p-3" }, React.createElement("summary", { className:"text-xs font-black cursor-pointer" }, "¿Primera vez? Crear cuenta"), React.createElement("div", { className:"grid gap-2 mt-3" }, React.createElement("input", { value:clubRegisterName,onChange:e=>setClubRegisterName(e.target.value),placeholder:"Nombre",className:"customer-compact-input" }),React.createElement("input", { value:clubRegisterSurname,onChange:e=>setClubRegisterSurname(e.target.value),placeholder:"Apellido",className:"customer-compact-input" }),React.createElement("button", { type:"button",onClick:registerClubUser,className:"club-points-btn" },"Registrarme con este celular"))))
                    : React.createElement(React.Fragment,null,
                        React.createElement("div", { className:"flex items-center justify-between gap-2" }, React.createElement("div",null,React.createElement("b", { className:"block text-sm" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || 'Mi cuenta'),React.createElement("span", { className:"text-[10px] text-neutral-400" },clubSessionPhone)),React.createElement("button", { type:"button",onClick:logoutClub,className:"text-[10px] text-neutral-400" },"Salir")),
                        React.createElement("button", { type:"button",onClick:()=>{setClubLookupDni(clubSessionPhone);lookupClubPoints();},className:"club-points-btn w-full mt-3" },"Actualizar puntos")),'''
new_ui='''                    !clubSessionPhone ? React.createElement(React.Fragment,null,
                        React.createElement("div", { className:"text-center mb-4" },
                            React.createElement("div", { className:"w-14 h-14 mx-auto rounded-full bg-orange-500/15 border border-orange-400/25 flex items-center justify-center mb-3" }, React.createElement("i", { className:"fas fa-mobile-screen-button text-orange-300 text-xl" })),
                            React.createElement("h3", { className:"text-xl font-black text-white" }, "Entrá con tu celular"),
                            React.createElement("p", { className:"text-xs text-neutral-400 mt-1 leading-relaxed" }, "No necesitás contraseña ni DNI. Escribí tu número y tocá Continuar.")),
                        React.createElement("input", { value:clubLookupDni, inputMode:"tel", autoComplete:"tel", onChange:e=>{setClubLookupDni(e.target.value);setClubLookupResult(null);setClubRegisterOpen(false);setClubMessage('');}, onKeyDown:e=>{if(e.key==='Enter'){e.preventDefault();lookupClubPoints(e.currentTarget.value);}}, placeholder:"Tu celular, ej. 351 5580770", className:"customer-compact-input w-full text-lg py-4 mb-2" }),
                        React.createElement("p", { className:"text-[10px] text-neutral-500 mb-3 px-1" }, "Podés escribirlo como 351…, 0351…, 15…, +54 o +54 9. La app lo unifica automáticamente."),
                        React.createElement("button", { type:"button", onClick:()=>lookupClubPoints(clubLookupDni), disabled:clubLookupLoading, className:"club-points-btn w-full py-4 text-base" }, clubLookupLoading?React.createElement(React.Fragment,null,React.createElement("i",{className:"fas fa-circle-notch fa-spin mr-2"}),"Buscando..."):React.createElement(React.Fragment,null,"Continuar",React.createElement("i",{className:"fas fa-arrow-right ml-2"}))),
                        clubRegisterOpen && React.createElement("div", { className:"mt-4 bg-black/25 border border-orange-400/20 rounded-2xl p-4" },
                            React.createElement("p", { className:"font-black text-white text-base" }, "Creá tu cuenta"),
                            React.createElement("p", { className:"text-xs text-neutral-400 mt-1 mb-3" }, "Sólo te lo pedimos esta primera vez."),
                            React.createElement("div", { className:"grid gap-2" },
                                React.createElement("input", { value:clubRegisterName,onChange:e=>setClubRegisterName(e.target.value),placeholder:"Nombre",autoComplete:"given-name",className:"customer-compact-input py-4" }),
                                React.createElement("input", { value:clubRegisterSurname,onChange:e=>setClubRegisterSurname(e.target.value),placeholder:"Apellido",autoComplete:"family-name",className:"customer-compact-input py-4" }),
                                React.createElement("button", { type:"button",onClick:registerClubUser,disabled:clubLookupLoading,className:"club-points-btn w-full py-4 text-base" },clubLookupLoading?"Creando cuenta...":"Crear cuenta y continuar"))))
                    : React.createElement(React.Fragment,null,
                        React.createElement("div", { className:"rounded-2xl bg-black/25 border border-orange-400/15 p-4" },
                            React.createElement("div", { className:"flex items-center justify-between gap-3" },
                                React.createElement("div",null,React.createElement("p", { className:"text-[10px] uppercase tracking-widest text-orange-300 font-black" },"Tu cuenta"),React.createElement("b", { className:"block text-lg text-white mt-1" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || 'Mi cuenta'),React.createElement("span", { className:"text-xs text-neutral-400" },clubSessionPhone)),
                                React.createElement("button", { type:"button",onClick:logoutClub,className:"bg-neutral-800 px-3 py-2 rounded-xl text-xs font-bold" },"Cambiar cuenta")),
                            React.createElement("button", { type:"button",onClick:()=>lookupClubPoints(clubSessionPhone),disabled:clubLookupLoading,className:"club-points-btn w-full mt-3 py-3" },clubLookupLoading?"Actualizando...":"Actualizar mis puntos"))),'''
if old_ui not in s: raise SystemExit('club login UI marker not found')
s=s.replace(old_ui,new_ui,1)

s=s.replace('''    const openClub = () => {
        setClubModalOpen(true);''','''    const openClub = () => {
        setClubPointsOpen(true);
        setClubModalOpen(true);''',1)

p.write_text(s,encoding='utf-8')
print('v80 patched')
