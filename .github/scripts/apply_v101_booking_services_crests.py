from pathlib import Path
from io import BytesIO
from collections import deque
import math
import requests
from PIL import Image

p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 occurrence, got {n}')
    s=s.replace(old,new,1)

# ---------- Pricing helpers ----------
needle="const CATEGORIES=['Primera','Reserva','4ta','5ta','6ta','7ma','9na','10ma','11ra','12da'];\n"
insert=needle+r"""const NIGHT_MATCH_PRICE=75000;
function isNightMatchEndTime(v){const t=String(v||'').trim();return /^\d{2}:\d{2}$/.test(t)&&t>='20:00'}
function bookingIsNight(b){return Boolean(b&&(b.service==='night'||isNightMatchEndTime(b.endTime)))}
function bookingServiceName(b){return bookingIsNight(b)?'Partido nocturno':'Cobertura de partido'}
function bookingPriceFor(endTime,basePayment,service='custom'){const night=isNightMatchEndTime(endTime)||service==='night';return {night,service:night?'night':'custom',payment:night?NIGHT_MATCH_PRICE:Number(basePayment||0)}}
"""
if 'const NIGHT_MATCH_PRICE=75000;' not in s:
    replace_once(needle,insert,'pricing helpers')

# ---------- Drafts and strict agenda visibility ----------
old=r"""async function createDraft(data){const id=uid();const clean={id,type:'booking',status:'pendiente',formCompleted:false,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),payment:Number(data.payment||0),adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}"""
new=r"""async function createDraft(data){const id=uid();const service=data.service==='night'?'night':'custom';const payment=service==='night'?NIGHT_MATCH_PRICE:Number(data.payment||0);const clean={id,type:'booking',status:'pendiente',formCompleted:false,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),service,payment,adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',endTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}"""
replace_once(old,new,'createDraft')

old=r"""function isAgendaBooking(b){if(!b)return false;if(b.formCompleted===true||b.confirmedAt)return true;return ['confirmado','realizado','cancelado'].includes(String(b.status||'').toLowerCase())&&Boolean(b.date&&b.home&&b.away)}"""
new=r"""function isAgendaBooking(b){if(!b)return false;const completed=Boolean(b.formCompleted===true||b.confirmedAt);const core=Boolean(b.date&&b.matchTime&&b.home&&b.away&&b.category&&b.venue&&b.address&&b.arrivalTime&&b.clientName&&b.phone);const hasEndTime=!Object.prototype.hasOwnProperty.call(b,'endTime')||Boolean(b.endTime);return completed&&core&&hasEndTime}"""
replace_once(old,new,'isAgendaBooking')

# ---------- Public form ----------
old=r"""<div class=\"field\"><label>Horario del partido</label><input required class=\"input\" type=\"time\" name=\"matchTime\" value=\"${esc(b.matchTime)}\"></div>${teamPickerMarkup('home','Equipo local',b.home)}"""
new=r"""<div class=\"field\"><label>Horario del partido</label><input required class=\"input\" type=\"time\" name=\"matchTime\" value=\"${esc(b.matchTime)}\"></div><div class=\"field\"><label>Hora de finalización</label><input required class=\"input\" type=\"time\" name=\"endTime\" value=\"${esc(b.endTime||'')}\"></div>${teamPickerMarkup('home','Equipo local',b.home)}"""
replace_once(old,new,'public end time')

old=r"""<div class=\"field\"><label>Pago acordado</label><input class=\"input\" readonly value=\"${money(b.payment)}\"></div><div class=\"field\"><label>Tu nombre</label>"""
new=r"""<div class=\"field\"><label>Servicio</label><input id=\"publicServiceDisplay\" class=\"input\" readonly value=\"${esc(bookingServiceName(b))}\"></div><div class=\"field\"><label>Pago acordado</label><input id=\"publicPaymentDisplay\" class=\"input\" readonly value=\"${money(b.payment)}\"></div><div class=\"field\"><label>Tu nombre</label>"""
replace_once(old,new,'public service display')

old=r"""function publicForm(b){currentDraft=b;document.title=`${b.id} · Contratación`;"""
new=r"""function wirePublicNightPricing(b){const form=$('#clientForm');if(!form)return;const end=form.querySelector('[name="endTime"]'),pay=$('#publicPaymentDisplay'),service=$('#publicServiceDisplay');const refresh=()=>{const pr=bookingPriceFor(end&&end.value,b.payment,b.service);if(pay)pay.value=money(pr.payment);if(service)service.value=pr.night?'Partido nocturno':'Cobertura de partido'};if(end){end.addEventListener('input',refresh);end.addEventListener('change',refresh)}refresh()}
function publicForm(b){currentDraft=b;document.title=`${b.id} · Contratación`;"""
replace_once(old,new,'public pricing helper')

