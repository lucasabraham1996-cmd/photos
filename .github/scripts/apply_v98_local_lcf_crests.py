from pathlib import Path
import re

p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

teams = """const LCF_TEAMS=[
  {name:'All Boys',logo:'assets/lcf/all-boys.png'},
  {name:'Almirante Brown',logo:'assets/lcf/almirante-brown.png'},
  {name:'AMSURRBAC',logo:'assets/lcf/amsurrbac.png'},
  {name:'Argentino Peñarol',logo:'assets/lcf/argentino-penarol.png'},
  {name:'Atlético Carlos Paz',logo:'assets/lcf/atletico-carlos-paz.png'},
  {name:'Avellaneda',logo:'assets/lcf/avellaneda.png'},
  {name:'Barrio Parque',logo:'assets/lcf/barrio-parque.png'},
  {name:'Belgrano',logo:'assets/lcf/belgrano.png'},
  {name:'Bella Vista',logo:'assets/lcf/bella-vista.png'},
  {name:'Calera Central',logo:'assets/lcf/calera-central.png'},
  {name:'Camioneros Córdoba',logo:'assets/lcf/camioneros-cordoba.png'},
  {name:'CIBI',logo:'assets/lcf/cibi.png'},
  {name:'Defensores Central Córdoba',logo:'assets/lcf/defensores-central-cordoba.png'},
  {name:'Defensores Juveniles',logo:'assets/lcf/defensores-juveniles.png'},
  {name:'Deportivo Alberdi',logo:'assets/lcf/deportivo-alberdi.png'},
  {name:'Deportivo Atalaya',logo:'assets/lcf/deportivo-atalaya.png'},
  {name:'Deportivo Banfield',logo:'assets/lcf/deportivo-banfield.png'},
  {name:'Deportivo Lasallano',logo:'assets/lcf/deportivo-lasallano.png'},
  {name:'Deportivo Norte',logo:'assets/lcf/deportivo-norte.png'},
  {name:'El Carmen',logo:'assets/lcf/el-carmen.png'},
  {name:'Escuela Presidente Roca',logo:'assets/lcf/escuela-presidente-roca.png'},
  {name:'General Paz Juniors',logo:'assets/lcf/general-paz-juniors.png'},
  {name:'Huracán',logo:'assets/lcf/huracan.png'},
  {name:'Independiente Carlos Paz',logo:'assets/lcf/independiente-de-carlos-paz.png'},
  {name:'Instituto',logo:'assets/lcf/instituto.png'},
  {name:'Juvenil Barrio Comercial',logo:'assets/lcf/juvenil-barrio-comercial.png'},
  {name:'La Unión de Malvinas',logo:'assets/lcf/la-union.png'},
  {name:'Las Flores',logo:'assets/lcf/las-flores.png'},
  {name:'Las Palmas',logo:'assets/lcf/las-palmas.png'},
  {name:'Libertad',logo:'assets/lcf/libertad.png'},
  {name:'Los Andes',logo:'assets/lcf/los-andes.png'},
  {name:'MEDEA Club',logo:'assets/lcf/medea.png'},
  {name:'Quilmes',logo:'assets/lcf/quilmes.png'},
  {name:'Racing de Córdoba',logo:'assets/lcf/racing-de-cordoba.png'},
  {name:'San Lorenzo',logo:'assets/lcf/san-lorenzo.png'},
  {name:'San Nicolás',logo:'assets/lcf/san-nicolas.png'},
  {name:'Talleres',logo:'assets/lcf/talleres.png'},
  {name:'Unión Florida',logo:'assets/lcf/union-florida.png'},
  {name:'Unión San Vicente',logo:'assets/lcf/union-san-vicente.png'},
  {name:'Universitario',logo:'assets/lcf/universitario.png'},
  {name:'Villa Azalais',logo:'assets/lcf/villa-azalais.png'},
  {name:'Villa Siburu',logo:'assets/lcf/villa-siburu.png'}
];"""

s,n=re.subn(r"const LCF_TEAMS=\[.*?\n\];",teams,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit('LCF_TEAMS replacement failed')

# Make crest containers explicitly transparent and keep the list unified.
s=s.replace('background:transparent;border:0;overflow:visible','background:transparent;border:0;overflow:visible')
if '.team-picker-group{display:none!important}' not in s:
    s=s.replace('.team-picker-search{', '.team-picker-group{display:none!important}\n    .team-picker-search{', 1)

# Remove any remaining visible division subtitle from options, if present.
s=s.replace("<small>${esc(t.division)}</small>","")
s=s.replace("data-team-division=\"${esc(t.division)}\" ","")

# Marker.
if 'v98-local-lcf-crests' not in s:
    s=s.replace('<!-- v97-unified-lcf-teams -->','<!-- v97-unified-lcf-teams -->\n<!-- v98-local-lcf-crests -->',1)

p.write_text(s,encoding='utf-8')
print('v98 local LCF crests patched')
