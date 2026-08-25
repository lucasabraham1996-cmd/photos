from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

# Helpers: team names always in title case.
old="""function dateLabel(v){if(!v)return {d:'--',m:'Sin fecha'};const d=new Date(v+'T12:00:00');return {d:String(d.getDate()).padStart(2,'0'),m:d.toLocaleDateString('es-AR',{month:'short',weekday:'short'}).replace('.','')}}
function mapsUrl(b){"""
new="""function dateLabel(v){if(!v)return {d:'--',m:'Sin fecha'};const d=new Date(v+'T12:00:00');return {d:String(d.getDate()).padStart(2,'0'),m:d.toLocaleDateString('es-AR',{month:'short',weekday:'short'}).replace('.','')}}
function titleCaseTeam(value){return String(value||'').trim().toLocaleLowerCase('es-AR').replace(/(^|[\\s\\-\\/])([a-záéíóúüñ])/g,(m,sep,ch)=>sep+ch.toLocaleUpperCase('es-AR'))}
function normalizeBookingTeams(data){return {...data,home:titleCaseTeam(data.home),away:titleCaseTeam(data.away)}}
function mapsUrl(b){"""
once(old,new,'titlecase helpers')

old="""async function submitClient(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget).entries());const msg=$('#msg');msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';try{await saveBooking(currentDraft.id,{...data,status:'confirmado',confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado'})}catch(err){msg.innerHTML='<div class=\"notice err\">No pude guardar la confirmación. Revisá tu conexión y volvé a intentar.</div>'}}"""
new="""async function submitClient(e){e.preventDefault();const data=normalizeBookingTeams(Object.fromEntries(new FormData(e.currentTarget).entries()));const msg=$('#msg');msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';try{await saveBooking(currentDraft.id,{...data,status:'confirmado',confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado'})}catch(err){msg.innerHTML='<div class=\"notice err\">No pude guardar la confirmación. Revisá tu conexión y volvé a intentar.</div>'}}"""
once(old,new,'normalize public submission')

# Render names normalized even for old records.
s=s.replace("${esc(b.home)} vs ${esc(b.away)}","${esc(titleCaseTeam(b.home))} vs ${esc(titleCaseTeam(b.away))}")
s=s.replace("${esc(b.home||'Equipo local')} <span style=\"color:#64748b\">vs</span> ${esc(b.away||'Equipo visitante')}","${esc(titleCaseTeam(b.home)||'Equipo Local')} <span style=\"color:#64748b\">vs</span> ${esc(titleCaseTeam(b.away)||'Equipo Visitante')}")

# Edit button inside every agenda card.
old="""<div class=\"booking-actions\">${maps}<button class=\"btn small ghost copy\" data-id=\"${esc(b.id)}\">Copiar link</button>"""
new="""<div class=\"booking-actions\">${maps}<button class=\"btn small ghost edit\" data-id=\"${esc(b.id)}\">✏️ Editar</button><button class=\"btn small ghost copy\" data-id=\"${esc(b.id)}\">Copiar link</button>"""
once(old,new,'edit button')

# Wire edit button.
old="""function wireBookingButtons(){document.querySelectorAll('.copy').forEach(btn=>btn.onclick=async()=>{await navigator.clipboard.writeText(publicLink(btn.dataset.id));btn.textContent='Link copiado ✓';setTimeout(()=>btn.textContent='Copiar link',1300)});"""
new="""function wireBookingButtons(){document.querySelectorAll('.edit').forEach(btn=>btn.onclick=()=>openEditBooking(btn.dataset.id));document.querySelectorAll('.copy').forEach(btn=>btn.onclick=async()=>{await navigator.clipboard.writeText(publicLink(btn.dataset.id));btn.textContent='Link copiado ✓';setTimeout(()=>btn.textContent='Copiar link',1300)});"""
once(old,new,'wire edit')

