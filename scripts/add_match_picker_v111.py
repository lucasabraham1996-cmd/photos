from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s = s.replace('content="v110-blank-screen-fix"', 'content="v111-mobile-match-picker"', 1)
s = s.replace('const APP_VERSION = "v110-blank-screen-fix";', 'const APP_VERSION = "v111-mobile-match-picker";', 1)

css = r'''
  <style id="v111-match-picker-styles">
    .home-quick-actions{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:0 auto 16px;width:100%}.home-quick-actions .booking-btn{min-width:min(260px,100%)}
    .match-picker-open-btn{position:relative;overflow:hidden;background:linear-gradient(135deg,#050505 0%,#0f172a 34%,#1d4ed8 72%,#020617 100%)!important;color:#fff!important;border:1px solid rgba(125,211,252,.38)!important;box-shadow:0 18px 44px rgba(37,99,235,.22),inset 0 1px 0 rgba(255,255,255,.12)!important;transition:.22s}.match-picker-open-btn:hover{transform:translateY(-1px);border-color:rgba(186,230,253,.75)!important}.match-picker-open-btn:before{content:"";position:absolute;inset:0;background:linear-gradient(105deg,transparent,rgba(255,255,255,.12),transparent);transform:translateX(-125%);transition:transform .65s ease}.match-picker-open-btn:hover:before{transform:translateX(125%)}.match-picker-open-btn *{color:#fff!important;position:relative;z-index:1}
    .match-picker-shell{margin:-4px;color:#fff}.match-picker-head{padding:2px 44px 14px 0;border-bottom:1px solid rgba(255,255,255,.08)}.match-picker-kicker{display:inline-flex;align-items:center;gap:7px;padding:6px 9px;border-radius:999px;background:rgba(37,99,235,.15);border:1px solid rgba(96,165,250,.24);color:#93c5fd!important;font-size:9px;font-weight:950;letter-spacing:.13em;text-transform:uppercase}.match-picker-title{font-size:clamp(25px,5vw,38px);line-height:.95;margin:10px 0 5px;font-weight:950;letter-spacing:-.04em;color:#fff!important}.match-picker-subtitle{font-size:12px;line-height:1.45;color:#94a3b8!important;margin:0}.match-picker-search-wrap{position:sticky;top:-20px;z-index:8;padding:12px 0 10px;background:linear-gradient(180deg,#171717 0%,rgba(23,23,23,.98) 82%,rgba(23,23,23,0) 100%)}.match-picker-search{width:100%;height:48px;border-radius:15px;border:1px solid rgba(125,211,252,.18);background:#070b13!important;color:#fff!important;-webkit-text-fill-color:#fff!important;padding:0 14px 0 42px;outline:none;font-size:14px;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}.match-picker-search:focus{border-color:rgba(96,165,250,.58);box-shadow:0 0 0 3px rgba(59,130,246,.11)}.match-picker-search::placeholder{color:#64748b!important;-webkit-text-fill-color:#64748b!important}.match-picker-search-icon{position:absolute;left:15px;top:27px;color:#60a5fa;font-size:13px;z-index:2}.match-picker-list{display:grid;gap:10px;padding:2px 0 5px}
    .match-picker-card{position:relative;width:100%;min-height:106px;display:grid;grid-template-columns:82px minmax(0,1fr) 82px;align-items:center;gap:12px;padding:12px 14px;border-radius:20px;border:1px solid rgba(96,165,250,.16);background:radial-gradient(circle at 50% 0%,rgba(59,130,246,.16),transparent 42%),linear-gradient(112deg,#050a14 0%,#0a1732 48%,#061126 100%);overflow:hidden;text-align:left;box-shadow:0 13px 34px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.06);transition:.22s ease}.match-picker-card:before{content:"";position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,#2563eb,#38bdf8 48%,#2563eb);opacity:.92}.match-picker-card:after{content:"";position:absolute;inset:0;background:linear-gradient(112deg,transparent 25%,rgba(255,255,255,.055) 49%,transparent 72%),repeating-linear-gradient(135deg,rgba(255,255,255,.027) 0 1px,transparent 1px 11px);pointer-events:none}.match-picker-card:hover{transform:translateY(-2px);border-color:rgba(96,165,250,.38);box-shadow:0 18px 44px rgba(37,99,235,.18),inset 0 1px 0 rgba(255,255,255,.08)}.match-picker-card>*{position:relative;z-index:2}
    .match-picker-crest-box{width:70px;height:70px;border-radius:18px;display:grid;place-items:center;background:rgba(2,6,23,.52);border:1px solid rgba(255,255,255,.09);box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}.match-picker-crest-box.right{justify-self:end}.match-picker-crest-fallback{position:absolute;font-family:Impact,"Arial Narrow",Inter,sans-serif;font-size:22px;letter-spacing:.04em;color:#64748b!important}.match-picker-crest{position:relative;z-index:1;width:55px;height:55px;object-fit:contain;filter:drop-shadow(0 7px 10px rgba(0,0,0,.38))}.match-picker-center{min-width:0;text-align:center}.match-picker-code-row{display:flex;align-items:center;justify-content:center;gap:10px;min-width:0}.match-picker-code{font-family:Impact,"Arial Narrow",Inter,sans-serif;font-size:clamp(29px,5vw,42px);line-height:.86;letter-spacing:.055em;color:#f8fafc!important;text-transform:uppercase;white-space:nowrap}.match-picker-vs{font-family:Impact,"Arial Narrow",Inter,sans-serif;font-size:17px;line-height:1;color:#60a5fa!important;letter-spacing:.08em}.match-picker-names{margin-top:6px;font-size:10px;font-weight:850;color:#cbd5e1!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-transform:uppercase;letter-spacing:.04em}.match-picker-meta{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:5px;margin-top:8px}.match-picker-chip{display:inline-flex;align-items:center;gap:5px;min-height:23px;padding:4px 7px;border-radius:999px;background:rgba(15,23,42,.72);border:1px solid rgba(148,163,184,.14);color:#bfdbfe!important;font-size:8px;font-weight:900;letter-spacing:.055em;text-transform:uppercase;white-space:nowrap}.match-picker-chip.archive{color:#fde68a!important;border-color:rgba(245,158,11,.20);background:rgba(120,53,15,.20)}.match-picker-count{margin-top:10px;text-align:center;color:#64748b!important;font-size:10px;font-weight:800}.match-picker-empty{padding:28px 18px;border:1px dashed rgba(148,163,184,.18);border-radius:20px;text-align:center;color:#94a3b8!important;background:rgba(2,6,23,.35)}body.light-mode .match-picker-shell,body.light-mode .match-picker-shell *,body.light-mode .match-picker-open-btn,body.light-mode .match-picker-open-btn *{color:#fff!important}
    @media(max-width:640px){.home-quick-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:7px!important;margin:14px 0 16px!important}.home-quick-actions>button{width:100%!important;min-width:0!important;min-height:48px!important;padding:10px 8px!important;border-radius:14px!important;font-size:10.5px!important;line-height:1.05!important}.home-quick-actions>button i{margin-right:4px!important}.match-picker-shell{margin:-3px}.match-picker-head{padding:2px 42px 12px 0}.match-picker-title{font-size:26px}.match-picker-subtitle{font-size:10.5px}.match-picker-search-wrap{top:-20px;padding:10px 0 8px}.match-picker-search{height:44px;font-size:13px;padding-left:39px}.match-picker-search-icon{left:14px;top:24px}.match-picker-list{gap:8px}.match-picker-card{min-height:96px;grid-template-columns:55px minmax(0,1fr) 55px;gap:7px;padding:10px 9px;border-radius:17px}.match-picker-crest-box{width:52px;height:52px;border-radius:14px}.match-picker-crest{width:41px;height:41px}.match-picker-crest-fallback{font-size:18px}.match-picker-code-row{gap:7px}.match-picker-code{font-size:29px;letter-spacing:.04em}.match-picker-vs{font-size:13px}.match-picker-names{font-size:8px;margin-top:4px}.match-picker-meta{gap:4px;margin-top:6px}.match-picker-chip{font-size:7px;min-height:20px;padding:3px 6px}}
  </style>
'''
if 'id="v111-match-picker-styles"' not in s:
    s = s.replace('</head>', css + '</head>', 1)

