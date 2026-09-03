from pathlib import Path
import re

idx=Path('index.html')
con=Path('contrataciones.html')
s=idx.read_text(encoding='utf-8')
c=con.read_text(encoding='utf-8')

def once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 got {n}')
    return text.replace(old,new,1)

# ---------------- index.html: night tariff belongs to Admin > Precios ----------------
s=once(s,
'''        pricingVersion: 2,
        photoAppPrice: "$2.000",''',
'''        pricingVersion: 3,
        photoAppPrice: "$2.000",''',
'pricing version')

s=once(s,
'''        sessionPrice: "$10.000",
        sessionNote: "con el requisito de que haya, al menos, 5 jugadores que me hayan contratado de la categoría para asistir."
    };''',
'''        sessionPrice: "$10.000",
        sessionNote: "con el requisito de que haya, al menos, 5 jugadores que me hayan contratado de la categoría para asistir.",
        nightMatchPrice: "$75.000",
        nightMatchNote: "Tarifa para partidos que finalizan a las 20:00 hs o después."
    };''',
'default night tariff')

old_norm='''    if (!v || Number(v.pricingVersion) !== defaults.pricingVersion) {
        return {
            ...defaults,
            sessionPrice: (v && v.sessionPrice) || defaults.sessionPrice,
            sessionNote: (v && v.sessionNote) || defaults.sessionNote
        };
    }
    return { ...defaults, ...v, pricingVersion: defaults.pricingVersion };'''
new_norm='''    return { ...defaults, ...(v || {}), pricingVersion: defaults.pricingVersion };'''
s=once(s,old_norm,new_norm,'preserve existing price settings')

s=once(s,
'''• Sesión individual en partido: ${p.sessionPrice} ${p.sessionNote}
''',
'''• Sesión individual en partido: ${p.sessionPrice} ${p.sessionNote}
• Partido nocturno: ${p.nightMatchPrice} ${p.nightMatchNote}
''',
'whatsapp night tariff')

s=once(s,
'''                ['Sesión individual en partido', p.sessionPrice, p.sessionNote]
            ];''',
'''                ['Sesión individual en partido', p.sessionPrice, p.sessionNote],
                ['Partido nocturno', p.nightMatchPrice, p.nightMatchNote]
            ];''',
'price story night tariff')

s=once(s,
'''                    React.createElement(PriceItem, { title: "Sesión individual en partido", price: p.sessionPrice, note: p.sessionNote, icon: "fas fa-user-group" }))),''',
'''                    React.createElement(PriceItem, { title: "Sesión individual en partido", price: p.sessionPrice, note: p.sessionNote, icon: "fas fa-user-group" }),
                    React.createElement(PriceItem, { title: "Partido nocturno", price: p.nightMatchPrice, note: p.nightMatchNote, icon: "fas fa-moon" }))),''',
'public price sheet night tariff')

s=once(s,
'''                React.createElement(PriceAdminField, { fieldKey: "sessionPrice", label: "Sesión individual en partido", value: p["sessionPrice"], onChange: update }), React.createElement(PriceAdminField, { fieldKey: "sessionNote", label: "Requisito sesión individual", value: p["sessionNote"], onChange: update, big: true }))));''',
'''                React.createElement(PriceAdminField, { fieldKey: "sessionPrice", label: "Sesión individual en partido", value: p["sessionPrice"], onChange: update }), React.createElement(PriceAdminField, { fieldKey: "sessionNote", label: "Requisito sesión individual", value: p["sessionNote"], onChange: update, big: true }),
                React.createElement(PriceAdminField, { fieldKey: "nightMatchPrice", label: "Partido nocturno", value: p["nightMatchPrice"], onChange: update }), React.createElement(PriceAdminField, { fieldKey: "nightMatchNote", label: "Aclaración partido nocturno", value: p["nightMatchNote"], onChange: update, big: true }))));''',
'price admin night tariff fields')

# Add quick reusable request-link button in main Admin header.
needle='''                    React.createElement("button", { onClick: () => setPriceAdminOpen(true), className: "bg-emerald-500 text-black px-4 py-3 rounded-xl font-black" }, React.createElement("i", { className: "fas fa-tags mr-2" }), "Precios"),
                    React.createElement("button", { onClick: goToGallery, className: "bg-indigo-600 px-4 py-3 rounded-xl font-bold" }, "Ver galer\\u00EDa"))),'''
repl='''                    React.createElement("button", { onClick: () => setPriceAdminOpen(true), className: "bg-emerald-500 text-black px-4 py-3 rounded-xl font-black" }, React.createElement("i", { className: "fas fa-tags mr-2" }), "Precios"),
                    React.createElement("button", { onClick: async () => { const link='https://lucasabraham1996-cmd.github.io/photos/contrataciones.html#/solicitar'; try { await navigator.clipboard.writeText(link); setAdminMessage('Link público de solicitudes copiado.'); } catch(e) { window.prompt('Copiá el link público de solicitudes:', link); } }, className: "bg-sky-600 px-4 py-3 rounded-xl font-bold" }, React.createElement("i", { className: "fas fa-link mr-2" }), "Solicitudes"),
                    React.createElement("button", { onClick: goToGallery, className: "bg-indigo-600 px-4 py-3 rounded-xl font-bold" }, "Ver galer\\u00EDa"))),'''
s=once(s,needle,repl,'main admin request link')

idx.write_text(s,encoding='utf-8')

# ---------------- contrataciones.html: consume shared tariff, never choose it when creating an event ----------------
c=once(c,
'''const NIGHT_MATCH_PRICE=75000;''',
'''const NIGHT_MATCH_PRICE_FALLBACK=75000;
let NIGHT_MATCH_PRICE=NIGHT_MATCH_PRICE_FALLBACK;
const SHARED_STATE_DOC_PATH='artifacts/lucasabraham-ph-db/config/shared_state';''',
'night tariff constant')