# Insert full edit modal before openNew.
anchor="""function openNew(){const modal=document.createElement('div');"""
edit_fn="""async function openEditBooking(id){
 const b=await loadOne(id);if(!b){alert('No pude encontrar esta contratación.');return}
 const modal=document.createElement('div');
 modal.style='position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:120;display:grid;place-items:center;padding:14px';
 modal.innerHTML=`<div class=\"card\" style=\"width:min(720px,100%);max-height:94vh;overflow:auto;position:relative\"><button type=\"button\" id=\"closeEditX\" aria-label=\"Cerrar\" style=\"position:absolute;right:14px;top:12px;width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.12);background:#16181d;color:#fff;font-size:20px;cursor:pointer\">×</button><div class=\"eyebrow\">Editar contratación</div><h3 style=\"font-size:26px;margin:8px 46px 5px 0\">${esc(titleCaseTeam(b.home)||'Equipo Local')} vs ${esc(titleCaseTeam(b.away)||'Equipo Visitante')}</h3><p class=\"copy\">Modificá cualquier dato de la agenda y guardalo. Los nombres de equipos se acomodan automáticamente.</p><form id=\"editBookingForm\" class=\"formgrid\" style=\"margin-top:17px\"><div class=\"field\"><label>Fecha</label><input class=\"input\" type=\"date\" name=\"date\" value=\"${esc(b.date||'')}\"></div><div class=\"field\"><label>Estado</label><select class=\"input\" name=\"status\"><option value=\"pendiente\" ${b.status==='pendiente'?'selected':''}>Pendiente</option><option value=\"confirmado\" ${b.status==='confirmado'?'selected':''}>Confirmado</option><option value=\"realizado\" ${b.status==='realizado'?'selected':''}>Realizado</option><option value=\"cancelado\" ${b.status==='cancelado'?'selected':''}>Cancelado</option></select></div><div class=\"field\"><label>Equipo local</label><input required class=\"input\" name=\"home\" value=\"${esc(titleCaseTeam(b.home))}\"></div><div class=\"field\"><label>Equipo visitante</label><input required class=\"input\" name=\"away\" value=\"${esc(titleCaseTeam(b.away))}\"></div><div class=\"field\"><label>Categoría</label><select class=\"input\" name=\"category\">${categoryOptions(b.category)}</select></div><div class=\"field\"><label>Pago acordado</label><input class=\"input\" type=\"number\" min=\"0\" name=\"payment\" value=\"${esc(b.payment||0)}\"></div><div class=\"field\"><label>Horario del partido</label><input class=\"input\" type=\"time\" name=\"matchTime\" value=\"${esc(b.matchTime||'')}\"></div><div class=\"field\"><label>Hora de llegada</label><input class=\"input\" type=\"time\" name=\"arrivalTime\" value=\"${esc(b.arrivalTime||'')}\"></div><div class=\"field\"><label>Cancha / estadio</label><input class=\"input\" name=\"venue\" value=\"${esc(b.venue||'')}\"></div><div class=\"field\"><label>Cliente</label><input class=\"input\" name=\"clientName\" value=\"${esc(b.clientName||'')}\"></div><div class=\"field full\"><label>Dirección</label><input class=\"input\" name=\"address\" value=\"${esc(b.address||'')}\"></div><div class=\"field\"><label>WhatsApp / teléfono</label><input class=\"input\" inputmode=\"tel\" name=\"phone\" value=\"${esc(b.phone||'')}\"></div><div class=\"field\"><label>Nota privada</label><input class=\"input\" name=\"adminNote\" value=\"${esc(b.adminNote||'')}\"></div><div class=\"field full\"><label>Observaciones</label><textarea class=\"input\" rows=\"3\" name=\"notes\">${esc(b.notes||'')}</textarea></div><div class=\"field full\"><div class=\"actions\"><button class=\"btn primary\" type=\"submit\">Guardar cambios</button><button class=\"btn ghost\" type=\"button\" id=\"closeEdit\">Cancelar</button></div><div id=\"editMsg\"></div></div></form></div>`;
 document.body.appendChild(modal);
 const close=()=>modal.remove();$('#closeEdit').onclick=close;$('#closeEditX').onclick=close;modal.onclick=e=>{if(e.target===modal)close()};
 $('#editBookingForm').onsubmit=async e=>{e.preventDefault();const msg=$('#editMsg');msg.innerHTML='<div class=\"notice info\">Guardando cambios…</div>';try{const raw=Object.fromEntries(new FormData(e.currentTarget).entries());const data=normalizeBookingTeams({...raw,payment:Number(raw.payment||0)});await saveBooking(id,data);msg.innerHTML='<div class=\"notice ok\">Cambios guardados ✓</div>';await renderAdminList($('#search')?$('#search').value:'');setTimeout(close,350)}catch(err){console.error(err);msg.innerHTML='<div class=\"notice err\">No pude guardar los cambios. Revisá la conexión.</div>'}};
}
function openNew(){const modal=document.createElement('div');"""
once(anchor,edit_fn,'edit modal')

# Normalize story export and calendar/detail text display too.
s=s.replace("const match=`${b.home||'Equipo local'} vs ${b.away||'Equipo visitante'}`;","const match=`${titleCaseTeam(b.home)||'Equipo Local'} vs ${titleCaseTeam(b.away)||'Equipo Visitante'}`;")
s=s.replace("Partido: ${b.home||''} vs ${b.away||''}","Partido: ${titleCaseTeam(b.home)||''} vs ${titleCaseTeam(b.away)||''}")

p.write_text(s,encoding='utf-8')
print('v93 edit bookings + title case patched')
