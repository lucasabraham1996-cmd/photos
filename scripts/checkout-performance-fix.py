#!/usr/bin/env python3
"""One-time, guarded migration of the existing single-file application."""
from pathlib import Path
import re
import sys

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

def replace(old, new, count=1):
    global s
    actual = s.count(old)
    if actual != count:
        raise RuntimeError(f'Expected {count} occurrences, got {actual}: {old[:110]!r}')
    s = s.replace(old, new)

def region(start, end, transform):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + transform(s[a:b]) + s[b:]

# Club membership is an explicit choice, never a checkout prerequisite.
replace('setCustomerDetailsOpen(false);\n        setCustomerDetailsSaved(false);', 'setCustomerDetailsOpen(false);\n        setCheckoutWantsPoints(false);\n        setCustomerDetailsSaved(false);')
replace('setCheckoutDni(\'\'); setCheckoutWantsPoints(true);', "setCheckoutDni(''); setCheckoutWantsPoints(true);")
replace('if(!String(checkoutCustomerName||\'\').trim()||!normalizePhone(checkoutPhone)){setCustomerDetailsOpen(true);alert(\'Antes de finalizar, guardá tu nombre y apellido y un celular de contacto.\');return}', "if(checkoutWantsPoints&&!customerDetailsSaved){setCustomerDetailsOpen(true);alert('Guardá los datos del Club o elegí continuar sin sumar puntos.');return}")
replace('const cleanPhone = normalizeClubPhone(checkoutPhone);\n        msg +=', 'const cleanPhone = checkoutWantsPoints && customerDetailsSaved ? normalizeClubPhone(checkoutPhone) : \'\';\n        msg +=')
replace('msg += `${EM.point} *Club:* puntos asociados al celular ${cleanPhone}', 'msg += `${EM.point} *Club:* ${cleanPhone ? `puntos asociados al celular ${cleanPhone}` : \'Compra sin Club · no suma puntos\'}')
replace('customerName: String(checkoutCustomerName || "").trim(),\n            dni: \'\',\n            phone: normalizeClubPhone(checkoutPhone),\n            wantsPoints: true,', 'customerName: cleanPhone ? String(checkoutCustomerName || "").trim() : \'\',\n            dni: \'\',\n            phone: cleanPhone,\n            wantsPoints: Boolean(cleanPhone),')
replace('if (orderPhone !== phone) return;\n            const status', "if (orderPhone !== phone) return;\n            if (o.wantsPoints === false && !['club_points_transfer','club_points_adjustment','benefit_redemption'].includes(o.type)) return;\n            const status")
replace('"Tu celular es obligatorio y funciona como tu cuenta del Club"', '"Opcional: sumá puntos con tu celular, o comprá sin registrarte"')
replace('"Identificate para sumar puntos"', '"Quiero sumar puntos (opcional)"')
replace('required:true, onChange:e => { setCheckoutPhone', 'onChange:e => { setCheckoutPhone')
replace('"Celular obligatorio · ej. 351 1234567"', '"Celular para sumar puntos · ej. 351 1234567"')
replace('"Ingresá un celular válido. Es obligatorio y se usa para identificar tus puntos."', '"Ingresá un celular válido para identificar tus puntos."')
# When editing a saved identity, invalidate the consent until it is saved again.
replace('setCheckoutCustomerName(e.target.value); setCustomerDetailsSaved(false);', 'setCheckoutCustomerName(e.target.value); setCustomerDetailsSaved(false); setCheckoutWantsPoints(false);')
replace('setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false);', 'setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false); setCheckoutWantsPoints(false);')
# Show the guest path before the optional loyalty form; keep the existing save handler.
marker = '                React.createElement("div", { className: "mb-3" },\n                    React.createElement("button", { type:"button", onClick:() => setCustomerDetailsOpen(v => !v)'
replace(marker, '''                React.createElement("div", { className:"checkout-guest-choice", role:"group", "aria-label":"Elegí cómo comprar" },
                    React.createElement("button", { type:"button", className:`checkout-guest-btn ${!checkoutWantsPoints ? 'active' : ''}`, onClick:()=>{setCheckoutWantsPoints(false);setCustomerDetailsSaved(false);setCustomerDetailsOpen(false);setCheckoutPriorClubAccount(null);setCheckoutCustomerName('');setCheckoutPhone('');setClubSessionPhone('');try{localStorage.removeItem('LA_CLUB_PHONE')}catch(e){}} }, "Continuar sin sumar puntos"),
                    React.createElement("p", null, "No necesitás registrarte. Elegí tus fotos, finalizá el pedido y envialo por WhatsApp.")),
''' + marker)
replace('setCustomerDetailsOpen(v => !v), className:`benefits-glass-btn', 'setCustomerDetailsOpen(v => !v), className:`benefits-glass-btn')
# Keep an opted-in saved profile intact when merely closing its panel.
replace('customerDetailsSaved && normalizeClubPhone(checkoutPhone) && React.createElement', 'checkoutWantsPoints && customerDetailsSaved && normalizeClubPhone(checkoutPhone) && React.createElement')
# Do not eagerly load every image in an album. Keep the existing order of photos and
# the original photo records so cart, full-resolution links and delivery stay intact.
replace('const totalAlbumPages = 1;\n    const safeAlbumPage = 1;\n    const pagedPhotos = [...albumPhotos].reverse();', '''const totalAlbumPages = Math.max(1, Math.ceil(albumPhotos.length / 60));
    const safeAlbumPage = Math.min(Math.max(1, albumPage), totalAlbumPages);
    const pagedPhotos = useMemo(() => albumPhotos.slice((safeAlbumPage - 1) * 60, safeAlbumPage * 60).reverse(), [albumPhotos, safeAlbumPage]);''')