# Load formatted $xx.xxx value from the same shared Firebase config used by Admin > Precios.
needle="""function money(v){return '$'+new Intl.NumberFormat('es-AR').format(Number(v||0))}"""
repl="""function money(v){return '$'+new Intl.NumberFormat('es-AR').format(Number(v||0))}
function parsePriceAmount(v){const digits=String(v??'').replace(/[^0-9]/g,'');return Number(digits||0)}
async function loadNightMatchPrice(){try{if(!db)return NIGHT_MATCH_PRICE;const snap=await db.doc(SHARED_STATE_DOC_PATH).get();if(snap&&snap.exists){const cfg=snap.data()||{};const n=parsePriceAmount(cfg&&cfg.priceSettings&&cfg.priceSettings.nightMatchPrice);if(n>0)NIGHT_MATCH_PRICE=n}}catch(e){console.warn('No pude leer tarifa nocturna compartida.',e)}return NIGHT_MATCH_PRICE}"""
c=once(c,needle,repl,'shared tariff loader')

# New admin-created event: only custom agreed payment; night tariff is automatic later from end time.
old_create="""async function createDraft(data){const id=uid();const service=data.service==='night'?'night':'custom';const payment=service==='night'?NIGHT_MATCH_PRICE:Number(data.payment||0);const clean={id,type:'booking',status:'pendiente',formCompleted:false,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),service,payment,adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',endTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}"""
new_create="""async function createDraft(data){const id=uid();const service='custom';const payment=Number(data.payment||0);const clean={id,type:'booking',status:'pendiente',formCompleted:false,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),service,payment,adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',endTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}"""
c=once(c,old_create,new_create,'create draft no night selector')

# Remove service/tariff selector from New booking modal.
c=c.replace('''<div class=\"field full\"><label>Servicio / tarifa</label><select class=\"input\" name=\"service\" id=\"draftService\"><option value=\"custom\">Tarifa personalizada</option><option value=\"night\">Partido nocturno · $75.000</option></select><div class=\"muted\">Partido nocturno: aplica cuando el partido finaliza a las 20:00 hs o después.</div></div>''','',1)
c=c.replace(""";document.body.appendChild(modal);const draftService=$('#draftService'),draftPayment=$('#draftForm [name=\"payment\"]');draftService.onchange=()=>{if(draftService.value==='night')draftPayment.value=String(NIGHT_MATCH_PRICE)};$('#closeModal').onclick""",""";document.body.appendChild(modal);$('#closeModal').onclick""",1)
if 'id=\\"draftService\\"' in c or "const draftService=$('#draftService')" in c:
    raise SystemExit('draft service selector still present')

# Remove manual service selector from edit modal too; night mode is derived only from end time.
service_edit='''<div class=\"field\"><label>Servicio</label><select class=\"input\" name=\"service\" id=\"editService\"><option value=\"custom\" ${bookingIsNight(b)?'':'selected'}>Cobertura de partido</option><option value=\"night\" ${bookingIsNight(b)?'selected':''}>Partido nocturno · $75.000</option></select></div>'''
if c.count(service_edit)!=1:
    raise SystemExit(f'edit service selector expected 1 got {c.count(service_edit)}')
c=c.replace(service_edit,'',1)
old_editwire=""";document.body.appendChild(modal);initTeamPickers();const editForm=$('#editBookingForm'),editEnd=editForm.querySelector('[name=\"endTime\"]'),editService=editForm.querySelector('[name=\"service\"]'),editPayment=editForm.querySelector('[name=\"payment\"]');const syncEditPricing=()=>{if(isNightMatchEndTime(editEnd.value)||editService.value==='night'){editService.value='night';editPayment.value=String(NIGHT_MATCH_PRICE)}};editEnd.addEventListener('change',syncEditPricing);editEnd.addEventListener('input',syncEditPricing);editService.addEventListener('change',syncEditPricing);syncEditPricing();"""
new_editwire=""";document.body.appendChild(modal);initTeamPickers();const editForm=$('#editBookingForm'),editEnd=editForm.querySelector('[name=\"endTime\"]'),editPayment=editForm.querySelector('[name=\"payment\"]');const syncEditPricing=()=>{if(isNightMatchEndTime(editEnd.value))editPayment.value=String(NIGHT_MATCH_PRICE)};editEnd.addEventListener('change',syncEditPricing);editEnd.addEventListener('input',syncEditPricing);syncEditPricing();"""
c=once(c,old_editwire,new_editwire,'edit automatic night pricing')

# Saving edited events derives service from the end time, not a manual selector.
c=once(c,
"""const pricing=bookingPriceFor(data.endTime,data.payment,data.service);data.service=pricing.service;data.payment=pricing.payment;""",
"""const pricing=bookingPriceFor(data.endTime,data.payment,'custom');data.service=pricing.service;data.payment=pricing.payment;""",
'edit derive service from time')

# Load tariff before rendering any route.
c=once(c,
"""async function boot(){const ok=await initFirebase();if(!ok){""",
"""async function boot(){const ok=await initFirebase();if(!ok){""",
'boot anchor')
c=once(c,
"""if(!ok){$('#app').innerHTML=appShell('<div class=\"notice err\">No se pudo iniciar Firebase.</div>');return}const params=new URLSearchParams(location.search);""",
"""if(!ok){$('#app').innerHTML=appShell('<div class=\"notice err\">No se pudo iniciar Firebase.</div>');return}await loadNightMatchPrice();const params=new URLSearchParams(location.search);""",
'load tariff at boot')

con.write_text(c,encoding='utf-8')
print('v100 night tariff moved to Admin prices + quick request link')
