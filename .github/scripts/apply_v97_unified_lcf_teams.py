from pathlib import Path
import re
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

# Visual: no white cards behind crests, one continuous list.
s=s.replace(".team-picker-crest,.team-option-crest{position:relative;display:grid;place-items:center;flex:0 0 auto;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);overflow:hidden}",".team-picker-crest,.team-option-crest{position:relative;display:grid;place-items:center;flex:0 0 auto;background:transparent;border:0;overflow:hidden}")
s=s.replace(".team-picker-crest img,.team-option-crest img{position:absolute;inset:4px;width:calc(100% - 8px);height:calc(100% - 8px);object-fit:contain;z-index:2}",".team-picker-crest img,.team-option-crest img{position:absolute;inset:2px;width:calc(100% - 4px);height:calc(100% - 4px);object-fit:contain;z-index:2;background:transparent;filter:drop-shadow(0 2px 4px rgba(0,0,0,.35))}")
s=s.replace(".team-picker-group{padding:7px 6px 5px;font-size:9px;color:#7dd3fc;font-weight:900;text-transform:uppercase;letter-spacing:.16em}\n","")

teams="""const LCF_TEAMS=[
  {name:'All Boys',logo:'https://www.allboyscba.com/inferiores/img/escudos/ALL%20BOYS.png'},
  {name:'Almirante Brown',logo:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Almirante%20Brown%20Malague%C3%B1o.png?width=512'},
  {name:'AMSURRBAC',logo:'https://images.seeklogo.com/logo-png/40/1/club-atletico-amsurrbac-de-cordoba-logo-png_seeklogo-403870.png'},
  {name:'Argentino Peñarol',logo:'https://images.seeklogo.com/logo-png/32/1/argentino-penarol-de-cordoba-logo-png_seeklogo-328791.png'},
  {name:'Atlético Carlos Paz',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/76carlospaz.gif'},
  {name:'Avellaneda',logo:'https://interiorfutbolero.com.ar/wp-content/uploads/2021/11/pixlr-bg-result.png'},
  {name:'Barrio Parque',logo:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Barrio%20Parque.jpg?width=256'},
  {name:'Belgrano',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Escudo_Oficial_del_Club_Atl%C3%A9tico_Belgrano.png/512px-Escudo_Oficial_del_Club_Atl%C3%A9tico_Belgrano.png'},
  {name:'Bella Vista',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72bellavista.gif'},
  {name:'Calera Central',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2025/05/caleta-central-la-calera-cordoba.png'},
  {name:'Camioneros Córdoba',logo:'https://www.estadiosdeargentina.com.ar/wp-content/uploads/2022/10/club-camioneros-cordoba.jpg'},
  {name:'CIBI',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72cibi.gif'},
  {name:'Defensores Central Córdoba',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72defcentralcordoba.gif'},
  {name:'Defensores Juveniles',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/10/defensores-juveniles-cordoba.png'},
  {name:'Deportivo Alberdi',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72alberdi.gif'},
  {name:'Deportivo Atalaya',logo:'https://i.pinimg.com/736x/38/14/5f/38145fe9673e2b562cd4a59a2f46d2b9.jpg'},
  {name:'Deportivo Banfield',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72banfield.gif'},
  {name:'Deportivo Lasallano',logo:'https://i.pinimg.com/736x/98/aa/9d/98aa9dc82fac2d73df8df8f4a1140e00.jpg'},
  {name:'Deportivo Norte',logo:'https://seeklogo.com/images/A/asociacion-deportiva-norte-de-alta-gracia-cordoba-logo-9A38FA221D-seeklogo.com.png'},
  {name:'El Carmen',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72elcarmen.gif'},
  {name:'Escuela Presidente Roca',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72pteroca.gif'},
  {name:'General Paz Juniors',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72gralpaz.gif'},
  {name:'Huracán',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72huracan2.gif'},
  {name:'Independiente Carlos Paz',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72independiente.gif'},
  {name:'Instituto',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Escudo_Instituto_Atletico_Central_Cordoba.png/512px-Escudo_Instituto_Atletico_Central_Cordoba.png'},
  {name:'Juvenil Barrio Comercial',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72comercial.gif'},
  {name:'La Unión de Malvinas',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionmalvinas.gif'},
  {name:'Las Flores',logo:'https://commons.wikimedia.org/wiki/Special:Redirect/file/Escudo%20de%20las%20flores.png?width=512'},
  {name:'Las Palmas',logo:'https://interiorfutbolero.com.ar/wp-content/uploads/2019/02/Las-Palmas.png'},
  {name:'Libertad',logo:'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/10/libertad-cordoba.png'},
  {name:'Los Andes',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72losandes2.gif'},
  {name:'MEDEA Club',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72medea.gif'},
  {name:'Quilmes',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72quilmes.gif'},
  {name:'Racing de Córdoba',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Escudo_del_Club_Atl%C3%A9tico_Racing_de_C%C3%B3rdoba.svg/512px-Escudo_del_Club_Atl%C3%A9tico_Racing_de_C%C3%B3rdoba.svg.png'},
  {name:'San Lorenzo',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72sanlorenzo.gif'},
  {name:'San Nicolás',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72sannicolas.gif'},
  {name:'Talleres',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Escudo_Club_Atl%C3%A9tico_Talleres.svg/512px-Escudo_Club_Atl%C3%A9tico_Talleres.svg.png'},
  {name:'Unión Florida',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionflorida.gif'},
  {name:'Unión San Vicente',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72unionsanvicente.gif'},
  {name:'Universitario',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Universitario_cba_logo.svg/512px-Universitario_cba_logo.svg.png'},
  {name:'Villa Azalais',logo:'https://logowik.com/content/uploads/images/club-social-deportivo-villa-azalais-de-villa-azalais-cordoba1723104177.logowik.com.webp'},
  {name:'Villa Siburu',logo:'https://www.futbolinterior.com.ar/images/stories/clubes/72villasirburu.gif'}
];"""
s,n=re.subn(r"const LCF_TEAMS=\[.*?\n\];",teams,s,count=1,flags=re.S)
if n!=1: raise SystemExit('LCF_TEAMS replacement failed')

