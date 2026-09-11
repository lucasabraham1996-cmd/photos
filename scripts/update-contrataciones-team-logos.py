#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('contrataciones.html')
s = p.read_text(encoding='utf-8')

teams = [
('All Boys','https://i.postimg.cc/Vkvy6VmY/All-Boys.png'),
('Almirante Brown','https://i.postimg.cc/K8jXzHxR/Almirante-Brown.png'),
('AMSURRBAC','https://i.postimg.cc/cLCqHb0v/Amsurbac.png'),
('Argentino Peñarol','https://i.postimg.cc/8zc850Ns/Argentino-Penarol.png'),
('Atalaya','https://i.postimg.cc/BnbW6V48/Atalaya.png'),
('Atlético Carlos Paz','https://i.postimg.cc/wjMKvGgN/Atletico-Carlos-Paz.png'),
('Avellaneda','https://i.postimg.cc/pLrNT6R8/Avellaneda.png'),
('Banfield','https://i.postimg.cc/jS2V5FtP/Banfield.png'),
('Barrio Parque','https://i.postimg.cc/rws6mPMC/Barrio-Parque.png'),
('Belgrano','https://i.postimg.cc/RZhrFD4R/Belgrano.png'),
('Bella Vista','https://i.postimg.cc/HknGxhdz/Bella-Vista.png'),
('Calera Central','https://i.postimg.cc/dV3M1xw4/Calera-Central.png'),
('Camioneros Córdoba','https://i.postimg.cc/K8H6gD8n/Cambioneros.png'),
('CIBI','https://i.postimg.cc/T34zWJ3J/CIBI.png'),
('Club Coronel Olmedo','https://i.postimg.cc/Jz2fB5zq/Club-Coronel-Olmedo.png'),
('Defensores Central Córdoba','https://i.postimg.cc/bwB729wL/Defensores-Central-Cordoba.png'),
('Deportivo Alberdi','https://i.postimg.cc/kgp0tvgf/Deportivo-Alberdi.png'),
('Deportivo Defensores Juveniles','https://i.postimg.cc/Njz3rkjn/Deportivo-Defensores-Junveniles.png'),
('Deportivo Norte','https://i.postimg.cc/7ZWFTnZc/Deportivo-Norte.png'),
('DIEF','https://i.postimg.cc/mg5vFyrf/DIEF.png'),
('El Carmen','https://i.postimg.cc/W1HBJw4c/El-Carmen.png'),
('Escuela Presidente Roca','https://i.postimg.cc/SxvBzfKq/Escuela-Presidente-Roca.png'),
('General Paz Junior','https://i.postimg.cc/jjnG6nD1/General-Paz-Junior.png'),
('Huracán','https://i.postimg.cc/VN0390JT/Huracan.png'),
('Independiente','https://i.postimg.cc/VN0390Jp/Independiente.png'),
('Instituto','https://i.postimg.cc/N02W82K3/Instituto.png'),
('Juvenil Barrio Comercial','https://i.postimg.cc/q769c6tf/Juvenil-Barrio-Comercial.png'),
('La Unión Malvinas','https://i.postimg.cc/Zqv1Pv9z/La-Union-Malvinas.png'),
('Las Flores','https://i.postimg.cc/Zqv1Pv9m/Las-Flores.png'),
('Las Palmas','https://i.postimg.cc/0NKLGK6P/Las-Palmas.png'),
('Lasallano','https://i.postimg.cc/d0ZzRZ7q/Lasallano.png'),
('Libertad','https://i.postimg.cc/25LPdLqk/Libertad.png'),
('Lobos del Sur','https://i.postimg.cc/CKnWCnZx/Lobos-del-Sur.png'),
('Los Andes','https://i.postimg.cc/W4qQmqD4/Los-Andes.png'),
('Medea','https://i.postimg.cc/5tQZ5QHy/Medea.png'),
('Quilmes','https://i.postimg.cc/Lsgrkgqh/Quilmes.png'),
('Racing','https://i.postimg.cc/Lsgrkgqg/Racing.png'),
('Rancagua','https://i.postimg.cc/QMKRgKBT/Rancagua.png'),
('Recreativo Municipalidad','https://i.postimg.cc/LsgrkgqZ/Recreativo-Municipalidad.png'),
('San Lorenzo','https://i.postimg.cc/76vjKP7Z/San-Lorenzo.png'),
('San Nicolás','https://i.postimg.cc/3RMztrpw/San-Nicolas.png'),
('Talleres','https://i.postimg.cc/G206X3YH/Talleres.png'),
('Unión Florida','https://i.postimg.cc/cHqPF1Yv/Union-Florida.png'),
('Unión San Vicente','https://i.postimg.cc/3RMztrp0/Union-San-Vicente.png'),
('Unión Serrana','https://i.postimg.cc/26pg0jvW/Union-Serrana.png'),
('Universitario','https://i.postimg.cc/76vjKP77/Universitario.png'),
('Valores','https://i.postimg.cc/sXFbTfS7/Valores.png'),
('Villa Azalais','https://i.postimg.cc/hjFN24xV/Villa-Azalaiz.png'),
('Villa Siburu','https://i.postimg.cc/j5VBMqNH/Villa-Siburu.png'),
]
block = "const LCF_TEAMS=[\n" + ",\n".join("  {name:%r,logo:%r}" % (n,u) for n,u in teams) + "\n];"
# Convert Python repr single quotes safely (names/URLs here contain no apostrophes).
s2, n = re.subn(r"const LCF_TEAMS=\[.*?\n\];", block, s, count=1, flags=re.S)
assert n == 1, 'LCF_TEAMS block not found'
s = s2

