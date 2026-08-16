from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v82-club-entry-flow','v83-club-welcome')

once("setClubMessage('Buscando tu cuenta...');","setClubMessage('Ingresando a tu cuenta...');",'login status copy')

once('''clubLookupLoading?React.createElement(React.Fragment,null,React.createElement("i",{className:"fas fa-circle-notch fa-spin mr-2"}),"Buscando..."):React.createElement(React.Fragment,null,"Continuar",React.createElement("i",{className:"fas fa-arrow-right ml-2"}))''','''clubLookupLoading?React.createElement(React.Fragment,null,React.createElement("i",{className:"fas fa-circle-notch fa-spin mr-2"}),"Ingresando..."):React.createElement(React.Fragment,null,"Continuar",React.createElement("i",{className:"fas fa-arrow-right ml-2"}))''','login button copy')

old='''            const firstName = String((profile && profile.name) || account.name || '').trim().split(' ')[0] || '';
            setClubMessage(account.points > 0 ? `¡Hola${firstName ? ', '+firstName : ''}! Tenés ${account.points} puntos disponibles.` : `¡Hola${firstName ? ', '+firstName : ''}! Tu cuenta está lista. Todavía no tenés puntos disponibles.`);'''
new='''            const fullName = String(profile ? `${profile.name || ''} ${profile.surname || ''}`.trim() : (account.name || '')).trim() || 'Cliente';
            setClubMessage(account.points > 0 ? `¡Bienvenido/a, ${fullName}! Tenés ${account.points} puntos disponibles.` : `¡Bienvenido/a, ${fullName}! Tu cuenta está lista. Todavía no tenés puntos disponibles.`);
            try { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); } catch(e) {}
            setTimeout(() => {
                try {
                    const shell = document.querySelector('.club-modal-shell');
                    if (shell && shell.scrollIntoView) shell.scrollIntoView({ behavior:'smooth', block:'start' });
                    const scrollable = shell && shell.closest('[class*="overflow-y-auto"], [class*="overflow-auto"]');
                    if (scrollable) scrollable.scrollTop = 0;
                } catch(e) {}
            }, 80);'''
once(old,new,'welcome message and scroll reset')

old_label='''React.createElement("div",null,React.createElement("p", { className:"text-[10px] uppercase tracking-widest text-orange-300 font-black" },"Tu cuenta"),React.createElement("b", { className:"block text-lg text-white mt-1" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || (clubLookupResult && clubLookupResult.name) || 'Mi cuenta'),React.createElement("span", { className:"text-xs text-neutral-400" },clubSessionPhone))'''
new_label='''React.createElement("div",null,React.createElement("p", { className:"text-[10px] uppercase tracking-widest text-orange-300 font-black" },"Bienvenido/a"),React.createElement("b", { className:"block text-xl text-white mt-1" }, (clubProfileForPhone(clubSessionPhone) && `${clubProfileForPhone(clubSessionPhone).name||''} ${clubProfileForPhone(clubSessionPhone).surname||''}`.trim()) || (clubLookupResult && clubLookupResult.name) || 'Mi cuenta'),React.createElement("span", { className:"text-xs text-neutral-400" },clubSessionPhone))'''
once(old_label,new_label,'logged account welcome label')

p.write_text(s,encoding='utf-8')
print('v83 patched')