replace_once(";initTeamPickers();$('#clientForm').onsubmit=submitClient}",";initTeamPickers();wirePublicNightPricing(b);$('#clientForm').onsubmit=submitClient}",'wire public pricing')

old=r"""async function submitClient(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget).entries());data.home=titleWords(data.home);data.away=titleWords(data.away);const msg=$('#msg');if(!data.home||!data.away){msg.innerHTML='<div class=\"notice err\">Elegí el equipo local y el visitante. Si no aparece, usá “Otro equipo”.</div>';return}msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';try{await saveBooking(currentDraft.id,{...data,status:'confirmado',formCompleted:true,confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado',formCompleted:true})}catch(err){msg.innerHTML='<div class=\"notice err\">No pude guardar la confirmación. Revisá tu conexión y volvé a intentar.</div>'}}"""
new=r"""async function submitClient(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget).entries());data.home=titleWords(data.home);data.away=titleWords(data.away);const msg=$('#msg');if(!data.home||!data.away){msg.innerHTML='<div class=\"notice err\">Elegí el equipo local y el visitante. Si no aparece, usá “Otro equipo”.</div>';return}const pricing=bookingPriceFor(data.endTime,currentDraft.payment,currentDraft.service);data.service=pricing.service;data.payment=pricing.payment;msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';try{await saveBooking(currentDraft.id,{...data,status:'confirmado',formCompleted:true,confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado',formCompleted:true})}catch(err){msg.innerHTML='<div class=\"notice err\">No pude guardar la confirmación. Revisá tu conexión y volvé a intentar.</div>'}}"""
replace_once(old,new,'submitClient pricing')

# ---------- Admin card ----------
old=r"""<span>⚽ Partido <strong>${esc(b.matchTime||'--:--')}</strong></span><span>💰 <strong>${money(b.payment)}</strong></span>"""
new=r"""<span>⚽ Partido <strong>${esc(b.matchTime||'--:--')}</strong></span><span>🏁 Finaliza <strong>${esc(b.endTime||'--:--')}</strong></span><span>📋 <strong>${esc(bookingServiceName(b))}</strong></span><span>💰 <strong>${money(b.payment)}</strong></span>"""
replace_once(old,new,'booking card service')

# ---------- Edit modal ----------
old=r"""<div class=\"field\"><label>Equipo local</label><input class=\"input\" name=\"home\" value=\"${esc(titleWords(b.home))}\"></div><div class=\"field\"><label>Equipo visitante</label><input class=\"input\" name=\"away\" value=\"${esc(titleWords(b.away))}\"></div>"""
new=r"""${teamPickerMarkup('home','Equipo local',b.home)}${teamPickerMarkup('away','Equipo visitante',b.away)}"""
replace_once(old,new,'edit team pickers')

old=r"""<div class=\"field\"><label>Hora partido</label><input class=\"input\" type=\"time\" name=\"matchTime\" value=\"${esc(b.matchTime||'')}\"></div>"""
new=r"""<div class=\"field\"><label>Hora partido</label><input class=\"input\" type=\"time\" name=\"matchTime\" value=\"${esc(b.matchTime||'')}\"></div><div class=\"field\"><label>Hora de finalización</label><input class=\"input\" type=\"time\" name=\"endTime\" value=\"${esc(b.endTime||'')}\"></div>"""
replace_once(old,new,'edit end time')

old=r"""<div class=\"field\"><label>Pago acordado</label><input class=\"input\" type=\"number\" min=\"0\" name=\"payment\" value=\"${esc(b.payment||0)}\"></div><div class=\"field\"><label>Estado</label>"""
new=r"""<div class=\"field\"><label>Servicio</label><select class=\"input\" name=\"service\" id=\"editService\"><option value=\"custom\" ${bookingIsNight(b)?'':'selected'}>Cobertura de partido</option><option value=\"night\" ${bookingIsNight(b)?'selected':''}>Partido nocturno · $75.000</option></select></div><div class=\"field\"><label>Pago acordado</label><input class=\"input\" type=\"number\" min=\"0\" name=\"payment\" value=\"${esc(b.payment||0)}\"></div><div class=\"field\"><label>Estado</label>"""
replace_once(old,new,'edit service')

