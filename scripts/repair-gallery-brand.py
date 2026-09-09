#!/usr/bin/env python3
"""Guarded gallery recovery and brand migration. Does not modify orders or payments."""
from pathlib import Path
import io
import re
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OLD = 'https://i.postimg.cc/PrD4jg9V/Logo-LA.png'
NEW = 'https://i.postimg.cc/nLw3YCFz/image.png'
LOCAL = './brand-logo.png?v=105'
VERSION = 'v105-gallery-recovery-brand'

req = urllib.request.Request(NEW, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=40) as response:
    raw = response.read()
assert raw[:8] == bytes([137,80,78,71,13,10,26,10]), 'The supplied artwork is not a PNG'
logo = Image.open(io.BytesIO(raw)).convert('RGBA')
assert logo.width > 0 and logo.height > 0
(ROOT/'brand-logo.png').write_bytes(raw)

def contain(image, size):
    image = image.copy()
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image

icon = Image.new('RGBA', (512,512), '#000000')
mark = contain(logo, (430,430))
icon.alpha_composite(mark, ((512-mark.width)//2, (512-mark.height)//2))
icon.convert('RGB').save(ROOT/'site-icon-dark-la.png', 'PNG')
preview = Image.new('RGBA', (1200,630), '#050505')
mark = contain(logo, (1050,510))
preview.alpha_composite(mark, ((1200-mark.width)//2, (630-mark.height)//2))
preview.convert('RGB').save(ROOT/'social-preview-la.png', 'PNG')

p = ROOT/'index.html'
s = p.read_text(encoding='utf-8')
assert OLD in s and 'async function fetchGalleryData({ force = false } = {}) {' in s
assert 'v104-guest-performance' in s
s = s.replace(OLD, LOCAL).replace('v104-guest-performance', VERSION)

loader = '''async function fetchGalleryData({ force = false } = {}) {
    const sources = [];
    if (APPS_SCRIPT_URL && APPS_SCRIPT_URL.trim()) {
        sources.push(jsonp(APPS_SCRIPT_URL.trim(), force ? 38000 : 18000, { force }).then(data => {
            if (!data || data.ok === false || data.error || !Array.isArray(data.albums) || !data.albums.length)
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
a = s.index('async function fetchGalleryData({ force = false } = {}) {')
b = s.index('\nfunction parseGvizTable(obj)', a)
s = s[:a] + loader + s[b:]
old_order = 'albumPhotos.slice((safeAlbumPage - 1) * 60, safeAlbumPage * 60).reverse()'
assert old_order in s
s = s.replace(old_order, 'albumPhotos.slice((safeAlbumPage - 1) * 60, safeAlbumPage * 60)')
assert 'ensureIphoneBrandAssets();' in s
s = s.replace('ensureIphoneBrandAssets();', "applyIphoneHeadAssets('./site-icon-dark-la.png?v=105');")
s = re.sub(r'social-preview-la[.]png[?]v=\d+', 'social-preview-la.png?v=105', s)
# Explicit static icons also cover browsers that do not execute the PWA helper.
s = s.replace('</head>', '<link rel="icon" type="image/png" href="./site-icon-dark-la.png?v=105" /><link rel="apple-touch-icon" href="./site-icon-dark-la.png?v=105" /></head>', 1)
assert OLD not in s
p.write_text(s, encoding='utf-8')

# The auxiliary pages use the same brand and social preview. Club and team logos remain untouched.
for name in ('como-pedir.html', 'contrataciones.html'):
    p = ROOT/name
    s = p.read_text(encoding='utf-8').replace(OLD, LOCAL)
    s = re.sub(r'social-preview-la[.]png[?]v=\d+', 'social-preview-la.png?v=105', s)
    s = s.replace('</head>', '<link rel="icon" type="image/png" href="./site-icon-dark-la.png?v=105" /><link rel="apple-touch-icon" href="./site-icon-dark-la.png?v=105" /></head>', 1)
    if name == 'como-pedir.html':
        s = s.replace('<a class="brand" href="./">lucasabraham.ph</a>', '<a class="brand" href="./" style="display:inline-flex;align-items:center;gap:10px"><img src="./brand-logo.png?v=105" alt="" width="42" height="42" style="object-fit:contain" />lucasabraham.ph</a>')
    assert OLD not in s
    p.write_text(s, encoding='utf-8')
print('Brand migration ready:', logo.size, 'bytes:', len(raw), flush=True)
