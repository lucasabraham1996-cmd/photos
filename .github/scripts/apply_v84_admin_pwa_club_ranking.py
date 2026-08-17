from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v83-club-welcome','v84-admin-pwa-club-ranking')

# Admin PIN
once('const ADMIN_PIN = "1234";','const ADMIN_PIN = "160218";','admin pin')

# iPhone/PWA manifest: preserve admin as install start destination using query param + hash.
once('''        const manifest = {
            name: BRAND,
            short_name: 'Lucas Abraham',
            start_url: `${baseScope}#/galeria`,''','''        const launchAdmin = location.hash === '#/admin' || new URLSearchParams(location.search).get('admin') === '1';
        const manifest = {
            name: launchAdmin ? `${BRAND} · Admin` : BRAND,
            short_name: launchAdmin ? 'LA Admin' : 'Lucas Abraham',
            start_url: launchAdmin ? `${baseScope}?admin=1#/admin` : `${baseScope}#/galeria`,''','manifest admin start url')

once('''    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;
        const target = route === '#/admin' ? '#/admin' : '#/galeria';
        try { localStorage.setItem('LA_INSTALL_START_ROUTE', target); } catch(e) {}
        return `${base || (location.href || '').split('#')[0]}${target}`;
    };''','''    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;
        const adminInstall = route === '#/admin';
        const target = adminInstall ? '#/admin' : '#/galeria';
        try { localStorage.setItem('LA_INSTALL_START_ROUTE', target); } catch(e) {}
        return adminInstall ? `${base || (location.href || '').split('#')[0]}?admin=1#/admin` : `${base || (location.href || '').split('#')[0]}#/galeria`;
    };''','install url admin query')

old_route='''    useEffect(() => { const h = () => { let hash = location.hash || "#/galeria"; try { const standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; const saved = localStorage.getItem('LA_INSTALL_START_ROUTE'); if (standalone && saved === '#/admin' && (!location.hash || location.hash === '#/galeria')) { location.hash = '#/admin'; hash = '#/admin'; } if (hash === '#/admin') localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);'''
new_route='''    useEffect(() => { const h = () => { let hash = location.hash || "#/galeria"; try { const standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; const saved = localStorage.getItem('LA_INSTALL_START_ROUTE'); const adminQuery = new URLSearchParams(location.search).get('admin') === '1'; if (adminQuery || (standalone && saved === '#/admin' && (!location.hash || location.hash === '#/galeria'))) { if (hash !== '#/admin') location.hash = '#/admin'; hash = '#/admin'; } if (hash === '#/admin') localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);'''
once(old_route,new_route,'route admin query')

# Club topbar button logo.
once('''                    React.createElement("button", { onClick: openClub, className: "la-insta-btn la-club-header", title: "Club de beneficios" },
                        React.createElement("i", { className: "fas fa-gift" }),
                        React.createElement("span", null, "Club")),''','''                    React.createElement("button", { onClick: openClub, className: "la-insta-btn la-club-header", title: "Club de beneficios" },
                        React.createElement("img", { src:"https://i.postimg.cc/W3SqHj91/LA-Marca-de-agua-copia.png", className:"club-header-logo", alt:"Club lucasabraham.ph" }),
                        React.createElement("span", null, "Club")),''','club header logo')

# Append v84 styles before closing head-ish style marker.
style='''\n<style id="v84-admin-pwa-club-ranking">\n.la-insta-btn.la-club-header{background:linear-gradient(135deg,#ff7a18 0%,#ff4d67 48%,#8b5cf6 100%)!important;border:1px solid rgba(255,255,255,.24)!important;color:#fff!important;box-shadow:0 8px 24px rgba(255,77,103,.22),inset 0 1px 0 rgba(255,255,255,.24)!important}\n.la-insta-btn.la-club-header:hover{filter:brightness(1.08);transform:translateY(-1px)}\n.club-header-logo{width:22px;height:22px;object-fit:contain;display:block;border-radius:50%;background:rgba(0,0,0,.22);padding:1px;box-shadow:0 2px 8px rgba(0,0,0,.26)}\n.club-ranking-card{background:linear-gradient(145deg,rgba(16,16,20,.98),rgba(4,4,7,.99));border:1px solid rgba(255,255,255,.09);border-radius:18px;padding:13px;display:grid;grid-template-columns:42px 1fr auto;gap:11px;align-items:center;box-shadow:0 10px 28px rgba(0,0,0,.20)}\n.club-ranking-card.top-1{border-color:rgba(250,204,21,.34);background:linear-gradient(145deg,rgba(72,53,5,.36),rgba(6,6,8,.98))}.club-ranking-card.top-2{border-color:rgba(203,213,225,.28)}.club-ranking-card.top-3{border-color:rgba(251,146,60,.30)}\n.club-ranking-pos{width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-weight:1000;font-size:15px;background:rgba(255,255,255,.07);color:#fff}.top-1 .club-ranking-pos{background:rgba(250,204,21,.15);color:#fde047}.top-2 .club-ranking-pos{background:rgba(203,213,225,.12);color:#e2e8f0}.top-3 .club-ranking-pos{background:rgba(251,146,60,.13);color:#fdba74}\n.club-ranking-points{font-size:25px;line-height:1;font-weight:1000;color:#fb923c;text-align:right}.club-ranking-points small{display:block;font-size:9px;color:#737373;margin-top:4px;text-transform:uppercase;letter-spacing:.08em}\n.admin-secret-footer{display:flex;justify-content:center;margin:30px auto 8px;opacity:.11;transition:opacity .2s}.admin-secret-footer:hover,.admin-secret-footer:focus-within{opacity:.4}.admin-secret-footer button{border:0;background:transparent;color:#a3a3a3;font-size:9px;padding:8px 16px;letter-spacing:.16em;text-transform:uppercase}\n@media(max-width:640px){.club-ranking-card{grid-template-columns:36px 1fr auto;padding:11px;gap:9px}.club-ranking-pos{width:36px;height:36px;border-radius:12px}.club-ranking-points{font-size:21px}.club-header-logo{width:20px;height:20px}}\n</style>\n'''
marker='</head>'
if marker not in s: raise SystemExit('head close missing')
s=s.replace(marker,style+marker,1)

