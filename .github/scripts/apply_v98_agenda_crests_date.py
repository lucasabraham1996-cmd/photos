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

# Responsive visual treatment for agenda cards.
css=r'''
    /* v98: escudos en agenda + fecha DOM / 06 / SEP */
    .datebox{min-height:112px!important;padding:10px 8px!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;gap:4px!important}
    .datebox .dow{font-size:10px;line-height:1;font-weight:900;letter-spacing:.12em;color:#dbeafe;text-transform:uppercase}
    .datebox .d{font-size:31px!important;line-height:.95!important;font-weight:1000!important;color:#fff}
    .datebox .mon{font-size:11px;line-height:1;font-weight:900;letter-spacing:.12em;color:#93c5fd;text-transform:uppercase}
    .booking-main{min-width:0}
    .booking-versus{display:grid!important;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:10px;margin-bottom:8px!important;min-width:0}
    .booking-team{display:flex;align-items:center;gap:9px;min-width:0}
    .booking-team.home{justify-content:flex-end;text-align:right}.booking-team.away{justify-content:flex-start;text-align:left}
    .booking-team-name{font-size:18px;line-height:1.05;font-weight:900;min-width:0;overflow-wrap:anywhere}
    .booking-vs{font-size:12px!important;color:#64748b!important;text-transform:uppercase;letter-spacing:.08em;font-weight:900}
    .booking-team-logo{position:relative;width:40px;height:40px;flex:0 0 40px;display:grid;place-items:center;background:transparent;border:0;overflow:visible}
    .booking-team-logo img{position:absolute;inset:1px;width:calc(100% - 2px);height:calc(100% - 2px);object-fit:contain;background:transparent;filter:drop-shadow(0 3px 5px rgba(0,0,0,.45));z-index:2}
    .booking-team-logo-fallback{font-size:9px;line-height:1;font-weight:900;color:#64748b;text-align:center}
    @media(max-width:860px){.booking-versus{gap:7px}.booking-team-logo{width:36px;height:36px;flex-basis:36px}.booking-team-name{font-size:16px}}
    @media(max-width:520px){.datebox{min-height:104px!important;padding:8px 5px!important}.datebox .dow{font-size:8px}.datebox .d{font-size:25px!important}.datebox .mon{font-size:9px}.booking-versus{gap:5px}.booking-team{gap:5px}.booking-team-logo{width:31px;height:31px;flex-basis:31px}.booking-team-name{font-size:14px}.booking-vs{font-size:10px!important}}
'''
once('  </style>',css+'  </style>','agenda css')

old="function dateLabel(v){if(!v)return {d:'--',m:'Sin fecha'};const d=new Date(v+'T12:00:00');return {d:String(d.getDate()).padStart(2,'0'),m:d.toLocaleDateString('es-AR',{month:'short',weekday:'short'}).replace('.','')}}"
new=r'''function dateLabel(v){if(!v)return {d:'--',mon:'---',dow:'---'};const d=new Date(v+'T12:00:00');const mons=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];const days=['DOM','LUN','MAR','MIÉ','JUE','VIE','SÁB'];return {d:String(d.getDate()).padStart(2,'0'),mon:mons[d.getMonth()],dow:days[d.getDay()]}}
function normalizeTeamKey(v){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es-AR').replace(/[^a-z0-9]+/g,' ').trim()}
function findLcfTeam(name){const key=normalizeTeamKey(name);if(!key)return null;const aliases={'all boys de cordoba':'all boys','club atletico all boys':'all boys','racing cordoba':'racing de cordoba','independiente carlos paz':'independiente de carlos paz','atletico carlos paz':'atletico carlos paz','defensores central cordoba':'defensores central cordoba','union san vicente':'union san vicente','villa siburu':'villa siburu'};const wanted=aliases[key]||key;return LCF_TEAMS.find(t=>normalizeTeamKey(t.name)===wanted)||LCF_TEAMS.find(t=>{const k=normalizeTeamKey(t.name);return wanted.length>5&&(k.includes(wanted)||wanted.includes(k))})||null}
function bookingTeamLogoHtml(name){const team=findLcfTeam(name);const src=team&&team.logo?esc(team.logo):'';return `<span class="booking-team-logo"><span class="booking-team-logo-fallback">${esc(teamInitials(name))}</span>${src?`<img src="${src}" alt="Escudo ${esc(team.name)}" loading="lazy" onerror="this.style.display='none'">`:''}</span>`}'''
once(old,new,'date and team helpers')

