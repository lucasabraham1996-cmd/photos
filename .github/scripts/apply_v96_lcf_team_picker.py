from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 got {n}')
    s=s.replace(old,new,1)

# Add visual team picker styles before </style>.
css=r'''
    /* v96: selector visual de clubes Liga Cordobesa */
    .team-field{position:relative;min-width:0}
    .team-picker-trigger{width:100%;min-height:58px;border:1px solid rgba(255,255,255,.12);background:#080a0f;color:#fff;border-radius:15px;padding:8px 12px;display:flex;align-items:center;gap:11px;cursor:pointer;text-align:left;transition:.2s}
    .team-picker-trigger:hover,.team-picker-trigger.open{border-color:rgba(56,189,248,.62);box-shadow:0 0 0 3px rgba(56,189,248,.09)}
    .team-picker-crest,.team-option-crest{position:relative;display:grid;place-items:center;flex:0 0 auto;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);overflow:hidden}
    .team-picker-crest{width:42px;height:42px;border-radius:12px}.team-option-crest{width:38px;height:38px;border-radius:10px}
    .team-picker-crest img,.team-option-crest img{position:absolute;inset:4px;width:calc(100% - 8px);height:calc(100% - 8px);object-fit:contain;z-index:2}
    .team-crest-fallback{font-size:10px;font-weight:900;color:#94a3b8;letter-spacing:-.03em;text-align:center;line-height:1}
    .team-picker-copy{min-width:0;flex:1}.team-picker-copy b{display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.team-picker-copy small{display:block;color:#7dd3fc;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-top:2px}
    .team-picker-chevron{color:#64748b;font-size:12px}
    .team-picker-menu{position:absolute;z-index:80;top:calc(100% + 7px);left:0;width:min(430px,calc(100vw - 36px));max-height:430px;overflow:auto;padding:10px;background:rgba(7,9,14,.99);border:1px solid rgba(125,211,252,.23);border-radius:18px;box-shadow:0 24px 70px rgba(0,0,0,.58)}
    .team-field.away-picker .team-picker-menu{left:auto;right:0}
    .team-picker-search{position:sticky;top:0;z-index:2;width:100%;height:44px;background:#0c1018;border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;padding:0 12px;outline:none;margin-bottom:8px;font-size:16px}
    .team-picker-group{padding:7px 6px 5px;font-size:9px;color:#7dd3fc;font-weight:900;text-transform:uppercase;letter-spacing:.16em}
    .team-option{width:100%;border:0;background:transparent;color:#fff;border-radius:12px;padding:7px;display:flex;align-items:center;gap:10px;text-align:left;cursor:pointer;min-height:50px}
    .team-option:hover,.team-option:focus{background:rgba(56,189,248,.11);outline:none}.team-option b{font-size:12px;line-height:1.15}.team-option small{display:block;color:#7b8493;font-size:9px;margin-top:3px}
    .team-option.other-team{margin-top:7px;border:1px dashed rgba(125,211,252,.28);background:rgba(56,189,248,.06)}
    .team-other-input{margin-top:7px}.team-picker-empty{padding:18px 8px;text-align:center;color:#747b88;font-size:11px}
    @media(max-width:640px){.team-picker-menu{position:fixed;left:12px!important;right:12px!important;top:78px;width:auto;max-height:calc(100vh - 100px);border-radius:20px}.team-picker-trigger{min-height:60px}.team-picker-crest{width:44px;height:44px}}
'''
once('  </style>',css+'  </style>','picker css')

