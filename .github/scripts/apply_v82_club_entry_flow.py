from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v81-history-backed-club-account','v82-club-entry-flow')

once('''    const openClub = () => {
        setClubPointsOpen(true);
        setClubModalOpen(true);
        if (location.hash !== '#/club') location.hash = '#/club';
    };''','''    const openClub = () => {
        setClubPointsOpen(false);
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (location.hash !== '#/club') location.hash = '#/club';
    };''','openClub collapsed')

once('''    useEffect(() => {
        if (route !== '#/club') return;
        setClubPointsOpen(true);
        setClubModalOpen(true);
        if (clubSessionPhone && sharedReady) lookupClubPoints(clubSessionPhone);
    }, [route, clubSessionPhone, sharedReady]);''','''    useEffect(() => {
        if (route !== '#/club') return;
        setClubPointsOpen(false);
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (clubSessionPhone && sharedReady) lookupClubPoints(clubSessionPhone);
    }, [route, clubSessionPhone, sharedReady]);''','route Club collapsed')

once('''                React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-user" }), clubPointsOpen ? "Ocultar mi cuenta" : (clubSessionPhone ? "Mi cuenta y puntos" : "Ingresar / registrarme")),''','''                React.createElement("button", { type:"button", onClick:() => { setClubPointsOpen(v => !v); setClubRegisterOpen(false); }, className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-user" }), clubPointsOpen ? "Ocultar mi cuenta" : "Ingresar / registrarme"),''','main Club button label')

old='''                        React.createElement("button", { type:"button", onClick:()=>lookupClubPoints(clubLookupDni), disabled:clubLookupLoading, className:"club-points-btn w-full py-4 text-base" }, clubLookupLoading?React.createElement(React.Fragment,null,React.createElement("i",{className:"fas fa-circle-notch fa-spin mr-2"}),"Buscando..."):React.createElement(React.Fragment,null,"Continuar",React.createElement("i",{className:"fas fa-arrow-right ml-2"}))),
                        clubRegisterOpen && React.createElement("div", { className:"mt-4 bg-black/25 border border-orange-400/20 rounded-2xl p-4" },'''
new='''                        React.createElement("button", { type:"button", onClick:()=>lookupClubPoints(clubLookupDni), disabled:clubLookupLoading, className:"club-points-btn w-full py-4 text-base" }, clubLookupLoading?React.createElement(React.Fragment,null,React.createElement("i",{className:"fas fa-circle-notch fa-spin mr-2"}),"Buscando..."):React.createElement(React.Fragment,null,"Continuar",React.createElement("i",{className:"fas fa-arrow-right ml-2"}))),
                        !clubRegisterOpen && React.createElement("button", { type:"button", onClick:()=>{setClubRegisterOpen(true);setClubMessage('Completá tu nombre y apellido para crear tu cuenta.');}, className:"w-full mt-3 py-3.5 rounded-2xl border border-orange-400/30 bg-orange-500/10 text-orange-100 font-black text-sm" }, React.createElement("i",{className:"fas fa-user-plus mr-2"}), "¿Es tu primera vez? Registrarme"),
                        clubRegisterOpen && React.createElement("div", { className:"mt-4 bg-black/25 border border-orange-400/20 rounded-2xl p-4" },'''
once(old,new,'visible first-time register button')

old2='''                                React.createElement("input", { value:clubRegisterSurname,onChange:e=>setClubRegisterSurname(e.target.value),placeholder:"Apellido",autoComplete:"family-name",className:"customer-compact-input py-4" }),
                                React.createElement("button", { type:"button",onClick:registerClubUser,disabled:clubLookupLoading,className:"club-points-btn w-full py-4 text-base" },clubLookupLoading?"Creando cuenta...":"Crear cuenta y continuar"))))'''
new2='''                                React.createElement("input", { value:clubRegisterSurname,onChange:e=>setClubRegisterSurname(e.target.value),placeholder:"Apellido",autoComplete:"family-name",className:"customer-compact-input py-4" }),
                                React.createElement("button", { type:"button",onClick:registerClubUser,disabled:clubLookupLoading,className:"club-points-btn w-full py-4 text-base" },clubLookupLoading?"Creando cuenta...":"Crear cuenta y continuar"),
                                React.createElement("button", { type:"button",onClick:()=>{setClubRegisterOpen(false);setClubMessage('');},className:"w-full py-3 rounded-xl text-xs font-bold text-neutral-400" },"Ya tengo cuenta · volver"))))'''
once(old2,new2,'register back button')

p.write_text(s,encoding='utf-8')
print('v82 patched')