new_picker=r'''function teamPickerMarkup(field,label,selected=''){
  const current=LCF_TEAMS.find(t=>t.name.toLocaleLowerCase('es-AR')===String(selected||'').trim().toLocaleLowerCase('es-AR'))||null;
  const other=Boolean(selected&&!current);
  const options=[...LCF_TEAMS].sort((a,b)=>a.name.localeCompare(b.name,'es-AR')).map(t=>`<button type="button" class="team-option" data-team-name="${esc(t.name)}" data-team-logo="${esc(t.logo||'')}">${teamLogoHtml(t)}<span><b>${esc(t.name)}</b></span></button>`).join('');
  const display=current?current.name:(other?titleWords(selected):'Elegí un equipo');
  const team=current||{name:display,logo:''};
  return `<div class="field team-field ${field==='away'?'away-picker':''}" data-team-picker="${field}"><label>${label}</label><input type="hidden" name="${field}" value="${esc(selected||'')}"><button type="button" class="team-picker-trigger" aria-expanded="false">${teamLogoHtml(team,'team-picker-crest')}<span class="team-picker-copy"><b>${esc(display)}</b><small>${current?'Liga Cordobesa':'Buscá o elegí un equipo'}</small></span><span class="team-picker-chevron">⌄</span></button><div class="team-picker-menu hidden"><input type="search" class="team-picker-search" placeholder="Buscar equipo…" autocomplete="off"><div class="team-picker-options">${options}<button type="button" class="team-option other-team" data-team-name="__other__"><span class="team-option-crest"><span class="team-crest-fallback">+</span></span><span><b>Otro equipo</b><small>Escribir manualmente</small></span></button><div class="team-picker-empty hidden">No encontré equipos con ese nombre.</div></div></div><input class="input team-other-input ${other?'':'hidden'}" data-team-other="${field}" placeholder="Escribí el nombre del equipo" value="${other?esc(titleWords(selected)):''}"></div>`;
}
'''
s,n=re.subn(r"function teamPickerMarkup\(field,label,selected=''\)\{.*?\n\}\n(?=function setTeamPicker)",new_picker,s,count=1,flags=re.S)
if n!=1: raise SystemExit('teamPickerMarkup replacement failed')

# Simplify setTeamPicker subtitle and remove category dependence.
s=s.replace("copy.querySelector('small').textContent=division||'Primera A · Primera B';","copy.querySelector('small').textContent=name?'Liga Cordobesa':'Buscá o elegí un equipo';")
s=s.replace("if(name!=='__other__'&&division!=='Otro equipo') other.classList.add('hidden');","if(name!=='__other__') other.classList.add('hidden');")
s=s.replace("setTeamPicker(root,name,btn.dataset.teamDivision||'',btn.dataset.teamLogo||'')","setTeamPicker(root,name,'',btn.dataset.teamLogo||'')")

# Marker.
if 'v97-unified-lcf-teams' not in s:
    s=s.replace('</head>','<!-- v97-unified-lcf-teams -->\n</head>',1)

p.write_text(s,encoding='utf-8')
print('v97 unified LCF team picker patched')
