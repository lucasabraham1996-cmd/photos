from pathlib import Path
import re

p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 got {n}')
    s=s.replace(old,new,1)

# Small visual treatment for the reusable public-request flow.
css=r'''
    /* v99: link público permanente para solicitar coberturas */
    .request-hero-badge{display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border-radius:999px;background:rgba(59,130,246,.12);border:1px solid rgba(96,165,250,.2);color:#bfdbfe;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}
    .request-explain{display:grid;gap:9px;margin-top:18px}.request-step{display:flex;align-items:flex-start;gap:10px;color:#cbd5e1;font-size:12px;line-height:1.45}.request-step b{display:grid;place-items:center;width:24px;height:24px;flex:0 0 24px;border-radius:8px;background:rgba(37,99,235,.16);color:#93c5fd;font-size:11px}
    .request-success-code{display:inline-flex;margin:12px auto 0;padding:9px 12px;border-radius:12px;background:rgba(255,255,255,.06);border:1px solid var(--line);font-size:11px;font-weight:900;color:#cbd5e1;letter-spacing:.05em}
'''
once('  </style>',css+'  </style>','request css')

# Preserve the distinction between a public request and an already priced booking.
old="function bookingServiceName(b){return bookingIsNight(b)?'Partido nocturno':'Cobertura de partido'}"
new="function bookingServiceName(b){return b&&b.service==='request'?'Solicitud de cobertura':bookingIsNight(b)?'Partido nocturno':'Cobertura de partido'}"
once(old,new,'booking service name')

# Public requests are complete enough to enter the agenda even though arrival time is defined later by Lucas.
old="function isAgendaBooking(b){if(!b)return false;const completed=Boolean(b.formCompleted===true||b.confirmedAt);const core=Boolean(b.date&&b.matchTime&&b.home&&b.away&&b.category&&b.venue&&b.address&&b.arrivalTime&&b.clientName&&b.phone);const hasEndTime=!Object.prototype.hasOwnProperty.call(b,'endTime')||Boolean(b.endTime);return completed&&core&&hasEndTime}"
new="function isAgendaBooking(b){if(!b)return false;const completed=Boolean(b.formCompleted===true||b.confirmedAt);const core=Boolean(b.date&&b.matchTime&&b.home&&b.away&&b.category&&b.venue&&b.address&&b.clientName&&b.phone);const arrivalReady=b.requestSource==='public'||Boolean(b.arrivalTime);const hasEndTime=!Object.prototype.hasOwnProperty.call(b,'endTime')||Boolean(b.endTime);return completed&&core&&arrivalReady&&hasEndTime}"
once(old,new,'agenda public request visibility')

# Helpers and complete public request screen, inserted before the existing pre-priced public form.
needle="function wirePublicNightPricing(b){"
request_code=r'''function publicRequestUrl(){return baseUrl()+'#/solicitar'}
function publicRequestPaymentLabel(b){return b&&b.requestSource==='public'&&Number(b.payment||0)<=0?'A definir':money(b&&b.payment)}
function publicRequestPage(){
  document.title='Solicitar cobertura · lucasabraham.ph';
  $('#app').innerHTML=appShell(`<div class="grid"><section class="card hero"><span class="request-hero-badge">📸 Solicitud abierta</span><div class="eyebrow" style="margin-top:18px">lucasabraham.ph</div><h2 class="title">Pedí la cobertura de tu partido.</h2><p class="copy">Completá los datos del encuentro y Lucas recibirá la solicitud directamente en su agenda. No necesitás que te envíe un enlace individual.</p><div class="request-explain"><div class="request-step"><b>1</b><span>Cargá fecha, horarios, equipos y cancha.</span></div><div class="request-step"><b>2</b><span>Dejá tu nombre y WhatsApp para poder confirmar disponibilidad.</span></div><div class="request-step"><b>3</b><span>La solicitud entra como <strong>pendiente</strong>. La cobertura queda confirmada cuando Lucas se contacte con vos.</span></div></div><div class="calendar-note" style="margin-top:18px"><b>Importante:</b> enviar esta solicitud no reserva automáticamente el partido ni confirma el precio.</div></section><section class="card"><h3 class="section-title">Datos del partido</h3><form id="publicRequestForm" class="formgrid"><div class="field"><label>Fecha del partido</label><input required class="input" type="date" name="date"></div><div class="field"><label>Horario del partido</label><input required class="input" type="time" name="matchTime"></div><div class="field"><label>Hora estimada de finalización</label><input required class="input" type="time" name="endTime"></div>${teamPickerMarkup('home','Equipo local','')}${teamPickerMarkup('away','Equipo visitante','')}<div class="field"><label>Categoría</label><select required class="input" name="category">${categoryOptions('')}</select></div><div class="field"><label>Cancha / estadio</label><input required class="input" name="venue" placeholder="Ej: Héroes de Malvinas"></div><div class="field full"><label>Dirección</label><input required class="input" name="address" placeholder="Ej: Av. X 1234, Córdoba"></div><div class="field"><label>Tu nombre</label><input required class="input" name="clientName" autocomplete="name" placeholder="Nombre y apellido"></div><div class="field"><label>WhatsApp / teléfono</label><input required class="input" name="phone" inputmode="tel" autocomplete="tel" placeholder="351..."></div><div class="field full"><label>Observaciones (opcional)</label><textarea class="input" rows="3" name="notes" placeholder="Referencia de ingreso, categorías adicionales u otra información útil."></textarea></div><div class="field full"><button class="btn green" type="submit">✓ Enviar solicitud de cobertura</button><div id="publicRequestMsg"></div></div></form></section></div>`,`<span class="pill">SOLICITAR COBERTURA</span>`);
  initTeamPickers();
  $('#publicRequestForm').onsubmit=submitPublicRequest;
}
async function submitPublicRequest(e){
  e.preventDefault();
  const form=e.currentTarget;
  const data=Object.fromEntries(new FormData(form).entries());
  data.home=titleWords(data.home);data.away=titleWords(data.away);data.clientName=titleWords(data.clientName);
  const msg=$('#publicRequestMsg');
  if(!data.home||!data.away){msg.innerHTML='<div class="notice err">Elegí el equipo local y el visitante. Si no aparece, usá “Otro equipo”.</div>';return}
  const submit=form.querySelector('button[type="submit"]');submit.disabled=true;submit.textContent='Enviando solicitud…';
  const id=uid();const now=new Date().toISOString();
  const clean={id,type:'booking',requestSource:'public',status:'pendiente',formCompleted:true,createdAt:now,updatedAt:now,service:'request',payment:0,adminNote:'Solicitud creada por el cliente desde el link público.',arrivalTime:'',...data};
  try{await bookingDoc(id).set(clean);renderPublicRequestSuccess(clean)}catch(err){console.error(err);submit.disabled=false;submit.textContent='✓ Enviar solicitud de cobertura';msg.innerHTML='<div class="notice err">No pude enviar la solicitud. Revisá tu conexión y volvé a intentar.</div>'}
}
function renderPublicRequestSuccess(b){
  const home=titleWords(b.home),away=titleWords(b.away);
  $('#app').innerHTML=appShell(`<div class="card success"><div class="check">✓</div><div class="eyebrow">Solicitud enviada</div><h2 class="title" style="max-width:none;font-size:40px">${esc(home)} vs ${esc(away)}</h2><p class="copy" style="max-width:620px;margin:0 auto">La solicitud ya ingresó a la agenda de Lucas como <b>pendiente</b>. Se va a comunicar con vos para confirmar disponibilidad, horario de llegada y valor de la cobertura.</p><div class="request-success-code">${esc(b.id)}</div><div class="actions" style="justify-content:center;margin-top:24px"><a class="btn ghost" href="${publicRequestUrl()}" style="text-decoration:none">Solicitar otro partido</a><a class="btn primary" href="${galleryUrl()}" style="text-decoration:none">Ver galería</a></div></div>`)
}
function wirePublicNightPricing(b){'''
once(needle,request_code,'public request functions')

