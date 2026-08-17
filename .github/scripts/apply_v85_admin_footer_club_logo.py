from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v84-admin-pwa-club-ranking','v85-admin-footer-club-logo')

# Use only the circular logo supplied by Lucas everywhere the Club header logo is referenced.
s=s.replace('https://i.postimg.cc/W3SqHj91/LA-Marca-de-agua-copia.png','https://i.postimg.cc/jSdxMNpb/LA-Marca-de-agua-copia2.png')

# Add a stronger final override so the admin access is discreet but actually visible on iPhone.
style='''\n<style id="v85-admin-footer-club-logo">\n.admin-secret-footer,.admin-footer-access-v85{display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;margin:28px auto 18px!important;opacity:.58!important;visibility:visible!important;pointer-events:auto!important;position:relative!important;z-index:20!important}\n.admin-secret-footer button,.admin-footer-access-v85 button{appearance:none!important;border:1px solid rgba(255,255,255,.13)!important;background:rgba(255,255,255,.045)!important;color:#a3a3a3!important;border-radius:999px!important;padding:9px 16px!important;font-size:10px!important;font-weight:800!important;letter-spacing:.12em!important;text-transform:uppercase!important;line-height:1!important;min-height:32px!important}\n.admin-secret-footer button:active,.admin-footer-access-v85 button:active{background:rgba(255,255,255,.10)!important;color:#fff!important;transform:scale(.98)}\n.la-insta-btn.la-club-header{gap:6px!important}\n.club-header-logo{width:23px!important;height:23px!important;object-fit:contain!important;object-position:center!important;border-radius:50%!important;padding:0!important;background:transparent!important;box-shadow:0 2px 8px rgba(0,0,0,.24)!important}\n@media(max-width:640px){.admin-secret-footer,.admin-footer-access-v85{margin:24px auto 16px!important;opacity:.68!important}.admin-secret-footer button,.admin-footer-access-v85 button{font-size:10px!important;padding:10px 15px!important}.club-header-logo{width:21px!important;height:21px!important}}\n</style>\n'''
if '</head>' not in s: raise SystemExit('missing head close')
s=s.replace('</head>',style+'</head>',1)

# Add an independent admin access after the main gallery content, so it is not tied to pagination/banner rendering.
needle='''        introOpen && !loading && allPhotos.length > 0 && route !== "#/admin" && React.createElement(PurchaseIntro, { photos: allPhotos, onClose: () => setIntroOpen(false) }),'''
replacement='''        route !== "#/admin" && route !== "#/club" && !currentAlbum && React.createElement("div", { className:"admin-footer-access-v85" },\n            React.createElement("button", { type:"button", onClick:()=>{ try { localStorage.setItem('LA_INSTALL_START_ROUTE','#/admin'); } catch(e) {} window.location.href=`${location.pathname}?admin=1#/admin`; }, title:"Administración" },\n                React.createElement("i", { className:"fas fa-lock mr-1.5" }), "Administración")),\n        introOpen && !loading && allPhotos.length > 0 && route !== "#/admin" && React.createElement(PurchaseIntro, { photos: allPhotos, onClose: () => setIntroOpen(false) }),'''
once(needle,replacement,'global admin footer access')

p.write_text(s,encoding='utf-8')
print('v85 patched')
