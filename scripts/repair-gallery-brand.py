#!/usr/bin/env python3
"""Apply the requested brand and repair the gallery source fallback without changing orders."""
from pathlib import Path
import re
import json
import urllib.request
import io

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'index.html'
s = p.read_text(encoding='utf-8')
OLD = 'https://i.postimg.cc/PrD4jg9V/Logo-LA.png'
NEW = 'https://i.postimg.cc/nLw3YCFz/image.png'
VERSION = 'v105-gallery-recovery-brand'

def replace(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:100], s.count(old), count)
    s = s.replace(old, new)

def block(start, end, replacement):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + replacement + s[b:]

# Keep the exact supplied artwork. Do not alter club crests or payment branding.
assert OLD in s
s = s.replace(OLD, NEW)
replace('v104-guest-performance', VERSION, 2)

# A successful HTTP response is not necessarily usable gallery data.
# The live Apps Script deployment currently returns 404, and the old gviz fallback
# also returns 404. Use a verified same-origin snapshot, not an invented API action.
loader = '''async function fetchGalleryData({ force = false } = {}) {
    const sources = [];
    if (APPS_SCRIPT_URL && APPS_SCRIPT_URL.trim()) {
        sources.push(jsonp(APPS_SCRIPT_URL.trim(), force ? 38000 : 18000, { force }).then(data => {
            if (!data || data.ok === false || data.error || !Array.isArray(data.albums))
                throw new Error((data && data.error) || 'La fuente principal no devolvió álbumes válidos');
            return data;
        }));
    }
    sources.push(fetch('./gallery-snapshot.json', { cache: force ? 'no-store' : 'default' }).then(async response => {
        if (!response.ok) throw new Error('No se pudo consultar el respaldo de la galería');
        const data = await response.json();
        if (!data || data.ok === false || !Array.isArray(data.albums) || !data.albums.length)
            throw new Error('El respaldo de la galería está vacío o no es válido');
        return data;
    }));
    return promiseAnySafe(sources);
}
'''
block('async function fetchGalleryData({ force = false } = {}) {', '\nfunction parseGvizTable(obj)', loader)
# Do not delete a previously valid gallery on a failed refresh.
replace('''            else {
                setAlbums([]);
                setError((e && e.message) || 'No se pudo cargar la hoja de cálculo.');
            }''', '''            else {
                setError((e && e.message) || 'No se pudo cargar la hoja de cálculo.');
            }''')
# Keep chronological photo order; pagination must not reverse it.
replace('albumPhotos.slice((safeAlbumPage - 1) * 60, safeAlbumPage * 60).reverse()', 'albumPhotos.slice((safeAlbumPage - 1) * 60, safeAlbumPage * 60)')
# Avoid a cache-busting version that still points to the old brand previews.
s = re.sub(r'(social-preview-la\\.png\\?v=)\\d+', r'\\g<1>105', s)
# Stable local app icons, including installations on iPhone.
replace('ensureIphoneBrandAssets();', "applyIphoneHeadAssets('./site-icon-dark-la.png?v=105');")
# Keep all previously deployed purchasing/club logic unchanged.
assert 'if(checkoutWantsPoints&&!customerDetailsSaved)' in s
assert 'wantsPoints: Boolean(cleanPhone)' in s
assert 'const totalAlbumPages = Math.max(1, Math.ceil(albumPhotos.length / 60))' in s
assert OLD not in s
p.write_text(s, encoding='utf-8')

# Download the actual user-supplied PNG and prepare local icon/preview assets.
from PIL import Image
req = urllib.request.Request(NEW, headers={'User-Agent':'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=40) as response:
    raw = response.read()
assert raw.startswith(b'\\x89PNG\\r\\n\\x1a\\n'), 'The supplied artwork is not a PNG'
(ROOT / 'brand-logo.png').write_bytes(raw)
logo = Image.open(io.BytesIO(raw)).convert('RGBA')
assert logo.width > 0 and logo.height > 0

def contain(image, size):
    image = image.copy()
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image

icon = Image.new('RGBA', (512,512), '#000000')
mark = contain(logo,(430,430))
icon.alpha_composite(mark,((512-mark.width)//2,(512-mark.height)//2))
icon.convert('RGB').save(ROOT/'site-icon-dark-la.png', 'PNG')
preview = Image.new('RGBA',(1200,630),'#050505')
mark = contain(logo,(1050,510))
preview.alpha_composite(mark,((1200-mark.width)//2,(630-mark.height)//2))
preview.convert('RGB').save(ROOT/'social-preview-la.png','PNG')
print('Brand migration ready:', logo.size, 'bytes:', len(raw))
