from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v80-easy-club-login','v81-history-backed-club-account')

old_effect='''    useEffect(() => {
        if (route === '#/club') setClubModalOpen(true);
    }, [route]);'''
new_effect='''    useEffect(() => {
        if (route !== '#/club') return;
        setClubPointsOpen(true);
        setClubModalOpen(true);
        if (clubSessionPhone && sharedReady) lookupClubPoints(clubSessionPhone);
    }, [route, clubSessionPhone, sharedReady]);'''
once(old_effect,new_effect,'club route effect')

start=s.index('    async function lookupClubPoints(rawPhone = \'\') {')
end=s.index('    async function registerClubUser() {',start)
new_lookup='''    async function lookupClubPoints(rawPhone = '') {
        const phone = normalizeClubPhone(rawPhone || clubLookupDni);
        if (!phone || phone.length < 10) {
            setClubMessage('Escribí un celular válido. Por ejemplo: 351 5580770.');
            setClubRegisterOpen(false);
            return;
        }
        setClubLookupDni(phone);
        setClubLookupLoading(true);
        setClubMessage('Buscando tu cuenta...');
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

            const list = await loadClubOrdersForPhone(phone);
            const account = clubAccountFromOrders(list, phone);
            const matchingHistory = mergeOrders(list).filter(o => {
                if (o.type === 'club_points_transfer') return [normalizeClubPhone(o.fromPhone), normalizeClubPhone(o.toPhone)].includes(phone);
                return normalizeClubPhone(o.phone || o.celular || o.customerPhone) === phone;
            });
            const hasHistory = matchingHistory.length > 0;

            if (!profile && hasHistory) {
                const historyName = String(account.name || (matchingHistory.find(o => String(o.customerName || o.nombreApellido || '').trim()) || {}).customerName || '').trim().replace(/\\s{2,}/g,' ');
                const parts = historyName.split(' ').filter(Boolean);
                const inferred = {
                    phone,
                    name: parts[0] || 'Cliente',
                    surname: parts.slice(1).join(' '),
                    createdAt:new Date().toISOString(),
                    migratedFromHistory:true
                };
                profile = inferred;
                const nextUsers = [inferred, ...users.filter(u => normalizeClubPhone(u.phone) !== phone)];
                setClubUsers(nextUsers);
                try { await saveSharedAdminState({ clubUsers:nextUsers }); } catch(e) { console.warn('No se pudo guardar el perfil recuperado desde compras.', e); }
            }

            if (!profile && !hasHistory) {
                setClubLookupResult(null);
                setClubRegisterOpen(true);
                setClubSessionPhone('');
                try { localStorage.removeItem('LA_CLUB_PHONE'); } catch(e) {}
                setClubMessage('Es tu primera vez. Completá nombre y apellido y tu cuenta queda lista.');
                return;
            }

            setClubLookupResult(account);
            setClubSessionPhone(phone);
            setClubRegisterOpen(false);
            try { localStorage.setItem('LA_CLUB_PHONE', phone); } catch(e) {}
            const firstName = String((profile && profile.name) || account.name || '').trim().split(' ')[0] || '';
            setClubMessage(account.points > 0 ? `¡Hola${firstName ? ', '+firstName : ''}! Tenés ${account.points} puntos disponibles.` : `¡Hola${firstName ? ', '+firstName : ''}! Tu cuenta está lista. Todavía no tenés puntos disponibles.`);
        } catch(e) {
            console.error('No se pudo ingresar al Club.', e);
            setClubMessage('No pudimos ingresar ahora. Revisá tu conexión y tocá Continuar nuevamente.');
        } finally {
            setClubLookupLoading(false);
        }
    }
'''
s=s[:start]+new_lookup+s[end:]

old_name='''React.createElement("b", { className:"block text-lg text-white mt-1" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || 'Mi cuenta')'''
new_name='''React.createElement("b", { className:"block text-lg text-white mt-1" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || (clubLookupResult && clubLookupResult.name) || 'Mi cuenta')'''
once(old_name,new_name,'account name fallback')

p.write_text(s,encoding='utf-8')
print('v81 patched')
