from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Bump version so installed/mobile copies refresh the UI.
s = s.replace('v111-match-picker', 'v113-match-picker-filters')
s = s.replace('v112-match-picker-broadcast', 'v113-match-picker-filters')

# Google Sheets may send dates as spreadsheet serials (e.g. 46256).
# Parse those as real dates instead of interpreting them as the year 46256.
new_parse = r'''function parseAlbumDate(v) {
    const s = String(v || "").trim();
    if (!s)
        return null;
    if (/^\d+(?:\.\d+)?$/.test(s)) {
        const n = Number(s);
        if (Number.isFinite(n)) {
            if (n >= 20000 && n <= 90000) {
                const excelEpoch = new Date(1899, 11, 30).getTime();
                return excelEpoch + Math.round(n * 86400000);
            }
            if (n > 1000000000000)
                return n;
            if (n > 1000000000)
                return n * 1000;
        }
    }
    const m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})$/);
    if (m) {
        const y = Number(m[3].length === 2 ? "20" + m[3] : m[3]);
        return new Date(y, Number(m[2]) - 1, Number(m[1])).getTime();
    }
    const t = Date.parse(s);
    return Number.isNaN(t) ? null : t;
}'''
s = re.sub(r'function parseAlbumDate\(v\) \{.*?\n\}', lambda _m: new_parse, s, count=1, flags=re.S)

helpers = r'''
function matchPickerChrono(album) {
    let ts = Number(album && album.dateTs) || 0;
    if (ts) {
        const d = new Date(ts);
        const y = d.getFullYear();
        if (Number.isFinite(y) && y >= 1900 && y <= 2100) return ts;
    }
    const label = String((album && album.dateLabel) || '').trim();
    const serialMatch = label.match(/(?:^|\D)(\d{5})(?:\D|$)/);
    if (serialMatch) {
        const serial = Number(serialMatch[1]);
        if (serial >= 20000 && serial <= 90000) {
            return new Date(1899, 11, 30).getTime() + Math.round(serial * 86400000);
        }
    }
    const parsed = parseAlbumDate(label);
    return parsed || ts || 0;
}
function matchPickerDateLabel(album) {
    const ts = matchPickerChrono(album);
    if (!ts) return String((album && album.dateLabel) || '');
    const d = new Date(ts);
    const y = d.getFullYear();
    if (y < 1900 || y > 2100) return String((album && album.dateLabel) || '');
    return new Intl.DateTimeFormat('es-AR', { day:'2-digit', month:'short', year:'numeric' }).format(d).replace('.', '');
}
function matchPickerCategories(album) {
    const items = [...new Set((Array.isArray(album && album.subalbums) ? album.subalbums : [])
        .map(sa => String((sa && sa.name) || '').trim())
        .filter(Boolean)
        .filter(name => norm(name) !== 'galeria'))];
    return items.sort((a, b) => {
        const aw = typeof subAlbumSortWeight === 'function' ? subAlbumSortWeight(a) : 99;
        const bw = typeof subAlbumSortWeight === 'function' ? subAlbumSortWeight(b) : 99;
        if (aw !== bw) return aw - bw;
        return a.localeCompare(b, 'es', { numeric:true, sensitivity:'base' });
    });
}
'''
if 'function matchPickerChrono(' not in s:
    s = s.replace('function MatchPickerModal({ albums, onClose, onSelect }) {', helpers + '\nfunction MatchPickerModal({ albums, onClose, onSelect }) {', 1)
elif 'function matchPickerCategories(' not in s:
    s = s.replace('function MatchPickerModal({ albums, onClose, onSelect }) {', helpers.split('function matchPickerCategories(album) {', 1)[1].join(['function matchPickerCategories(album) {', '\nfunction MatchPickerModal({ albums, onClose, onSelect }) {']), 1)

# Selector: newest real match first, oldest last.
s = s.replace(
    '    const all = Array.isArray(albums) ? albums : [];',
    "    const all = Array.isArray(albums) ? [...albums].sort((a, b) => matchPickerChrono(b) - matchPickerChrono(a) || String(a.name || '').localeCompare(String(b.name || ''), 'es', { numeric:true, sensitivity:'base' })) : [];",
    1
)

# Pagination + category state.
if 'const [visibleCount, setVisibleCount]' not in s:
    s = s.replace(
        "    const [query, setQuery] = useState('');",
        "    const [query, setQuery] = useState('');\n    const [visibleCount, setVisibleCount] = useState(10);\n    const [selectedCategory, setSelectedCategory] = useState('todas');",
        1
    )