# Make price/arrival visibly pending on user-created requests in the agenda card.
old="<span>📸 Llegar <strong>${esc(b.arrivalTime||'--:--')}</strong></span><span>⚽ Partido <strong>${esc(b.matchTime||'--:--')}</strong></span><span>🏁 Finaliza <strong>${esc(b.endTime||'--:--')}</strong></span><span>📋 <strong>${esc(bookingServiceName(b))}</strong></span><span>💰 <strong>${money(b.payment)}</strong></span>"
new="<span>📸 Llegar <strong>${esc(b.arrivalTime||(b.requestSource==='public'?'A definir':'--:--'))}</strong></span><span>⚽ Partido <strong>${esc(b.matchTime||'--:--')}</strong></span><span>🏁 Finaliza <strong>${esc(b.endTime||'--:--')}</strong></span><span>📋 <strong>${esc(bookingServiceName(b))}</strong></span><span>💰 <strong>${esc(publicRequestPaymentLabel(b))}</strong></span>"
once(old,new,'agenda public request labels')

# Add reusable public-link button to Admin header and wire it.
old="<button id=\"storyBtn\" class=\"btn green\">⬇ Historia agenda</button><button id=\"newBtn\" class=\"btn primary\">+ Nueva contratación</button><a class=\"btn ghost\" href=\"${galleryUrl()}\" style=\"text-decoration:none\">Ver galería</a>"
new="<button id=\"storyBtn\" class=\"btn green\">⬇ Historia agenda</button><button id=\"requestLinkBtn\" class=\"btn ghost\">🔗 Link de solicitudes</button><button id=\"newBtn\" class=\"btn primary\">+ Nueva contratación</button><a class=\"btn ghost\" href=\"${galleryUrl()}\" style=\"text-decoration:none\">Ver galería</a>"
once(old,new,'admin request link button')

old="$('#newBtn').onclick=openNew;$('#storyBtn').onclick=downloadAgendaStory;await renderAdminList()"
new="$('#newBtn').onclick=openNew;$('#storyBtn').onclick=downloadAgendaStory;$('#requestLinkBtn').onclick=async()=>{const btn=$('#requestLinkBtn');const link=publicRequestUrl();try{await navigator.clipboard.writeText(link);btn.textContent='Link copiado ✓';setTimeout(()=>btn.textContent='🔗 Link de solicitudes',1500)}catch(e){prompt('Copiá este link de solicitudes:',link)}};await renderAdminList()"
once(old,new,'wire admin request link')

# Route the reusable URL before the old individual-id/admin behavior.
old="const params=new URLSearchParams(location.search);const id=params.get('id');if(location.hash==='#/admin'||(!id&&location.hash==='#/admin'))return adminPage();if(id){"
new="const params=new URLSearchParams(location.search);const id=params.get('id');if(location.hash==='#/solicitar')return publicRequestPage();if(location.hash==='#/admin'||(!id&&location.hash==='#/admin'))return adminPage();if(id){"
once(old,new,'public request route')

p.write_text(s,encoding='utf-8')
print('v99 public request link patched')