component = r'''
function matchPickerInitials(name = '') {
    const ignored = new Set(['club','atletico','atlético','de','del','la','el','los','las','y','cordoba','córdoba']);
    const rawWords = String(name || '').trim().split(/\s+/).filter(Boolean);
    const words = rawWords.filter(w => !ignored.has(norm(w)));
    return (words.length ? words : rawWords).slice(0, 3).map(w => String(w).charAt(0)).join('').toUpperCase().slice(0, 3) || '--';
}
function matchPickerCategory(album) {
    const items = [...new Set((Array.isArray(album && album.subalbums) ? album.subalbums : []).map(s => String((s && s.name) || '').trim()).filter(Boolean).filter(n => norm(n) !== 'galeria'))];
    if (!items.length) return 'Galería';
    return items.slice(0, 3).join(' · ') + (items.length > 3 ? ` +${items.length - 3}` : '');
}
function matchPickerSides(album) {
    let home = albumTeamSide(album, 0, true);
    let away = albumTeamSide(album, 1, true);
    if (!away.name) {
        const parts = String((album && album.name) || '').split(/\s+(?:vs\.?|v\.?|versus|[-–—])\s+/i).map(x => x.trim()).filter(Boolean);
        if (parts.length >= 2) {
            if (!home.name || home.name === album.name) home = { ...home, name: parts[0] };
            away = { ...away, name: parts.slice(1).join(' ') };
        }
    }
    return { home, away };
}
function MatchPickerModal({ albums, onClose, onSelect }) {
    const [query, setQuery] = useState('');
    useEffect(() => { const onKey = e => { if (e.key === 'Escape') onClose(); }; document.addEventListener('keydown', onKey); return () => document.removeEventListener('keydown', onKey); }, [onClose]);
    const list = useMemo(() => {
        const all = Array.isArray(albums) ? [...albums].sort((a,b)=>(b.dateTs||0)-(a.dateTs||0)||String(a.name||'').localeCompare(String(b.name||''))) : [];
        const q = norm(query);
        if (!q) return all;
        return all.filter(album => { const sides = matchPickerSides(album); return norm([album && album.name, album && album.dateLabel, sides.home.name, sides.away.name, matchPickerCategory(album)].filter(Boolean).join(' ')).includes(q); });
    }, [albums, query]);
    const crest = (side, right = false) => React.createElement("div", { className: `match-picker-crest-box ${right ? 'right' : ''}`.trim() }, React.createElement("span", { className: "match-picker-crest-fallback" }, matchPickerInitials(side && side.name)), side && side.logo ? React.createElement("img", { src: side.logo, alt: `Escudo ${side.name || ''}`, className: "match-picker-crest", loading: "lazy", decoding: "async", onError: e => { e.currentTarget.style.display = 'none'; } }) : null);
    return React.createElement(Modal, { onClose, max: "max-w-4xl" },
        React.createElement("div", { className: "match-picker-shell" },
            React.createElement("div", { className: "match-picker-head" }, React.createElement("span", { className: "match-picker-kicker" }, React.createElement("i", { className: "fas fa-futbol" }), " Galerías por partido"), React.createElement("h2", { className: "match-picker-title" }, "Seleccionar partido"), React.createElement("p", { className: "match-picker-subtitle" }, "Elegí el cruce y entrá directamente a sus fotos. Incluye partidos actuales y galerías anteriores.")),
            React.createElement("div", { className: "match-picker-search-wrap" }, React.createElement("i", { className: "fas fa-magnifying-glass match-picker-search-icon" }), React.createElement("input", { value: query, onChange: e => setQuery(e.target.value), className: "match-picker-search", placeholder: "Buscar equipo, categoría o fecha...", autoFocus: true })),
            React.createElement("div", { className: "match-picker-list" }, list.length ? list.map(album => { const { home, away } = matchPickerSides(album); const photoCount = Array.isArray(album.photos) ? album.photos.length : 0; return React.createElement("button", { key: album.id, type: "button", className: "match-picker-card", onClick: () => onSelect(album) }, crest(home, false), React.createElement("div", { className: "match-picker-center" }, React.createElement("div", { className: "match-picker-code-row" }, React.createElement("span", { className: "match-picker-code" }, matchPickerInitials(home.name)), React.createElement("span", { className: "match-picker-vs" }, "VS"), React.createElement("span", { className: "match-picker-code" }, matchPickerInitials(away.name))), React.createElement("div", { className: "match-picker-names" }, `${home.name || 'Local'} · ${away.name || 'Visitante'}`), React.createElement("div", { className: "match-picker-meta" }, album.dateLabel ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-calendar" }), album.dateLabel) : null, React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "fas fa-layer-group" }), matchPickerCategory(album)), photoCount ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-image" }), `${photoCount} fotos`) : null, album.archived ? React.createElement("span", { className: "match-picker-chip archive" }, React.createElement("i", { className: "fas fa-box-archive" }), "Archivo") : null)), crest(away, true)); }) : React.createElement("div", { className: "match-picker-empty" }, "No encontré partidos con esa búsqueda.")),
            React.createElement("div", { className: "match-picker-count" }, `${list.length} ${list.length === 1 ? 'partido' : 'partidos'}`)));
}
'''
if 'function MatchPickerModal(' not in s:
    s = s.replace('function App() {', component + '\nfunction App() {', 1)