# Ranking admin button/card visual, still collapsed by default.
once('''                React.createElement("button", { type:"button", onClick:()=>setPointsAdminOpen(v=>!v), className:"w-full mb-3 bg-neutral-800 rounded-xl px-4 py-3 text-sm font-black flex items-center justify-between" }, React.createElement("span", null, React.createElement("i", { className:"fas fa-users mr-2" }), "Usuarios y puntos"), React.createElement("i", { className:`fas ${pointsAdminOpen?'fa-chevron-up':'fa-chevron-down'}` })),
                pointsAdminOpen && React.createElement("div", { className:"grid gap-2 mb-4" },
                    customerDniStats.length===0 && React.createElement("p", { className:"text-sm text-neutral-500" }, "Todavía no hay usuarios con teléfono registrado."),
                    customerDniStats.map(r=>React.createElement("div", { key:r.phone, className:"bg-neutral-950 border border-neutral-800 rounded-2xl p-3 grid grid-cols-[1fr,auto] gap-3 items-center" },
                        React.createElement("div", { className:"min-w-0" }, React.createElement("b", { className:"block text-sm truncate" }, r.name||'Sin nombre'), React.createElement("span", { className:"block text-xs text-neutral-400" }, r.phone), React.createElement("span", { className:"block text-[10px] text-neutral-500 mt-1" }, `${r.purchases} compras · ${formatPrice(r.spent)} · ${r.redeemedPoints} canjeados`)),
                        React.createElement("div", { className:"text-right" }, React.createElement("b", { className:"block text-2xl text-orange-300" }, r.points), React.createElement("span", { className:"text-[9px] text-neutral-500" }, "puntos"))))),''','''                React.createElement("button", { type:"button", onClick:()=>setPointsAdminOpen(v=>!v), className:"w-full mb-3 bg-gradient-to-r from-neutral-900 to-neutral-800 border border-orange-400/15 rounded-2xl px-4 py-3.5 text-sm font-black flex items-center justify-between" }, React.createElement("span", null, React.createElement("i", { className:"fas fa-ranking-star mr-2 text-orange-300" }), "Ranking del Club · usuarios y puntos"), React.createElement("i", { className:`fas ${pointsAdminOpen?'fa-chevron-up':'fa-chevron-down'}` })),
                pointsAdminOpen && React.createElement("div", { className:"grid gap-2 mb-4" },
                    React.createElement("div", { className:"flex items-center justify-between px-1 mb-1" }, React.createElement("span", { className:"text-[10px] uppercase tracking-widest text-neutral-500 font-black" }, "Ranking por puntos disponibles"), React.createElement("span", { className:"text-[10px] text-neutral-500" }, `${customerDniStats.length} usuarios`)),
                    customerDniStats.length===0 && React.createElement("p", { className:"text-sm text-neutral-500" }, "Todavía no hay usuarios con teléfono registrado."),
                    customerDniStats.map((r,index)=>React.createElement("div", { key:r.phone, className:`club-ranking-card ${index<3?`top-${index+1}`:''}` },
                        React.createElement("div", { className:"club-ranking-pos" }, index===0?'🥇':index===1?'🥈':index===2?'🥉':`#${index+1}`),
                        React.createElement("div", { className:"min-w-0" }, React.createElement("b", { className:"block text-sm sm:text-base truncate text-white" }, r.name||'Sin nombre'), React.createElement("span", { className:"block text-xs text-neutral-400 mt-0.5" }, r.phone), React.createElement("span", { className:"block text-[10px] text-neutral-500 mt-1" }, `${r.purchases} compras · ${formatPrice(r.spent)} gastados · ${r.redeemedPoints} canjeados`)),
                        React.createElement("div", { className:"club-ranking-points" }, r.points, React.createElement("small", null,"puntos"))))),''','ranking visual')

# Nearly invisible admin access at the very bottom of main gallery.
needle='''                React.createElement(PromoBanners, { bannerSettings: bannerSettings }))),'''
replacement='''                React.createElement(PromoBanners, { bannerSettings: bannerSettings }),
                React.createElement("div", { className:"admin-secret-footer" }, React.createElement("button", { type:"button", onClick:()=>{ try{localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin');}catch(e){} window.location.href=`${location.pathname}?admin=1#/admin`; }, title:"Administración" }, "Administración")))),'''
once(needle,replacement,'secret admin footer')

p.write_text(s,encoding='utf-8')
print('v84 patched')
