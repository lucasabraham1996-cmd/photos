from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v88-admin-gallery-navigation','v89-club-blue-login')

# Existing Club sessions should open directly as logged in, not collapse the account again.
once("""    const openClub = () => {
        setClubPointsOpen(false);
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (location.hash !== '#/club') location.hash = '#/club';
    };""","""    const openClub = () => {
        setClubPointsOpen(Boolean(clubSessionPhone));
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (location.hash !== '#/club') location.hash = '#/club';
    };""",'openClub logged state')

once("""    useEffect(() => {
        if (route !== '#/club') return;
        setClubPointsOpen(false);
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (clubSessionPhone && sharedReady) lookupClubPoints(clubSessionPhone);
    }, [route, clubSessionPhone, sharedReady]);""","""    useEffect(() => {
        if (route !== '#/club') return;
        setClubPointsOpen(Boolean(clubSessionPhone));
        setClubRegisterOpen(false);
        setClubModalOpen(true);
        if (clubSessionPhone && sharedReady) lookupClubPoints(clubSessionPhone);
    }, [route, clubSessionPhone, sharedReady]);""",'club route logged state')

# Remove technical phone-format helper.
once('''                        React.createElement("p", { className:"text-[10px] text-neutral-500 mb-3 px-1" }, "Podés escribirlo como 351…, 0351…, 15…, +54 o +54 9. La app lo unifica automáticamente."),\n''','', 'phone helper copy')

# Share: full share is Admin-only. Customers only get a compact copy-URL action.
old='''                React.createElement("button", { type:"button", onClick:shareClubLink, className:"club-share-btn" }, React.createElement("i", { className:"fas fa-share-nodes" }), "Compartir link del Club"),'''
new='''                admin ? React.createElement("button", { type:"button", onClick:shareClubLink, className:"club-share-btn" }, React.createElement("i", { className:"fas fa-share-nodes" }), "Compartir link del Club") : React.createElement("div", { className:"flex justify-end mb-2" }, React.createElement("button", { type:"button", onClick:async()=>{ const url=getClubUrl(); try { await navigator.clipboard.writeText(url); setClubMessage('Link copiado.'); } catch(e) { try { prompt('Copiá este link:',url); } catch(_e) {} } }, className:"club-copy-url-btn", title:"Copiar link del Club" }, React.createElement("i", { className:"fas fa-link" }), "Copiar URL")),'''
once(old,new,'admin share customer copy')

# Login toggle text should acknowledge active session; logged users never see another login prompt.
old='''                React.createElement("button", { type:"button", onClick:() => { setClubPointsOpen(v => !v); setClubRegisterOpen(false); }, className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-user" }), clubPointsOpen ? "Ocultar mi cuenta" : "Ingresar / registrarme"),'''
new='''                React.createElement("button", { type:"button", onClick:() => { setClubPointsOpen(v => !v); setClubRegisterOpen(false); }, className:"club-points-btn w-full mb-3" }, React.createElement("i", { className:"fas fa-user" }), clubSessionPhone ? (clubPointsOpen ? "Ocultar mi cuenta" : "Ver mi cuenta") : (clubPointsOpen ? "Ocultar acceso" : "Ingresar / registrarme")),'''
once(old,new,'login toggle state')

# Admin PIN panel gets a close X that safely returns to gallery and removes admin query.
old='''        return React.createElement("div", { className: "min-h-screen flex items-center justify-center p-4" },
            React.createElement("form", { onSubmit: e => { e.preventDefault(); pin === ADMIN_PIN ? setAdmin(true) : alert('PIN incorrecto'); }, className: "bg-neutral-900 border border-neutral-800 p-7 rounded-3xl w-full max-w-sm" },
                React.createElement("h1", { className: "text-2xl font-bold mb-2" }, "Acceso admin"),'''
new='''        return React.createElement("div", { className: "min-h-screen flex items-center justify-center p-4" },
            React.createElement("form", { onSubmit: e => { e.preventDefault(); pin === ADMIN_PIN ? setAdmin(true) : alert('PIN incorrecto'); }, className: "relative bg-neutral-900 border border-neutral-800 p-7 rounded-3xl w-full max-w-sm" },
                React.createElement("button", { type:"button", onClick:goToGallery, className:"absolute top-4 right-4 w-9 h-9 rounded-full bg-black/40 border border-white/10 text-neutral-400 hover:text-white flex items-center justify-center", title:"Cerrar", "aria-label":"Cerrar acceso administrador" }, React.createElement("i", { className:"fas fa-xmark" })),
                React.createElement("h1", { className: "text-2xl font-bold mb-2 pr-10" }, "Acceso admin"),'''
once(old,new,'admin login close')

# Blue/cyan Club visual override. Keep existing structure, override orange treatment comprehensively.
style='''\n<style id="v89-club-blue-login">\n.la-insta-btn.la-club-header{background:linear-gradient(135deg,#075985 0%,#0284c7 48%,#38bdf8 100%)!important;border-color:rgba(125,211,252,.38)!important;color:#fff!important;box-shadow:0 8px 24px rgba(14,165,233,.22),inset 0 1px 0 rgba(255,255,255,.24)!important}\n.club-modal-shell{border-color:rgba(56,189,248,.24)!important;background:linear-gradient(160deg,rgba(8,47,73,.28),rgba(7,12,22,.98) 42%,rgba(2,6,23,.99))!important}\n.club-modal-header p.text-orange-300,.club-account-card .text-orange-300,.club-account-card .text-orange-200{color:#7dd3fc!important}\n.club-account-card{border-color:rgba(56,189,248,.25)!important;background:linear-gradient(145deg,rgba(8,47,73,.30),rgba(5,12,24,.92))!important}\n.club-points-btn{background:linear-gradient(135deg,#0369a1 0%,#0ea5e9 48%,#67e8f9 100%)!important;color:#fff!important;border-color:rgba(125,211,252,.35)!important;box-shadow:0 10px 28px rgba(14,165,233,.18),inset 0 1px 0 rgba(255,255,255,.25)!important}\n.club-account-card .bg-orange-500\\/15{background:rgba(14,165,233,.14)!important}.club-account-card .border-orange-400\\/25,.club-account-card .border-orange-400\\/30,.club-account-card .border-orange-400\\/20{border-color:rgba(125,211,252,.28)!important}.club-account-card .text-orange-300,.club-account-card .text-orange-100{color:#bae6fd!important}.club-account-card .bg-orange-500\\/10{background:rgba(14,165,233,.10)!important}\n.club-copy-url-btn{display:inline-flex;align-items:center;gap:5px;border:1px solid rgba(125,211,252,.16);background:rgba(14,165,233,.07);color:#94a3b8;border-radius:999px;padding:6px 9px;font-size:9px;font-weight:800;line-height:1;opacity:.78}.club-copy-url-btn:active{transform:scale(.97);background:rgba(14,165,233,.14);color:#e0f2fe}\n.club-share-btn{border-color:rgba(125,211,252,.18)!important;background:rgba(14,165,233,.08)!important}\n@media(max-width:640px){.club-copy-url-btn{font-size:9px;padding:6px 8px}}\n</style>\n'''
if '</head>' not in s: raise SystemExit('missing head')
s=s.replace('</head>',style+'</head>',1)

p.write_text(s,encoding='utf-8')
print('v89 patched')