old=r""";document.body.appendChild(modal);const close=()=>modal.remove();$('#closeEdit').onclick=close;"""
new=r""";document.body.appendChild(modal);initTeamPickers();const editForm=$('#editBookingForm'),editEnd=editForm.querySelector('[name="endTime"]'),editService=editForm.querySelector('[name="service"]'),editPayment=editForm.querySelector('[name="payment"]');const syncEditPricing=()=>{if(isNightMatchEndTime(editEnd.value)||editService.value==='night'){editService.value='night';editPayment.value=String(NIGHT_MATCH_PRICE)}};editEnd.addEventListener('change',syncEditPricing);editEnd.addEventListener('input',syncEditPricing);editService.addEventListener('change',syncEditPricing);syncEditPricing();const close=()=>modal.remove();$('#closeEdit').onclick=close;"""
replace_once(old,new,'init edit pickers')

old=r"""data.home=titleWords(data.home);data.away=titleWords(data.away);data.payment=Number(data.payment||0);$('#editMsg')"""
new=r"""data.home=titleWords(data.home);data.away=titleWords(data.away);const pricing=bookingPriceFor(data.endTime,data.payment,data.service);data.service=pricing.service;data.payment=pricing.payment;$('#editMsg')"""
replace_once(old,new,'edit save pricing')

# ---------- New booking quick service ----------
old=r"""<form id=\"draftForm\" class=\"formgrid\" style=\"margin-top:17px\"><div class=\"field full\"><label>Pago acordado</label><input required class=\"input\" type=\"number\" min=\"0\" name=\"payment\" placeholder=\"Ej: 60000\"></div>"""
new=r"""<form id=\"draftForm\" class=\"formgrid\" style=\"margin-top:17px\"><div class=\"field full\"><label>Servicio / tarifa</label><select class=\"input\" name=\"service\" id=\"draftService\"><option value=\"custom\">Tarifa personalizada</option><option value=\"night\">Partido nocturno · $75.000</option></select><div class=\"muted\">Partido nocturno: aplica cuando el partido finaliza a las 20:00 hs o después.</div></div><div class=\"field full\"><label>Pago acordado</label><input required class=\"input\" type=\"number\" min=\"0\" name=\"payment\" placeholder=\"Ej: 60000\"></div>"""
replace_once(old,new,'new service selector')

old=r""";document.body.appendChild(modal);$('#closeModal').onclick=()=>modal.remove();$('#draftForm').onsubmit=async e=>"""
new=r""";document.body.appendChild(modal);const draftService=$('#draftService'),draftPayment=$('#draftForm [name="payment"]');draftService.onchange=()=>{if(draftService.value==='night')draftPayment.value=String(NIGHT_MATCH_PRICE)};$('#closeModal').onclick=()=>modal.remove();$('#draftForm').onsubmit=async e=>"""
replace_once(old,new,'wire draft service')

# ---------- Calendar/details ----------
replace_once("function endDate(b){const s=startDate(b);if(!s)return null;return new Date(s.getTime()+3*60*60*1000)}","function endDate(b){if(b&&b.date&&b.endTime){const e=new Date(`${b.date}T${b.endTime}:00`);if(!Number.isNaN(e.getTime()))return e}const s=startDate(b);if(!s)return null;return new Date(s.getTime()+3*60*60*1000)}",'calendar end time')
replace_once(r"""Hora del partido: ${b.matchTime||''}\nLlegada fotógrafo: ${b.arrivalTime||''}\nCliente:""",r"""Hora del partido: ${b.matchTime||''}\nFinalización: ${b.endTime||''}\nServicio: ${bookingServiceName(b)}\nLlegada fotógrafo: ${b.arrivalTime||''}\nCliente:""",'calendar details')

if 'v101-booking-services-crests' not in s:
    s=s.replace('<!-- v100-hide-uncompleted-bookings -->','<!-- v100-hide-uncompleted-bookings -->\n<!-- v101-booking-services-crests -->',1)

p.write_text(s,encoding='utf-8')