# Dataset and helpers after CATEGORIES.
needle="const CATEGORIES=['Primera','Reserva','4ta','5ta','6ta','7ma','9na','10ma','11ra','12da'];\n"
teams=r'''const LCF_TEAMS=[
  {name:'General Paz Juniors',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72gralpaz.gif'},
  {name:'Camioneros Córdoba',division:'Primera A',logo:'https://www.estadiosdeargentina.com.ar/wp-content/uploads/2022/10/club-camioneros-cordoba.jpg'},
  {name:'Deportivo Lasallano',division:'Primera A',logo:'https://i.pinimg.com/736x/98/aa/9d/98aa9dc82fac2d73df8df8f4a1140e00.jpg'},
  {name:'Argentino Peñarol',division:'Primera A',logo:'https://images.seeklogo.com/logo-png/32/1/argentino-penarol-de-cordoba-logo-png_seeklogo-328791.png'},
  {name:'Villa Azalais',division:'Primera A',logo:'https://logowik.com/content/uploads/images/club-social-deportivo-villa-azalais-de-villa-azalais-cordoba1723104177.logowik.com.webp'},
  {name:'Escuela Presidente Roca',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72pteroca.gif'},
  {name:'CIBI',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72cibi.gif'},
  {name:'Huracán',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72huracan2.gif'},
  {name:'Libertad',division:'Primera A',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/10/libertad-cordoba.png'},
  {name:'Instituto',division:'Primera A',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Escudo_Instituto_Atletico_Central_Cordoba.png/960px-Escudo_Instituto_Atletico_Central_Cordoba.png'},
  {name:'Unión San Vicente',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionsanvicente.gif'},
  {name:'Universitario',division:'Primera A',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Universitario_cba_logo.svg/829px-Universitario_cba_logo.svg.png'},
  {name:'AMSURRBAC',division:'Primera A',logo:'https://images.seeklogo.com/logo-png/40/1/club-atletico-amsurrbac-de-cordoba-logo-png_seeklogo-403870.png'},
  {name:'Las Palmas',division:'Primera A',logo:'https://interiorfutbolero.com.ar/wp-content/uploads/2019/02/Las-Palmas.png'},
  {name:'Racing de Córdoba',division:'Primera A',logo:'https://www.ogol.com.br/img/logos/equipas/9677_imgbank_1686735991.png'},
  {name:'Los Andes',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72losandes2.gif'},
  {name:'Belgrano',division:'Primera A',logo:'https://www.pngfind.com/pngs/m/308-3083133_humo-de-mercado-on-twitter-escudo-belgrano.png'},
  {name:'San Lorenzo',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72sanlorenzo.gif'},
  {name:'Talleres',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72talleres.gif'},
  {name:'Deportivo Atalaya',division:'Primera A',logo:'https://i.pinimg.com/736x/38/14/5f/38145fe9673e2b562cd4a59a2f46d2b9.jpg'},
  {name:'Barrio Parque',division:'Primera A',logo:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Barrio%20Parque.jpg?width=256'},
  {name:'Bella Vista',division:'Primera A',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72bellavista.gif'},
  {name:'Almirante Brown',division:'Primera B',logo:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Almirante%20Brown%20Malague%C3%B1o.png?width=256'},
  {name:'Atlético Carlos Paz',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/76carlospaz.gif'},
  {name:'Avellaneda',division:'Primera B',logo:'https://interiorfutbolero.com.ar/wp-content/uploads/2021/11/pixlr-bg-result.png'},
  {name:'Deportivo Banfield',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72banfield.gif'},
  {name:'Deportivo Norte',division:'Primera B',logo:'https://seeklogo.com/images/A/asociacion-deportiva-norte-de-alta-gracia-cordoba-logo-9A38FA221D-seeklogo.com.png'},
  {name:'Independiente de Carlos Paz',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72independiente.gif'},
  {name:'Juvenil Barrio Comercial',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72comercial.gif'},
  {name:'Las Flores',division:'Primera B',logo:'https://i.pinimg.com/originals/a9/cd/8f/a9cd8f949afbe1d87430e7e35dab6fb8.png'},
  {name:'Quilmes',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72quilmes.gif'},
  {name:'San Nicolás',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72sannicolas.gif'},
  {name:'All Boys',division:'Primera B',logo:'https://www.allboyscba.com/inferiores/img/escudos/ALL%20BOYS.png'},
  {name:'Calera Central',division:'Primera B',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2025/05/caleta-central-la-calera-cordoba.png'},
  {name:'Defensores Central Córdoba',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72defcentralcordoba.gif'},
  {name:'Defensores Juveniles',division:'Primera B',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/10/defensores-juveniles-cordoba.png'},
  {name:'Deportivo Alberdi',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72alberdi.gif'},
  {name:'El Carmen',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72elcarmen.gif'},
  {name:'La Unión',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionmalvinas.gif'},
  {name:'MEDEA',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72medea.gif'},
  {name:'Unión Florida',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionflorida.gif'},
  {name:'Villa Siburú',division:'Primera B',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72villasirburu.gif'}
];
function teamInitials(name){return String(name||'?').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'?'}
function teamLogoHtml(team,cls='team-option-crest'){const src=team&&team.logo?esc(team.logo):'';const initials=teamInitials(team&&team.name);return `<span class="${cls}"><span class="team-crest-fallback">${esc(initials)}</span>${src?`<img src="${src}" alt="Escudo ${esc(team.name)}" loading="lazy" onerror="this.style.display='none'">`:''}</span>`}
function teamPickerMarkup(field,label,selected=''){
  const current=LCF_TEAMS.find(t=>t.name.toLocaleLowerCase('es-AR')===String(selected||'').trim().toLocaleLowerCase('es-AR'))||null;
  const other=Boolean(selected&&!current);
  const groups=['Primera A','Primera B'].map(div=>`<div class="team-picker-group">${div}</div>${LCF_TEAMS.filter(t=>t.division===div).map(t=>`<button type="button" class="team-option" data-team-name="${esc(t.name)}" data-team-division="${esc(t.division)}" data-team-logo="${esc(t.logo)}">${teamLogoHtml(t)}<span><b>${esc(t.name)}</b><small>${esc(t.division)}</small></span></button>`).join('')}`).join('');
  const display=current?current.name:(other?titleWords(selected):'Elegí un equipo');
  const div=current?current.division:(other?'Otro equipo':'Primera A · Primera B');
  const team=current||{name:display,logo:''};
  return `<div class="field team-field ${field==='away'?'away-picker':''}" data-team-picker="${field}"><label>${label}</label><input type="hidden" name="${field}" value="${esc(selected||'')}"><button type="button" class="team-picker-trigger" aria-expanded="false">${teamLogoHtml(team,'team-picker-crest')}<span class="team-picker-copy"><b>${esc(display)}</b><small>${esc(div)}</small></span><span class="team-picker-chevron">⌄</span></button><div class="team-picker-menu hidden"><input type="search" class="team-picker-search" placeholder="Buscar equipo…" autocomplete="off"><div class="team-picker-options">${groups}<button type="button" class="team-option other-team" data-team-name="__other__"><span class="team-option-crest"><span class="team-crest-fallback">+</span></span><span><b>Otro equipo</b><small>Escribir manualmente</small></span></button><div class="team-picker-empty hidden">No encontré equipos con ese nombre.</div></div></div><input class="input team-other-input ${other?'':'hidden'}" data-team-other="${field}" placeholder="Escribí el nombre del equipo" value="${other?esc(titleWords(selected)):''}"></div>`;
}
function setTeamPicker(root,name,division='',logo=''){
  const hidden=root.querySelector('input[type="hidden"]'); const copy=root.querySelector('.team-picker-copy'); const crest=root.querySelector('.team-picker-crest'); const other=root.querySelector('.team-other-input');
  hidden.value=name||''; copy.querySelector('b').textContent=name||'Elegí un equipo'; copy.querySelector('small').textContent=division||'Primera A · Primera B';
  crest.innerHTML=`<span class="team-crest-fallback">${teamInitials(name||'?')}</span>${logo?`<img src="${logo}" alt="Escudo ${esc(name)}" onerror="this.style.display='none'">`:''}`;
  if(name!=='__other__'&&division!=='Otro equipo') other.classList.add('hidden');
}
function initTeamPickers(){
  const roots=[...document.querySelectorAll('[data-team-picker]')];
  const closeAll=except=>roots.forEach(r=>{if(r!==except){r.querySelector('.team-picker-menu').classList.add('hidden');r.querySelector('.team-picker-trigger').classList.remove('open');r.querySelector('.team-picker-trigger').setAttribute('aria-expanded','false')}});
  roots.forEach(root=>{
    const trigger=root.querySelector('.team-picker-trigger'),menu=root.querySelector('.team-picker-menu'),search=root.querySelector('.team-picker-search'),hidden=root.querySelector('input[type="hidden"]'),other=root.querySelector('.team-other-input');
    trigger.onclick=e=>{e.stopPropagation();const opening=menu.classList.contains('hidden');closeAll(root);menu.classList.toggle('hidden',!opening);trigger.classList.toggle('open',opening);trigger.setAttribute('aria-expanded',String(opening));if(opening)setTimeout(()=>search.focus(),30)};
    root.querySelectorAll('.team-option').forEach(btn=>btn.onclick=()=>{const name=btn.dataset.teamName;if(name==='__other__'){hidden.value=other.value||'';setTeamPicker(root,titleWords(other.value)||'Otro equipo','Otro equipo','');other.classList.remove('hidden');setTimeout(()=>other.focus(),30)}else{setTeamPicker(root,name,btn.dataset.teamDivision||'',btn.dataset.teamLogo||'')}menu.classList.add('hidden');trigger.classList.remove('open');trigger.setAttribute('aria-expanded','false')});
    other.oninput=()=>{hidden.value=titleWords(other.value);root.querySelector('.team-picker-copy b').textContent=hidden.value||'Otro equipo'};
    other.onblur=()=>{other.value=titleWords(other.value);hidden.value=other.value};
    search.oninput=()=>{const q=search.value.trim().toLocaleLowerCase('es-AR');let visible=0;root.querySelectorAll('.team-option:not(.other-team)').forEach(btn=>{const ok=!q||btn.dataset.teamName.toLocaleLowerCase('es-AR').includes(q);btn.classList.toggle('hidden',!ok);if(ok)visible++});root.querySelectorAll('.team-picker-group').forEach(g=>{let n=g.nextElementSibling,has=false;while(n&&!n.classList.contains('team-picker-group')&&!n.classList.contains('other-team')){if(n.classList.contains('team-option')&&!n.classList.contains('hidden'))has=true;n=n.nextElementSibling}g.classList.toggle('hidden',!has)});root.querySelector('.team-picker-empty').classList.toggle('hidden',visible>0)};
  });
  document.addEventListener('click',()=>closeAll(null),{once:true});
}
'''
once(needle,needle+teams,'team dataset')

