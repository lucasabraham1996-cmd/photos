from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'v73-club-header-link-delivered-points' in s:
    print('v73 already applied')
    raise SystemExit(0)

# Version
s, n = re.subn(r'<meta name="app-version" content="[^"]+"\s*/>', '<meta name="app-version" content="v73-club-header-link-delivered-points" />', s, count=1)
if n != 1:
    raise SystemExit('app-version anchor missing')

# Final UI overrides: header flush to top, fourth Club button, no floating Club button.
css = r'''
<style id="v73-club-header-link">
.club-floating-btn{display:none!important}
.la-insta-btn.la-club-header{background:linear-gradient(135deg,rgba(249,115,22,.22),rgba(239,68,68,.16))!important;border-color:rgba(251,146,60,.38)!important;color:#ffedd5!important}
.la-insta-btn.la-club-header:hover{border-color:rgba(251,146,60,.7)!important;background:linear-gradient(135deg,rgba(249,115,22,.32),rgba(239,68,68,.23))!important}
.club-share-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.055);color:#fff;border-radius:14px;padding:10px 13px;font-size:12px;font-weight:900;margin:0 0 12px}
.club-share-btn:active{transform:scale(.985)}
@media(max-width:768px){
  .la-insta-topbar{position:fixed!important;top:0!important;left:0!important;right:0!important;width:100%!important;max-width:none!important;margin:0!important;border-radius:0 0 18px 18px!important;z-index:9999!important;padding-top:max(7px,env(safe-area-inset-top))!important;transform:none!important}
  .la-insta-topbar + header{margin-top:76px!important}
  .la-insta-actions{gap:5px!important}
  .la-insta-btn{min-width:0!important;padding-left:7px!important;padding-right:7px!important}
  .la-insta-btn.la-club-header span{font-size:10px!important}
}
</style>
'''
if '</head>' not in s:
    raise SystemExit('head tag missing')
s = s.replace('</head>', css + '</head>', 1)

# Points: ONLY explicit delivered=true earns points.
old = "            const confirmed = isTruthyStatus(o.delivered) || ['entregado','cargado_y_entregado','pagado'].includes(status);"
new = "            const confirmed = isTruthyStatus(o.delivered);"
if old not in s:
    raise SystemExit('confirmed points anchor missing')
s = s.replace(old, new, 1)

# Add club routing/share helpers after gallery install URL helper.
anchor = '''    const getGalleryInstallUrl = () => {\n        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;\n        return `${base || (location.href || '').split('#')[0]}#/galeria`;\n    };\n'''
helpers = '''    const getClubUrl = () => {\n        const base = `${location.origin && location.origin !== 'null' ? location.origin : ''}${location.pathname || ''}`;\n        return `${base || (location.href || '').split('#')[0]}#/club`;\n    };\n    const openClub = () => {\n        setClubModalOpen(true);\n        if (location.hash !== '#/club') location.hash = '#/club';\n    };\n    const closeClub = () => {\n        setClubModalOpen(false);\n        if (location.hash === '#/club') location.hash = '#/galeria';\n    };\n    const shareClubLink = async () => {\n        const url = getClubUrl();\n        try {\n            if (navigator.share) {\n                await navigator.share({ title:'Club de beneficios · lucasabraham.ph', text:'Consultá tus puntos y beneficios.', url });\n                return;\n            }\n        } catch (e) {\n            if (e && e.name === 'AbortError') return;\n        }\n        try {\n            await navigator.clipboard.writeText(url);\n            alert('Link del Club copiado.');\n        } catch (e) {\n            window.prompt('Copiá el link del Club:', url);\n        }\n    };\n'''
if anchor not in s:
    raise SystemExit('gallery url helper anchor missing')
s = s.replace(anchor, anchor + helpers, 1)

# Route #/club opens the Club directly when shared.
route_anchor = '''    useEffect(() => { const h = () => { const hash = location.hash || "#/galeria"; setRoute(hash); setActiveAlbum(getAlbumIdFromHash(hash)); setActiveSubAlbum(getSubAlbumIdFromHash(hash)); }; addEventListener('hashchange', h); h(); return () => removeEventListener('hashchange', h); }, []);\n'''
route_effect = '''    useEffect(() => {\n        if (route === '#/club') setClubModalOpen(true);\n    }, [route]);\n'''
if route_anchor not in s:
    raise SystemExit('route effect anchor missing')
s = s.replace(route_anchor, route_anchor + route_effect, 1)

# Add Club as fourth action button in the top header.
old = '''                    React.createElement("button", { onClick: () => window.open(`https://wa.me/${SELLER_PHONE}`, '_blank'), className: "la-insta-btn la-insta-whatsapp", title: "WhatsApp" },\n                        React.createElement("i", { className: "fab fa-whatsapp" }),\n                        React.createElement("span", null, "WhatsApp")),\n                    )),'''
new = '''                    React.createElement("button", { onClick: () => window.open(`https://wa.me/${SELLER_PHONE}`, '_blank'), className: "la-insta-btn la-insta-whatsapp", title: "WhatsApp" },\n                        React.createElement("i", { className: "fab fa-whatsapp" }),\n                        React.createElement("span", null, "WhatsApp")),\n                    React.createElement("button", { onClick: openClub, className: "la-insta-btn la-club-header", title: "Club de beneficios" },\n                        React.createElement("i", { className: "fas fa-gift" }),\n                        React.createElement("span", null, "Club")),\n                    )),'''
if old not in s:
    raise SystemExit('topbar buttons anchor missing')
