from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v87-admin-history-pending-only','v88-admin-gallery-navigation')

# Add one robust navigation helper. It deliberately removes ?admin=1 so the route effect
# cannot bounce the user back into Admin after pressing Galeria.
needle='''    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;'''
replacement='''    const goToGallery = () => {
        try { localStorage.setItem('LA_INSTALL_START_ROUTE', '#/galeria'); } catch(e) {}
        try {
            const cleanUrl = `${location.pathname || '/'}#/galeria`;
            history.replaceState(null, '', cleanUrl);
        } catch(e) {
            try { location.href = `${location.pathname || '/'}#/galeria`; } catch(_e) { location.hash = '#/galeria'; }
        }
        setRoute('#/galeria');
        setActiveAlbum(null);
        setActiveSubAlbum('');
        setClubModalOpen(false);
        try { window.scrollTo({ top:0, behavior:'smooth' }); } catch(e) {}
    };
    const getGalleryInstallUrl = () => {
        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;'''
once(needle,replacement,'goToGallery helper')

# admin=1 should recover an Admin shortcut if the hash is missing, but must NOT override an
# explicit navigation to #/galeria. The saved standalone route still repairs old Admin shortcuts.
old="""    useEffect(() => { const h = () => { let hash = location.hash || \"#/galeria\"; try { const standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; const saved = localStorage.getItem('LA_INSTALL_START_ROUTE'); const adminQuery = new URLSearchParams(location.search).get('admin') === '1'; if (adminQuery || (standalone && saved === '#/admin' && (!location.hash || location.hash === '#/galeria'))) { if (hash !== '#/admin') location.hash = '#/admin'; hash = '#/admin'; } if (hash === '#/admin') localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);"""
new="""    useEffect(() => { const h = () => { let hash = location.hash || \"#/galeria\"; try { const standalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true; const saved = localStorage.getItem('LA_INSTALL_START_ROUTE'); const adminQuery = new URLSearchParams(location.search).get('admin') === '1'; const recoverAdminShortcut = (adminQuery && !location.hash) || (standalone && saved === '#/admin' && (!location.hash || location.hash === '#/galeria')); if (recoverAdminShortcut) { if (hash !== '#/admin') location.hash = '#/admin'; hash = '#/admin'; } if (hash === '#/admin') localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);"""
once(old,new,'route admin query behavior')

# Admin header gallery button must use the robust helper.
once('''React.createElement("button", { onClick: () => location.hash = "#/galeria", className: "bg-indigo-600 px-4 py-3 rounded-xl font-bold" }, "Ver galer\\u00EDa")''',
     '''React.createElement("button", { onClick: goToGallery, className: "bg-indigo-600 px-4 py-3 rounded-xl font-bold" }, "Ver galer\\u00EDa")''',
     'admin gallery button')

# Remove the older embedded footer access completely; retain only the independent global access.
old_footer='''                React.createElement(PromoBanners, { bannerSettings: bannerSettings }),
                React.createElement("div", { className:"admin-secret-footer" }, React.createElement("button", { type:"button", onClick:()=>{ try{localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin');}catch(e){} window.location.href=`${location.pathname}?admin=1#/admin`; }, title:"Administración" }, "Administración")))),'''
new_footer='''                React.createElement(PromoBanners, { bannerSettings: bannerSettings }))),'''
once(old_footer,new_footer,'remove duplicate admin footer')

# The sole footer access is icon-only, with an accessible aria label/title but no visible text.
old_global='''        route !== "#/admin" && route !== "#/club" && !currentAlbum && React.createElement("div", { className:"admin-footer-access-v85" },
            React.createElement("button", { type:"button", onClick:()=>{ try { localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} window.location.href=`${location.pathname}?admin=1#/admin`; }, title:"Administración" },
                React.createElement("i", { className:"fas fa-lock mr-1.5" }), "Administración")),'''
new_global='''        route !== "#/admin" && route !== "#/club" && !currentAlbum && React.createElement("div", { className:"admin-footer-access-v85" },
            React.createElement("button", { type:"button", onClick:()=>{ try { localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} window.location.href=`${location.pathname}?admin=1#/admin`; }, title:"Administración", "aria-label":"Administración" },
                React.createElement("i", { className:"fas fa-lock" }))),'''
once(old_global,new_global,'icon only admin footer')

# Final CSS override: tiny charcoal lock, no link/button chrome. Still tappable via a larger invisible hit area.
style='''\n<style id="v88-admin-gallery-navigation">\n.admin-secret-footer{display:none!important}\n.admin-footer-access-v85{display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;margin:30px auto 16px!important;opacity:1!important;visibility:visible!important;pointer-events:auto!important;position:relative!important;z-index:20!important}\n.admin-footer-access-v85 button{appearance:none!important;border:0!important;outline:0!important;background:transparent!important;box-shadow:none!important;width:38px!important;height:38px!important;min-height:0!important;padding:0!important;margin:0!important;border-radius:50%!important;display:flex!important;align-items:center!important;justify-content:center!important;color:#202020!important;font-size:11px!important;opacity:.55!important;cursor:pointer!important;text-decoration:none!important;letter-spacing:0!important}\n.admin-footer-access-v85 button:hover,.admin-footer-access-v85 button:focus{background:transparent!important;color:#292929!important;opacity:.75!important}\n.admin-footer-access-v85 button:active{background:transparent!important;color:#333!important;opacity:.9!important;transform:scale(.94)!important}\n@media(max-width:640px){.admin-footer-access-v85{margin:24px auto 12px!important}.admin-footer-access-v85 button{width:42px!important;height:42px!important;font-size:11px!important;color:#202020!important;opacity:.58!important}}\n</style>\n'''
if '</head>' not in s: raise SystemExit('missing </head>')
s=s.replace('</head>',style+'</head>',1)

p.write_text(s,encoding='utf-8')
print('v88 patched')