# ---------- User-selected crest sources ----------
sources={
 'all-boys.png':'https://scontent.fcor11-1.fna.fbcdn.net/v/t39.30808-6/448251325_972821488184438_3977286275255435066_n.jpg?stp=dst-jpg_tt6&cstp=mx629x633&ctp=s629x633&_nc_cat=102&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=LhYNDVLtBaMQ7kNvwFYAidE&_nc_oc=Adp96eWOuWF2Md0sxmogWc4oP9TgTHYa1mMf8Dhq6cdh5YRi4SVAjf1nA9DwhjoNwXU&_nc_zt=23&_nc_ht=scontent.fcor11-1.fna&_nc_gid=Z92QASPgzf0-3aSF9rZXKw&_nc_ss=73289&oh=00_AQLodfZNdoVfzju6lH_ee8BGIEJGW_MHzp1tAhsk6BKnjg&oe=6A9E222E',
 'belgrano.png':'https://upload.wikimedia.org/wikipedia/commons/8/85/Escudo_Oficial_del_Club_Atl%C3%A9tico_Belgrano.png',
 'talleres.png':'https://www.clubtalleres.com.ar/wp-content/uploads/2025/03/escudo-2-estrellas-x2-251x300.png',
 'cibi.png':'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9uEIuQxH6RZDKQL9gQlQgiNnL9tCR4vcmDJRLKC1nPP2_9kWhhUrSYRbT&s=10',
 'deportivo-alberdi.png':'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_l8nMEpEbeVy38EHo1aR-vDqGWdzRGXxfao3fuzlLKewVrMJWaJNCqH8i&s=10',
 'deportivo-atalaya.png':'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6BaWbDmpakOVsS7TxkUKPgWnWLXHiXrse83BungsGbnGHm6vLlgkZPnvz&s=10',
 'deportivo-banfield.png':'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/10/banfield-cordoba-1.png',
 'general-paz-juniors.png':'https://logowik.com/content/uploads/images/club-general-paz-juniors8459.logowik.com.webp',
 'los-andes.png':'https://futbolfundaciones.wordpress.com/wp-content/uploads/2025/01/los-andes-cordoba-1.png',
 'union-florida.png':'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwrohFyobxodSUzpwKR58mQEQ-ZkSbYgXqC2iAdJDFwEKe48KKpGtqC3s&s=10',
 'villa-azalais.png':'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSAcgE5zmvwy7WZV6QCtcUWgdNsgsPhfPbAozDF_TjwshugH3oACXN4Mmc&s=10',
}

def color_dist(a,b):
    return math.sqrt(sum((int(a[i])-int(b[i]))**2 for i in range(3)))

def clean_background(raw,out_path):
    im=Image.open(BytesIO(raw)); im.load(); im=im.convert('RGBA')
    w,h=im.size; px=im.load()
    samples=[px[0,0][:3],px[w-1,0][:3],px[0,h-1][:3],px[w-1,h-1][:3],px[w//2,0][:3],px[w//2,h-1][:3],px[0,h//2][:3],px[w-1,h//2][:3]]
    bg=tuple(sorted(c[i] for c in samples)[len(samples)//2] for i in range(3))
    tol=62; seen=bytearray(w*h); q=deque()
    def ok(x,y):
        r,g,b,a=px[x,y]
        if a==0:return True
        near_white=(r>218 and g>218 and b>218 and max(r,g,b)-min(r,g,b)<36)
        return near_white or color_dist((r,g,b),bg)<=tol
    def add(x,y):
        idx=y*w+x
        if not seen[idx] and ok(x,y): seen[idx]=1; q.append((x,y))
    for x in range(w): add(x,0); add(x,h-1)
    for y in range(h): add(0,y); add(w-1,y)
    while q:
        x,y=q.popleft(); r,g,b,a=px[x,y]; px[x,y]=(r,g,b,0)
        if x:add(x-1,y)
        if x+1<w:add(x+1,y)
        if y:add(x,y-1)
        if y+1<h:add(x,y+1)
    bbox=im.getchannel('A').getbbox()
    if not bbox: raise RuntimeError(f'background cleaning erased entire image: {out_path}')
    im=im.crop(bbox); im.thumbnail((460,460),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(512,512),(0,0,0,0)); x=(512-im.width)//2; y=(512-im.height)//2; canvas.alpha_composite(im,(x,y))
    out_path.parent.mkdir(parents=True,exist_ok=True); canvas.save(out_path,'PNG',optimize=True)

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36','Accept':'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8','Referer':'https://www.google.com/'}
for filename,url in sources.items():
    print('downloading',filename)
    r=requests.get(url,headers=headers,timeout=40,allow_redirects=True); r.raise_for_status()
    if len(r.content)<1500: raise RuntimeError(f'{filename}: response too small ({len(r.content)} bytes)')
    clean_background(r.content,Path('assets/lcf')/filename)

print('v101 booking services, edit pickers and selected crests applied')