pattern=r"function bookingCard\(b\)\{.*?\}\n\nfunction publicLink"
replacement=r'''function bookingCard(b){
  const dl=dateLabel(b.date);
  const maps=b.address||b.venue?`<button class="btn small green maps" data-id="${esc(b.id)}">📍 Maps</button>`:'';
  const safeStatus=['pendiente','confirmado','realizado','cancelado'].includes(b.status)?b.status:'pendiente';
  const home=titleWords(b.home)||'Equipo Local';
  const away=titleWords(b.away)||'Equipo Visitante';
  return `<article class="booking status-${esc(safeStatus)}" data-id="${esc(b.id)}" data-status="${esc(safeStatus)}"><div class="datebox"><div class="dow">${esc(dl.dow)}</div><div class="d">${esc(dl.d)}</div><div class="mon">${esc(dl.mon)}</div></div><div class="booking-main"><div class="versus booking-versus"><span class="booking-team home">${bookingTeamLogoHtml(home)}<span class="booking-team-name">${esc(home)}</span></span><span class="booking-vs">vs</span><span class="booking-team away">${bookingTeamLogoHtml(away)}<span class="booking-team-name">${esc(away)}</span></span></div><div class="meta"><span>⚽ Categoría <strong>${esc(b.category||'Pendiente')}</strong></span><span>🏟️ <strong>${esc(b.venue||'Cancha pendiente')}</strong></span><span>📍 <strong>${esc(b.address||'Dirección pendiente')}</strong></span><span>📸 Llegar <strong>${esc(b.arrivalTime||'--:--')}</strong></span><span>⚽ Partido <strong>${esc(b.matchTime||'--:--')}</strong></span><span>🏁 Finaliza <strong>${esc(b.endTime||'--:--')}</strong></span><span>📋 <strong>${esc(bookingServiceName(b))}</strong></span><span>💰 <strong>${money(b.payment)}</strong></span><span>👤 <strong>${esc(b.clientName||'Sin confirmar')}</strong></span></div><div style="margin-top:8px"><span class="status ${esc(b.status||'pendiente')}">${esc(b.status||'pendiente')}</span> <span class="muted">${esc(b.id)}</span></div></div><div class="booking-actions">${maps}<button class="btn small ghost editBooking" data-id="${esc(b.id)}">✏️ Editar</button><button class="btn small red deleteBooking" data-id="${esc(b.id)}">🗑 Eliminar</button><button class="btn small ghost copy" data-id="${esc(b.id)}">Copiar link</button><button class="btn small primary cal" data-id="${esc(b.id)}">Google Calendar</button><button class="btn small ghost ics" data-id="${esc(b.id)}">.ics</button><select class="input statusSel" data-id="${esc(b.id)}" style="padding:8px 10px;width:auto"><option ${b.status==='pendiente'?'selected':''}>pendiente</option><option ${b.status==='confirmado'?'selected':''}>confirmado</option><option ${b.status==='realizado'?'selected':''}>realizado</option><option ${b.status==='cancelado'?'selected':''}>cancelado</option></select></div></article>`
}

function publicLink'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'bookingCard replacement: {n}')

story_pattern=r"function storyStatus\(status\)\{.*?\}\nfunction drawStoryPage\(items,page,totalPages\)\{.*?\}\nasync function downloadAgendaStory"
story_new=r'''function storyStatus(status){return status==='confirmado'?['#463311','#fde68a']:status==='realizado'?['#123a25','#86efac']:status==='cancelado'?['#431b1b','#fecaca']:['#142d50','#bfdbfe']}
function loadStoryCrest(name){return new Promise(resolve=>{const team=findLcfTeam(name);if(!team||!team.logo)return resolve(null);const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>resolve(null);img.src=team.logo})}
function drawStoryCrest(ctx,img,name,x,y,size){if(img){ctx.save();ctx.shadowColor='rgba(0,0,0,.38)';ctx.shadowBlur=8;ctx.drawImage(img,x,y,size,size);ctx.restore();return}ctx.fillStyle='rgba(255,255,255,.08)';ctx.beginPath();ctx.arc(x+size/2,y+size/2,size/2,0,Math.PI*2);ctx.fill();ctx.fillStyle='#94a3b8';ctx.font=`900 ${Math.max(10,Math.floor(size*.24))}px Inter, Arial`;ctx.textAlign='center';ctx.fillText(teamInitials(name),x+size/2,y+size*.62);ctx.textAlign='left'}
async function drawStoryPage(items,page,totalPages){
  const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1920;const ctx=canvas.getContext('2d');
  const bg=ctx.createLinearGradient(0,0,1080,1920);bg.addColorStop(0,'#111d3a');bg.addColorStop(.38,'#070b13');bg.addColorStop(1,'#030406');ctx.fillStyle=bg;ctx.fillRect(0,0,1080,1920);
  const glow=ctx.createRadialGradient(900,80,10,900,80,560);glow.addColorStop(0,'rgba(37,99,235,.42)');glow.addColorStop(1,'rgba(37,99,235,0)');ctx.fillStyle=glow;ctx.fillRect(0,0,1080,720);
  ctx.fillStyle='#7dd3fc';ctx.font='800 25px Inter, Arial';ctx.fillText('LUCASABRAHAM.PH · FOTOGRAFÍA DEPORTIVA',72,108);ctx.fillStyle='#ffffff';ctx.font='900 72px Inter, Arial';ctx.fillText('AGENDA DE',72,190);ctx.fillText('COBERTURAS',72,270);ctx.fillStyle='#9ca3af';ctx.font='600 25px Inter, Arial';const now=new Date();ctx.fillText(`Actualizada ${now.toLocaleDateString('es-AR')} · ${items.length?items.length:'Sin'} cobertura${items.length===1?'':'s'} en esta historia`,74,322);
  if(totalPages>1){roundedRect(ctx,870,86,138,54,27,'rgba(255,255,255,.08)','rgba(255,255,255,.13)');ctx.fillStyle='#fff';ctx.font='800 22px Inter, Arial';ctx.textAlign='center';ctx.fillText(`${page}/${totalPages}`,939,121);ctx.textAlign='left'}
  let y=382;const h=166,gap=18;
  for(const b of items){
    roundedRect(ctx,64,y,952,h,30,'rgba(10,14,24,.93)','rgba(255,255,255,.11)');roundedRect(ctx,84,y+22,118,122,25,'rgba(37,99,235,.18)','rgba(96,165,250,.28)');
    const dl=dateLabel(b.date);ctx.textAlign='center';ctx.fillStyle='#dbeafe';ctx.font='900 15px Inter, Arial';ctx.fillText(dl.dow,143,y+48);ctx.fillStyle='#fff';ctx.font='900 45px Inter, Arial';ctx.fillText(dl.d,143,y+91);ctx.fillStyle='#93c5fd';ctx.font='900 18px Inter, Arial';ctx.fillText(dl.mon,143,y+123);ctx.textAlign='left';
    ctx.fillStyle='#93c5fd';ctx.font='800 18px Inter, Arial';ctx.fillText((b.category||'Categoría pendiente').toUpperCase(),228,y+36);
    const home=b.home||'Equipo local',away=b.away||'Equipo visitante';const [homeImg,awayImg]=await Promise.all([loadStoryCrest(home),loadStoryCrest(away)]);drawStoryCrest(ctx,homeImg,home,228,y+49,38);drawStoryCrest(ctx,awayImg,away,274,y+49,38);
    const match=`${home} vs ${away}`;const fs=fitText(ctx,match,470,30,19,900);ctx.fillStyle='#fff';ctx.font=`900 ${fs}px Inter, Arial`;ctx.fillText(match,326,y+77);
    ctx.fillStyle='#aab2bf';ctx.font='600 19px Inter, Arial';const venue=(b.venue||'Cancha pendiente').slice(0,58);ctx.fillText(`🏟 ${venue}`,228,y+111);ctx.fillText(`📸 Llegar ${b.arrivalTime||'--:--'}   ·   ⚽ Partido ${b.matchTime||'--:--'}`,228,y+141);
    const [sb,st]=storyStatus(b.status||'pendiente');roundedRect(ctx,835,y+24,151,42,21,sb,null);ctx.fillStyle=st;ctx.font='800 16px Inter, Arial';ctx.textAlign='center';ctx.fillText((b.status||'pendiente').toUpperCase(),910,y+51);ctx.textAlign='left';y+=h+gap;
  }
  ctx.fillStyle='#64748b';ctx.font='600 20px Inter, Arial';ctx.fillText('Organización de coberturas · lucasabraham.ph',72,1848);return canvas
}
async function downloadAgendaStory'''
s,n=re.subn(story_pattern,story_new,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'story replacement: {n}')

once('const canvas=drawStoryPage(pageItems,i+1,totalPages);','const canvas=await drawStoryPage(pageItems,i+1,totalPages);','await story canvas')

p.write_text(s,encoding='utf-8')
print('v98 agenda crests and date patched')
