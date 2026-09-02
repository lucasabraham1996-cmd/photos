from pathlib import Path
from io import BytesIO
from collections import deque
from urllib.parse import urljoin
import re, unicodedata
import requests
from PIL import Image

p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

# Control de la temporada 2026: 22 clubes de Primera A + 20 clubes activos de Primera B.
# Unión Serrana inició el torneo pero dejó de participar durante la temporada, por eso no integra la nómina activa.
EXPECTED_A={
'Camioneros Córdoba','Argentino Peñarol','Barrio Parque','Talleres','CIBI','Deportivo Lasallano','San Lorenzo','Racing de Córdoba','Las Palmas','Libertad','Los Andes','AMSURRBAC','Huracán','Bella Vista','Belgrano','Escuela Presidente Roca','Deportivo Atalaya','General Paz Juniors','Instituto','Universitario','Villa Azalais','Unión San Vicente'
}
EXPECTED_B={
'Defensores Central Córdoba','Deportivo Banfield','Independiente de Carlos Paz','All Boys','Atlético Carlos Paz','Juvenil Barrio Comercial','Unión Florida','Deportivo Norte','San Nicolás','Deportivo Alberdi','El Carmen','Quilmes','MEDEA','Las Flores','La Unión','Defensores Juveniles','Villa Siburú','Calera Central','Avellaneda','Almirante Brown'
}

# Código de cada ficha exacta dentro de la galería de clubes afiliados de Fútbol Interior.
FI_CODES={
'All Boys':'1074','Defensores Central Córdoba':'9851','El Carmen':'1203','Independiente de Carlos Paz':'3935',
'Instituto':'1091','La Unión':'7371','Quilmes':'14384','San Nicolás':'7401','Unión San Vicente':'1102','Universitario':'1087'
}

# Fuentes puntuales verificadas para los escudos que tenían enlaces viejos/bloqueados.
EXTRA_SOURCES={
'Instituto':[
    'https://commons.wikimedia.org/wiki/Special:Redirect/file/Instituto%20Atl%C3%A9tico%20Central%20C%C3%B3rdoba%20Escudo.png',
],
'Unión San Vicente':[
    'https://futbolinterior.com.ar/images/stories/clubes/72unionsv.gif',
    'https://commons.wikimedia.org/wiki/Special:Redirect/file/Escudo%20Club%20Union%20San%20Vicente%20de%20C%C3%B3rdoba.gif',
],
'Universitario':[
    'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Universitario_cba_logo.svg/512px-Universitario_cba_logo.svg.png',
],
'Independiente de Carlos Paz':[
    'https://independientevcp.com.ar/logo.png',
],
'Quilmes':[
    'https://futbolfundaciones.wordpress.com/wp-content/uploads/2024/11/quilmes-1.png',
],
'San Nicolás':[
    'https://i.pinimg.com/736x/05/8b/5c/058b5cb4265e271a0b239a3d2a5ca76d.jpg',
],
'All Boys':[
    'https://commons.wikimedia.org/wiki/Special:Redirect/file/All%20Boys%20Cordoba%20logo.png',
],
'Defensores Central Córdoba':[
    'https://futbolfundaciones.wordpress.com/wp-content/uploads/2022/09/club-atletico-defensores-central-cordoba-cordoba2.png?w=963',
],
'El Carmen':[
    'https://futbolfundaciones.wordpress.com/wp-content/uploads/2025/04/el-carmen-montecristo-cordoba.png',
],
}

block_start=s.index('const LCF_TEAMS=[')
block_end=s.index('];',block_start)+2
block=s[block_start:block_end]
pat=re.compile(r"\{name:'([^']+)',division:'([^']+)',logo:'([^']*)'\}")
teams=[{'name':m.group(1),'division':m.group(2),'logo':m.group(3)} for m in pat.finditer(block)]
if len(teams)!=42:
    raise SystemExit(f'Esperaba 42 clubes activos y encontré {len(teams)}')
found_a={t['name'] for t in teams if t['division']=='Primera A'}
found_b={t['name'] for t in teams if t['division']=='Primera B'}
if found_a!=EXPECTED_A:
    raise SystemExit(f'Diferencia Primera A. Faltan={sorted(EXPECTED_A-found_a)} sobran={sorted(found_a-EXPECTED_A)}')
if found_b!=EXPECTED_B:
    raise SystemExit(f'Diferencia Primera B. Faltan={sorted(EXPECTED_B-found_b)} sobran={sorted(found_b-EXPECTED_B)}')

def slug(text):
    x=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+','-',x).strip('-')

def remove_outer_white(im):
    """Quita únicamente el blanco conectado al borde; conserva el blanco que pertenece al escudo."""
    im=im.convert('RGBA')
    px=im.load(); w,h=im.size
    white=lambda x,y: px[x,y][3]>0 and px[x,y][0]>=238 and px[x,y][1]>=238 and px[x,y][2]>=238
    q=deque(); seen=set()
    for x in range(w):
        if white(x,0): q.append((x,0)); seen.add((x,0))
        if white(x,h-1): q.append((x,h-1)); seen.add((x,h-1))
    for y in range(h):
        if white(0,y): q.append((0,y)); seen.add((0,y))
        if white(w-1,y): q.append((0,y)); seen.add((0,y))
    while q:
        x,y=q.popleft()
        r,g,b,a=px[x,y]; px[x,y]=(r,g,b,0)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and white(nx,ny):
                seen.add((nx,ny)); q.append((nx,ny))
    return im