s = s.replace(old, new, 1)

# Remove the old large Club section from the home page entirely.
pattern = re.compile(r'''\n            !currentAlbum && React\.createElement\("section", \{ className:"club-benefits-shell mb-4 sm:mb-5" \},.*?\n            React\.createElement\("div", \{ className: "mb-3 sm:mb-5" \},''', re.S)
replacement = '''\n            React.createElement("div", { className: "mb-3 sm:mb-5" },'''
s, n = pattern.subn(lambda m: replacement, s, count=1)
if n != 1:
    raise SystemExit(f'old club home section replacement count {n}')

# Remove floating Club button; access is now in header.
float_line = '''        !checkoutOpen && !viewer && route !== "#/admin" && React.createElement("button", { type:"button", onClick:() => setClubModalOpen(true), className:"club-floating-btn", title:"Abrir Club de beneficios" }, React.createElement("span", { className:"club-float-dot" }), React.createElement("i", { className:"fas fa-gift" }), React.createElement("span", null, "Club de beneficios")),\n'''
if float_line not in s:
    raise SystemExit('floating club button anchor missing')
s = s.replace(float_line, '', 1)

# Club modal: close cleanly back to gallery and add shareable-link control.
s = s.replace('clubModalOpen && React.createElement(Modal, { onClose:() => setClubModalOpen(false), max:"max-w-2xl" },', 'clubModalOpen && React.createElement(Modal, { onClose:closeClub, max:"max-w-2xl" },', 1)
header_old = '''                React.createElement("div", { className:"club-modal-header" },\n                    React.createElement("div", null, React.createElement("p", { className:"text-[10px] uppercase tracking-[.18em] text-orange-300 font-black mb-2" }, "Club lucasabraham.ph"), React.createElement("h2", { className:"club-modal-title" }, "Club de beneficios"), React.createElement("p", { className:"club-modal-copy" }, "Sumás 1 punto por cada $5.000 acumulados. Si una compra individual llega a $10.000 o más, suma 1 punto extra: una compra de $10.000 genera 3 puntos."))),\n                React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn w-full mb-3" },'''
header_new = '''                React.createElement("div", { className:"club-modal-header" },\n                    React.createElement("div", null, React.createElement("p", { className:"text-[10px] uppercase tracking-[.18em] text-orange-300 font-black mb-2" }, "Club lucasabraham.ph"), React.createElement("h2", { className:"club-modal-title" }, "Club de beneficios"), React.createElement("p", { className:"club-modal-copy" }, "Sumás 1 punto por cada $5.000 acumulados. Si una compra individual llega a $10.000 o más, suma 1 punto extra: una compra de $10.000 genera 3 puntos."))),\n                React.createElement("button", { type:"button", onClick:shareClubLink, className:"club-share-btn" }, React.createElement("i", { className:"fas fa-share-nodes" }), "Compartir link del Club"),\n                React.createElement("button", { type:"button", onClick:() => setClubPointsOpen(v => !v), className:"club-points-btn w-full mb-3" },'''
if header_old not in s:
    raise SystemExit('club modal header anchor missing')
s = s.replace(header_old, header_new, 1)

# Checkout button: no field list in collapsed orange button.
old = '''                            React.createElement("b", null, customerDetailsSaved ? "Datos guardados para beneficios" : "Quiero sumar puntos para beneficios"),\n                            React.createElement("small", null, customerDetailsSaved ? `${checkoutCustomerName} · ${checkoutPhone}${checkoutDni ? ` · DNI ${normalizeDni(checkoutDni)}` : ''}` : "Nombre y apellido · celular · DNI opcional")),'''
new = '''                            React.createElement("b", null, customerDetailsSaved ? "Datos listos para sumar puntos" : "Quiero sumar puntos con esta compra"),\n                            React.createElement("small", null, customerDetailsSaved ? "Se acreditan cuando el pedido quede entregado" : "El DNI identifica tu cuenta y permite acumular los puntos")),'''
if old not in s:
    raise SystemExit('benefits button text anchor missing')
s = s.replace(old, new, 1)

# DNI helper and save button wording.
old = '''                                React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "El DNI se solicita para acumular puntos del Club. Ingresalo sin puntos; si escribís puntos, espacios o guiones, se unifica automáticamente.")),\n                            React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-floppy-disk mr-2" }), "Guardar datos"),'''
new = '''                                React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "El DNI es el dato que identifica tu cuenta para acumular puntos del Club.")),\n                            React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-coins mr-2" }), "Guardar y sumar puntos con la compra"),'''
if old not in s:
    raise SystemExit('DNI helper/save wording anchor missing')
s = s.replace(old, new, 1)

# Explicit copy in preview: only delivered orders earn points.
old = '                            React.createElement("p", { className:"text-[10px] text-neutral-400 mt-2 leading-relaxed" }, "Los puntos de esta compra se acreditan cuando el pedido queda marcado como entregado."))'
new = '                            React.createElement("p", { className:"text-[10px] text-neutral-400 mt-2 leading-relaxed" }, "Los puntos se acreditan únicamente cuando Lucas confirma el pedido como entregado. Los pedidos pendientes o rechazados no suman."))'
if old not in s:
    raise SystemExit('points preview wording anchor missing')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('v73 patch applied')