old='''<div class="field"><label>Equipo local</label><input required class="input" name="home" placeholder="Ej: All Boys" value="${esc(b.home)}"></div><div class="field"><label>Equipo visitante</label><input required class="input" name="away" placeholder="Ej: Las Palmas" value="${esc(b.away)}"></div>'''
new='''${teamPickerMarkup('home','Equipo local',b.home)}${teamPickerMarkup('away','Equipo visitante',b.away)}'''
once(old,new,'public team inputs')

old="`);$('#clientForm').onsubmit=submitClient}"
new="`);initTeamPickers();$('#clientForm').onsubmit=submitClient}"
once(old,new,'init pickers')

old="async function submitClient(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget).entries());data.home=titleWords(data.home);data.away=titleWords(data.away);const msg=$('#msg');msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';"
new="async function submitClient(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget).entries());data.home=titleWords(data.home);data.away=titleWords(data.away);const msg=$('#msg');if(!data.home||!data.away){msg.innerHTML='<div class=\"notice err\">Elegí el equipo local y el visitante. Si no aparece, usá “Otro equipo”.</div>';return}msg.innerHTML='<div class=\"notice info\">Guardando confirmación…</div>';"
once(old,new,'team validation')

p.write_text(s,encoding='utf-8')
print('v96 LCF team picker patched')