# Enable the existing pagination controls rather than replacing them with an unbounded DOM.
replace('false && React.createElement("div", { className: "page-panel', 'totalAlbumPages > 1 && React.createElement("div", { className: "page-panel', 2)
replace('src: photo.url, loading: "lazy", decoding: "async"', 'src: toImgUrl(photo.rawUrl || photo.fullUrl || photo.url, 360), loading: "lazy", decoding: "async"')
replace('src:p.url, loading:"lazy", alt:p.name || p.code', 'src:toImgUrl(p.rawUrl || p.fullUrl || p.url, 180), loading:"lazy", alt:p.name || p.code')
# Avoid a fresh network request on each return visit when a valid cached gallery exists.
replace('const data = await fetchGalleryData({ force: !!force });', '''const data = await fetchGalleryData({ force: !!force });''')
# Cache fast first paint: hide the boot overlay when cached data is available.
replace('if (cachedAlbums.length)\n                setAlbums(cachedAlbums);', "if (cachedAlbums.length) {\n                setAlbums(cachedAlbums);\n                try { hideBootOverlay(); } catch(e) {}\n            }")
# A responsive non-blocking explanation near the final button.
replace('"Se abre WhatsApp con el pedido listo. Luego adjuntá el comprobante de la transferencia en el mismo chat."', '"No necesitás registrarte para comprar. Se abre WhatsApp con el pedido listo; enviá el mensaje y adjuntá el comprobante."')
css = '''<style id="la-v104-guest-performance">
.checkout-guest-choice{display:grid;gap:8px;margin:0 0 12px;padding:12px;border:1px solid rgba(255,255,255,.13);border-radius:16px;background:rgba(255,255,255,.035)}
.checkout-guest-btn{width:100%;min-height:48px;border:1px solid rgba(134,239,172,.45);border-radius:13px;background:#166534;color:#fff;font-size:14px;font-weight:900;padding:12px;cursor:pointer}
.checkout-guest-btn.active{background:#15803d;box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)}
.checkout-guest-choice p{margin:0;color:#d4d4d8;font-size:12px;line-height:1.5}
.checkout-simple-shell{max-width:100%;box-sizing:border-box}
@media(max-width:640px){.checkout-guest-choice{padding:10px}.checkout-guest-btn{min-height:48px;font-size:13px}.checkout-simple-shell{padding-bottom:90px!important}.page-panel{min-width:0}}
</style>\n'''
replace('</head>', css + '</head>')
replace('v103-order-recovery', 'v104-guest-performance')
# Assert no mandatory identity remains at the send boundary.
assert 'if(checkoutWantsPoints&&!customerDetailsSaved)' in s
assert 'wantsPoints: Boolean(cleanPhone)' in s
assert 'const totalAlbumPages = Math.max(1, Math.ceil(albumPhotos.length / 60))' in s
assert 'if(!String(checkoutCustomerName' not in s
assert s != original
p.write_text(s, encoding='utf-8')
print('Migration assertions passed; changed index.html bytes:', len(s.encode()))
