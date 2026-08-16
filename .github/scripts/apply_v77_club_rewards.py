from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = """    const CLUB_DEFAULT_PRODUCT = { id:'club-pack-3-fotos-10x15', name:'Pack de 3 fotos impresas a elección', description:'Tres fotos impresas a elección en tamaño de 10x15 cm.', points:3, imageUrl:'https://i.postimg.cc/gkPWMjB9/Chat-GPT-Image-15-ago-2026-10-46-05-p-m.png', active:true, createdAt:'2026-08-15T23:03:00-03:00' };\n    const withDefaultClubProducts = (list) => {\n        const items = Array.isArray(list) ? list : [];\n        return items.some(p => p && p.id === CLUB_DEFAULT_PRODUCT.id) ? items : [CLUB_DEFAULT_PRODUCT, ...items];\n    };"""
new = """    const CLUB_DEFAULT_PRODUCTS = [\n        { id:'club-foto-impresa-10x15', name:'1 foto impresa a elección', description:'Una foto impresa a elección en tamaño de 10x15 cm.', points:3, imageUrl:'https://i.postimg.cc/gkPWMjB9/Chat-GPT-Image-15-ago-2026-10-46-05-p-m.png', active:true, createdAt:'2026-08-15T23:17:00-03:00' },\n        { id:'club-pack-3-fotos-10x15', name:'Pack de 3 fotos impresas a elección', description:'Tres fotos impresas a elección en tamaño de 10x15 cm.', points:5, imageUrl:'https://i.postimg.cc/gkPWMjB9/Chat-GPT-Image-15-ago-2026-10-46-05-p-m.png', active:true, createdAt:'2026-08-15T23:03:00-03:00' }\n    ];\n    const withDefaultClubProducts = (list) => {\n        const items = Array.isArray(list) ? list : [];\n        const defaultIds = new Set(CLUB_DEFAULT_PRODUCTS.map(p => p.id));\n        const customItems = items.filter(p => p && !defaultIds.has(p.id));\n        const existingById = new Map(items.filter(Boolean).map(p => [p.id, p]));\n        const defaults = CLUB_DEFAULT_PRODUCTS.map(def => ({ ...existingById.get(def.id), ...def }));\n        return [...defaults, ...customItems];\n    };"""
count = s.count(old)
if count != 1:
    raise SystemExit(f'Club defaults block: expected 1 match, got {count}')
s = s.replace(old, new, 1)
s = s.replace('v76-club-gallery-points-reset', 'v77-club-rewards-3-and-5')
if "club-foto-impresa-10x15" not in s or "points:5" not in s:
    raise SystemExit('required reward markers missing after patch')
p.write_text(s, encoding='utf-8')
print('v77 Club rewards patch applied')