old = "const current=LCF_TEAMS.find(t=>t.name.toLocaleLowerCase('es-AR')===String(selected||'').trim().toLocaleLowerCase('es-AR'))||null;"
new = "const current=findLcfTeam(selected)||null;"
assert old in s, 'teamPicker current lookup not found'
s = s.replace(old, new, 1)

pattern = r"function findLcfTeam\(name\)\{.*?\}\nfunction bookingTeamLogoHtml"
replacement = """function findLcfTeam(name){const key=normalizeTeamKey(name);if(!key)return null;const aliases={'all boys de cordoba':'all boys','club atletico all boys':'all boys','club atletico all boys cordoba':'all boys','caab':'all boys','amsurbac':'amsurrbac','camioneros':'camioneros cordoba','cambioneros':'camioneros cordoba','club camioneros':'camioneros cordoba','coronel olmedo':'club coronel olmedo','defensores juveniles':'deportivo defensores juveniles','deportivo defensores junveniles':'deportivo defensores juveniles','presidente roca':'escuela presidente roca','general paz juniors':'general paz junior','general paz juniors cordoba':'general paz junior','barrio comercial':'juvenil barrio comercial','comercial':'juvenil barrio comercial','la union':'la union malvinas','municipalidad':'recreativo municipalidad','recreativo municipalidad de cordoba':'recreativo municipalidad','racing cordoba':'racing','racing de cordoba':'racing','independiente carlos paz':'independiente','independiente de carlos paz':'independiente','atletico carlos paz':'atletico carlos paz','defensores central cordoba':'defensores central cordoba','central cordoba':'defensores central cordoba','union san vicente':'union san vicente','villa azalaiz':'villa azalais','villa siburu':'villa siburu'};const wanted=aliases[key]||key;return LCF_TEAMS.find(t=>normalizeTeamKey(t.name)===wanted)||LCF_TEAMS.find(t=>{const k=normalizeTeamKey(t.name);return wanted.length>5&&(k.includes(wanted)||wanted.includes(k))})||null}\nfunction bookingTeamLogoHtml"""
s2, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
assert n == 1, 'findLcfTeam function not found'
s = s2

# Cache/version marker so installed browsers take the updated contratación UI.
s = s.replace('/* v97: lista única LCF + 42 escudos PNG transparentes locales */', '/* v107: lista LCF actualizada con 49 escudos APP */', 1)

p.write_text(s, encoding='utf-8')
print('Updated contratación team catalog:', len(teams), 'teams')