# Replace the old query-only filtering with query + category filtering and category choices.
filter_block = r'''    const availableCategories = useMemo(() => {
        const categories = new Set();
        all.forEach(album => matchPickerCategories(album).forEach(cat => categories.add(cat)));
        return [...categories].sort((a, b) => {
            const aw = typeof subAlbumSortWeight === 'function' ? subAlbumSortWeight(a) : 99;
            const bw = typeof subAlbumSortWeight === 'function' ? subAlbumSortWeight(b) : 99;
            if (aw !== bw) return aw - bw;
            return a.localeCompare(b, 'es', { numeric:true, sensitivity:'base' });
        });
    }, [albums]);
    const filtered = useMemo(() => {
        const q = norm(query);
        return all.filter(album => {
            const sides = matchPickerSides(album);
            const categories = matchPickerCategories(album);
            const matchesQuery = !q || norm([album && album.name, album && album.dateLabel, sides.home.name, sides.away.name, categories.join(' ')].filter(Boolean).join(' ')).includes(q);
            const matchesCategory = selectedCategory === 'todas' || categories.some(cat => norm(cat) === norm(selectedCategory));
            return matchesQuery && matchesCategory;
        });
    }, [albums, query, selectedCategory]);
    useEffect(() => { setVisibleCount(10); }, [query, selectedCategory]);
    const visibleAlbums = filtered.slice(0, visibleCount);
    const hasMoreMatches = filtered.length > visibleCount;'''
s = re.sub(
    r'    const filtered = useMemo\(\(\) => \{.*?\n    \}, \[all, query\]\);',
    lambda _m: filter_block,
    s,
    count=1,
    flags=re.S
)

# Show corrected dates in cards.
s = s.replace(
    'album.dateLabel ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-calendar" }), album.dateLabel) : null,',
    'matchPickerDateLabel(album) ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-calendar" }), matchPickerDateLabel(album)) : null,',
    1
)

# Add category filters just above the list.
filters_ui = r'''            React.createElement("div", { className: "match-picker-filters", role: "group", "aria-label": "Filtrar por categoría" },
                React.createElement("button", { type: "button", onClick: () => setSelectedCategory('todas'), className: `match-picker-filter-chip ${selectedCategory === 'todas' ? 'active' : ''}`.trim() }, "Todas"),
                availableCategories.map(category => React.createElement("button", { key: category, type: "button", onClick: () => setSelectedCategory(category), className: `match-picker-filter-chip ${selectedCategory === category ? 'active' : ''}`.trim() }, category))),
'''
if 'className: "match-picker-filters"' not in s:
    s = s.replace(
        '            React.createElement("div", { className: "match-picker-list" },',
        filters_ui + '            React.createElement("div", { className: "match-picker-list" },',
        1
    )

# Only render the first 10 filtered matches, then reveal more in batches of 10.
s = s.replace('                filtered.length ? filtered.map(album => {', '                visibleAlbums.length ? visibleAlbums.map(album => {', 1)

# If a category is selected, clicking a match opens that category directly.
if 'preferredSubId' not in s:
    s = s.replace(
        '                    const photoCount = Array.isArray(album.photos) ? album.photos.length : 0;\n                    return React.createElement("button", { key: album.id, type: "button", className: "match-picker-card", onClick: () => onSelect(album) },',
        '                    const photoCount = Array.isArray(album.photos) ? album.photos.length : 0;\n                    const preferredSub = selectedCategory === \'todas\' ? null : (Array.isArray(album.subalbums) ? album.subalbums.find(sa => norm(sa && sa.name) === norm(selectedCategory)) : null);\n                    const preferredSubId = preferredSub && preferredSub.id ? preferredSub.id : \'\';\n                    return React.createElement("button", { key: album.id, type: "button", className: "match-picker-card", onClick: () => onSelect(album, preferredSubId) },',
        1
    )
    s = s.replace(
        'onSelect: album => { const firstSub = (((album && album.subalbums) || [])[0] || {}).id || \'\';',
        'onSelect: (album, preferredSubId) => { const firstSub = preferredSubId || ((((album && album.subalbums) || [])[0] || {}).id || \'\');',
        1
    )

# Add the "Ver más" control and a clearer visible/total count.
old_count = '            React.createElement("div", { className: "match-picker-count" }, `${filtered.length} ${filtered.length === 1 ? \'partido\' : \'partidos\'}`)));'
new_count = '''            hasMoreMatches ? React.createElement("div", { className: "match-picker-more-wrap" },
                React.createElement("button", { type: "button", className: "match-picker-more-btn", onClick: () => setVisibleCount(v => v + 10) }, React.createElement("span", null, "Ver más"), React.createElement("i", { className: "fas fa-chevron-down" }))) : null,
            React.createElement("div", { className: "match-picker-count" }, `${visibleAlbums.length} de ${filtered.length} ${filtered.length === 1 ? 'partido' : 'partidos'}`)));'''
s = s.replace(old_count, new_count, 1)

