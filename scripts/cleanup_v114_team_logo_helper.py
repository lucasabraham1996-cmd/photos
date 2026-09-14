from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

helper = r'''function teamLogoTokens(value) {
    const stop = new Set([
        'club','atletico','atletica','atleticos','ca','c','fc','sc','de','del','la','las','los','el','y',
        'cordoba','cordobes','cordobesa','futbol','football','sociedad','deportivo','deportiva',
        'primera','reserva','cebollitas','inferiores','femenino','masculino','categoria','cat'
    ]);
    return norm(value).split('_').filter(t => t && t.length > 1 && !stop.has(t));
}
'''

pattern = r'(?:function teamLogoTokens\(value\) \{.*?\n\}\n)+(?=function canonicalAppTeamKey)'
s, count = re.subn(pattern, lambda _m: helper, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit('No se encontró el bloque teamLogoTokens antes de canonicalAppTeamKey')

p.write_text(s, encoding='utf-8')
print('v114 helper deduplicated')