if 'const [matchPickerOpen, setMatchPickerOpen]' not in s:
    s = s.replace('    const [bookingOpen, setBookingOpen] = useState(false);\n', '    const [bookingOpen, setBookingOpen] = useState(false);\n    const [matchPickerOpen, setMatchPickerOpen] = useState(false);\n', 1)

old_button = '''                !currentAlbum && React.createElement("div", { className:"price-button-only" },
                    React.createElement("button", { onClick:() => setBookingOpen(true), className:"booking-btn px-5 py-4 rounded-2xl font-black" }, React.createElement("i", { className:"fas fa-tags mr-2" }), "Consultar precios")),'''
new_button = '''                !currentAlbum && React.createElement("div", { className:"home-quick-actions price-button-only" },
                    React.createElement("button", { onClick:() => setBookingOpen(true), className:"booking-btn px-5 py-4 rounded-2xl font-black", type:"button" }, React.createElement("i", { className:"fas fa-tags mr-2" }), "Consultar precios"),
                    React.createElement("button", { onClick:() => setMatchPickerOpen(true), className:"match-picker-open-btn px-5 py-4 rounded-2xl font-black", type:"button" }, React.createElement("i", { className:"fas fa-futbol mr-2" }), "Seleccionar partido")),'''
if 'setMatchPickerOpen(true)' not in s:
    if old_button not in s:
        raise RuntimeError('No se encontró el botón Consultar precios esperado')
    s = s.replace(old_button, new_button, 1)

if 'React.createElement(MatchPickerModal' not in s:
    modal_old = '        bookingOpen && React.createElement(PriceModal, { onClose: () => setBookingOpen(false), priceSettings: priceSettings }),\n'
    modal_new = '        bookingOpen && React.createElement(PriceModal, { onClose: () => setBookingOpen(false), priceSettings: priceSettings }),\n        matchPickerOpen && React.createElement(MatchPickerModal, { albums: displayAlbums, onClose: () => setMatchPickerOpen(false), onSelect: album => { const firstSub = (Array.isArray(album && album.subalbums) && album.subalbums[0] && album.subalbums[0].id) || ""; setMatchPickerOpen(false); location.hash = albumHash(album.id, firstSub); } }),\n'
    if modal_old not in s:
        raise RuntimeError('No se encontró PriceModal para insertar MatchPickerModal')
    s = s.replace(modal_old, modal_new, 1)

p.write_text(s, encoding='utf-8')
print('match picker v111 applied')