# Keep the search specifically oriented to teams.
s = s.replace('placeholder: "Buscar equipo, categoría o fecha..."', 'placeholder: "Buscar por equipo..."', 1)

# Broadcast style + filters/pagination styling.
style = r'''
<style id="v113-match-picker-broadcast-style">
  .match-picker-card{
    min-height:112px!important;
    grid-template-columns:92px minmax(0,1fr) 92px!important;
    gap:4px!important;
    padding:12px 8px!important;
    overflow:hidden!important;
  }
  .match-picker-code-row{display:none!important}
  .match-picker-center{z-index:4!important;padding:0 2px!important}
  .match-picker-names{
    margin:0!important;
    white-space:normal!important;
    overflow:visible!important;
    text-overflow:clip!important;
    font-family:'Bebas Neue',Impact,'Arial Narrow',sans-serif!important;
    font-size:clamp(20px,3vw,31px)!important;
    line-height:.95!important;
    letter-spacing:.025em!important;
    font-weight:400!important;
    color:#fff!important;
    text-align:center!important;
    text-transform:uppercase!important;
    text-shadow:0 2px 10px rgba(0,0,0,.38)!important;
  }
  .match-picker-crest-box{
    width:112px!important;
    height:104px!important;
    border:0!important;
    border-radius:0!important;
    background:transparent!important;
    box-shadow:none!important;
    overflow:visible!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    transform:translateX(-24px)!important;
  }
  .match-picker-crest-box.right{justify-self:end!important;transform:translateX(24px)!important}
  .match-picker-crest-fallback{display:none!important}
  .match-picker-crest{width:98px!important;height:98px!important;max-width:none!important;object-fit:contain!important;filter:drop-shadow(0 10px 18px rgba(0,0,0,.42))!important}
  .match-picker-meta{position:relative;z-index:5!important;margin-top:9px!important}
  .match-picker-filters{display:flex;align-items:center;gap:7px;overflow-x:auto;overflow-y:hidden;padding:2px 1px 11px;margin:0 0 2px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
  .match-picker-filters::-webkit-scrollbar{display:none}
  .match-picker-filter-chip{flex:0 0 auto;min-height:34px;padding:7px 12px;border-radius:999px;border:1px solid rgba(125,211,252,.18);background:rgba(15,23,42,.72);color:#bfdbfe!important;font-size:9px;font-weight:950;letter-spacing:.055em;text-transform:uppercase;transition:.18s ease}
  .match-picker-filter-chip:hover{border-color:rgba(96,165,250,.42);background:rgba(30,64,175,.22)}
  .match-picker-filter-chip.active{background:linear-gradient(135deg,#0ea5e9,#2563eb 58%,#1d4ed8);border-color:rgba(186,230,253,.48);color:#fff!important;box-shadow:0 9px 22px rgba(37,99,235,.24),inset 0 1px 0 rgba(255,255,255,.17)}
  .match-picker-more-wrap{display:flex;justify-content:center;margin:10px 0 2px}
  .match-picker-more-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:10px 18px;border-radius:14px;border:1px solid rgba(96,165,250,.30);background:linear-gradient(135deg,#081632 0%,#0b2d73 52%,#1261cf 100%);color:#fff!important;font-size:11px;font-weight:950;box-shadow:inset 0 1px 0 rgba(255,255,255,.14),0 12px 28px rgba(37,99,235,.20)}
  .match-picker-more-btn:active{transform:scale(.985)}

  @media(max-width:640px){
    .match-picker-card{min-height:102px!important;grid-template-columns:66px minmax(0,1fr) 66px!important;gap:2px!important;padding:10px 3px!important}
    .match-picker-names{font-size:clamp(16px,5.1vw,22px)!important;line-height:.94!important;letter-spacing:.018em!important}
    .match-picker-crest-box{width:88px!important;height:92px!important;transform:translateX(-26px)!important}
    .match-picker-crest-box.right{transform:translateX(26px)!important}
    .match-picker-crest{width:80px!important;height:80px!important}
    .match-picker-meta{gap:3px!important;margin-top:7px!important}
    .match-picker-chip{font-size:6.6px!important;padding:3px 5px!important;min-height:19px!important}
    .match-picker-filters{gap:6px;padding-bottom:9px}
    .match-picker-filter-chip{min-height:31px;padding:6px 10px;font-size:8px}
    .match-picker-more-btn{width:100%;min-height:42px;font-size:10px}
  }
</style>
'''
s = re.sub(r'<style id="v112-match-picker-broadcast-style">.*?</style>\s*', '', s, count=1, flags=re.S)
s = re.sub(r'<style id="v113-match-picker-broadcast-style">.*?</style>\s*', '', s, count=1, flags=re.S)
s = s.replace('</head>', style + '</head>', 1)

p.write_text(s, encoding='utf-8')
print('v113 match picker filters patch applied')