def normalize_logo(content,name):
    im=Image.open(BytesIO(content))
    try: im.seek(0)
    except Exception: pass
    im=remove_outer_white(im)
    alpha=im.getchannel('A')
    bbox=alpha.getbbox()
    if not bbox: raise ValueError('imagen sin contenido visible')
    im=im.crop(bbox)
    max_side=224
    ratio=min(max_side/im.width,max_side/im.height)
    nw=max(1,round(im.width*ratio)); nh=max(1,round(im.height*ratio))
    im=im.resize((nw,nh),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0))
    canvas.alpha_composite(im,((256-nw)//2,(256-nh)//2))
    out=Path('assets/lcf')/(slug(name)+'.png')
    out.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(out,'PNG',optimize=True)
    return out.as_posix()

session=requests.Session()
session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; lucasabraham.ph/1.0)','Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'})

def discover_futbolinterior_logo(name):
    code=FI_CODES.get(name)
    if not code: return []
    page=f'https://futbolinterior.com.ar/escudos/ppal/ampesc.php?cod={code}'
    try:
        r=session.get(page,timeout=20,allow_redirects=True)
        r.raise_for_status()
        html=r.text
        srcs=re.findall(r'''(?:src|href)=["']([^"']*images/stories/clubes/[^"']+)["']''',html,re.I)
        urls=[]
        for src in srcs:
            u=urljoin(page,src.replace('&amp;','&'))
            if u not in urls: urls.append(u)
        if urls: print('DESCUBIERTO',name,urls[:3])
        return urls
    except Exception as e:
        print('No pude leer ficha Fútbol Interior',name,repr(e))
        return []

def download_first_valid(name,primary):
    candidates=[]
    for u in [primary,*EXTRA_SOURCES.get(name,[]),*discover_futbolinterior_logo(name)]:
        if u and u not in candidates: candidates.append(u)
    errors=[]
    for url in candidates:
        try:
            r=session.get(url,timeout=25,allow_redirects=True)
            r.raise_for_status()
            if not r.content: raise ValueError('respuesta vacía')
            path=normalize_logo(r.content,name)
            print('OK',name,'<-',url,'=>',path)
            return path,url
        except Exception as e:
            errors.append(f'{url} :: {e!r}')
            print('FALLBACK',name,url,repr(e))
    raise RuntimeError(' | '.join(errors) or 'sin candidatos')

fail=[]
local_paths={}
used_sources={}
for t in teams:
    try:
        local_paths[t['name']],used_sources[t['name']]=download_first_valid(t['name'],t['logo'])
    except Exception as e:
        fail.append((t['name'],repr(e)))
        print('FAIL FINAL',t['name'],e)
if fail:
    print('\nFallaron escudos:')
    for row in fail: print(row)
    raise SystemExit(f'No se pudieron normalizar {len(fail)} escudos')

# Reescribir las URLs remotas por PNG transparentes locales y estables.
new_block=block
for t in teams:
    old=f"{{name:'{t['name']}',division:'{t['division']}',logo:'{t['logo']}'}}"
    new=f"{{name:'{t['name']}',division:'{t['division']}',logo:'{local_paths[t['name']]}'}}"
    if old not in new_block: raise SystemExit('No pude reemplazar '+t['name'])
    new_block=new_block.replace(old,new,1)
s=s[:block_start]+new_block+s[block_end:]

# Una sola lista alfabética. La división queda sólo como dato interno y nunca se muestra al cliente.
fstart=s.index('function teamPickerMarkup(')
gstart=s.index('  const groups=',fstart)
dstart=s.index('  const display=',gstart)
options="""  const options=[...LCF_TEAMS].sort((a,b)=>a.name.localeCompare(b.name,'es-AR')).map(t=>`<button type=\"button\" class=\"team-option\" data-team-name=\"${esc(t.name)}\" data-team-division=\"${esc(t.division)}\" data-team-logo=\"${esc(t.logo)}\">${teamLogoHtml(t)}<span><b>${esc(t.name)}</b></span></button>`).join('');\n"""
s=s[:gstart]+options+s[dstart:]
s=s.replace("  const div=current?current.division:(other?'Otro equipo':'Primera A · Primera B');","  const div=other?'Otro equipo':'Liga Cordobesa';",1)
s=s.replace('${groups}<button type="button" class="team-option other-team"','${options}<button type="button" class="team-option other-team"',1)
s=s.replace("copy.querySelector('small').textContent=division||'Primera A · Primera B';","copy.querySelector('small').textContent=name?'Liga Cordobesa':'Buscá o elegí un equipo';",1)

# Escudo sin placa/fondo claro alrededor.
s=s.replace("background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.09);overflow:hidden","background:transparent;border:0;overflow:visible",1)
s=s.replace('.team-picker-group{padding:7px 6px 5px;font-size:9px;color:#7dd3fc;font-weight:900;text-transform:uppercase;letter-spacing:.16em}', '.team-picker-group{display:none!important}',1)

if '/* v96: selector visual de clubes Liga Cordobesa */' in s:
    s=s.replace('/* v96: selector visual de clubes Liga Cordobesa */','/* v97: lista única LCF + 42 escudos PNG transparentes locales */',1)

p.write_text(s,encoding='utf-8')
print('v97 listo: 42 clubes, lista única y escudos locales transparentes')
print('Fuentes finalmente usadas:')
for name in sorted(used_sources): print(name,'=>',used_sources[name])
