from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v117-match-picker-filters'
s = re.sub(r'<meta name="app-version" content="[^"]+"\s*/?>', f'<meta name="app-version" content="{VERSION}" />', s, count=1)

new_block = r'''function canonicalMatchPickerCategory(value) {
    const original = String(value || '').trim();
    if (!original) return '';
    const raw = original.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[._-]+/g, ' ').replace(/\s+/g, ' ').trim();
    const rules = [
        [/^(1ra|1era|primera)(\b|\s)/, 'Primera'],
        [/^(2da|segunda)(\b|\s)/, 'Segunda'],
        [/^(3ra|tercera)(\b|\s)/, 'Tercera'],
        [/^(4ta|cuarta)(\b|\s)/, 'Cuarta'],
        [/^(5ta|quinta)(\b|\s)/, 'Quinta'],
        [/^(6ta|sexta)(\b|\s)/, 'Sexta'],
        [/^(7ma|7ta|septima)(\b|\s)/, 'Séptima'],
        [/^(8va|octava)(\b|\s)/, 'Octava'],
        [/^(9na|novena)(\b|\s)/, 'Novena']
    ];
    for (const [rx, label] of rules) {
        if (rx.test(raw)) return label;
    }
    return original.replace(/\s+/g, ' ').replace(/^./, c => c.toUpperCase());
}

function normalizedMatchPickerCategories(album) {
    const out = [];
    const seen = new Set();
    matchPickerCategories(album).forEach(category => {
        const canonical = canonicalMatchPickerCategory(category);
        const key = norm(canonical);
        if (canonical && key && !seen.has(key)) {
            seen.add(key);
            out.push(canonical);
        }
    });
    return out;
}

function matchPickerTeamFilterKey(side) {
    const name = String((side && side.name) || '').trim();
    return canonicalAppTeamKey(name) || norm(name);
}

function MatchPickerModal({ albums, onClose, onSelect }) {
    const [query, setQuery] = useState('');
    const [visibleCount, setVisibleCount] = useState(10);
    const [selectedCategory, setSelectedCategory] = useState('todas');
    const [selectedTeam, setSelectedTeam] = useState('todos');
    const [teamFilterOpen, setTeamFilterOpen] = useState(false);
    const [categoryFilterOpen, setCategoryFilterOpen] = useState(false);

    const all = Array.isArray(albums)
        ? [...albums].sort((a, b) => matchPickerChrono(b) - matchPickerChrono(a) || String(a.name || '').localeCompare(String(b.name || ''), 'es', { numeric:true, sensitivity:'base' }))
        : [];

    const availableCategories = useMemo(() => {
        const map = new Map();
        all.forEach(album => normalizedMatchPickerCategories(album).forEach(category => {
            const key = norm(category);
            if (key && !map.has(key)) map.set(key, category);
        }));
        const order = ['Primera','Segunda','Tercera','Cuarta','Quinta','Sexta','Séptima','Octava','Novena'];
        const weight = value => {
            const idx = order.indexOf(value);
            return idx >= 0 ? idx : 100;
        };
        return [...map.values()].sort((a, b) => {
            const aw = weight(a), bw = weight(b);
            if (aw !== bw) return aw - bw;
            return a.localeCompare(b, 'es', { numeric:true, sensitivity:'base' });
        });
    }, [albums]);

    const availableTeams = useMemo(() => {
        const map = new Map();
        all.forEach(album => {
            const sides = matchPickerSides(album);
            [sides.home, sides.away].forEach(side => {
                const key = matchPickerTeamFilterKey(side);
                const name = String((side && side.name) || '').trim();
                if (!key || !name || map.has(key)) return;
                map.set(key, {
                    key,
                    name,
                    logo: String((side && (side.logo || side.appLogo)) || findAppTeamLogo(name) || '').trim(),
                    initials: (side && side.initials) || matchPickerInitials(name)
                });
            });
        });
        return [...map.values()].sort((a, b) => a.name.localeCompare(b.name, 'es', { sensitivity:'base', numeric:true }));
    }, [albums]);

    const filtered = useMemo(() => {
        const q = norm(query);
        return all.filter(album => {
            const sides = matchPickerSides(album);
            const categories = normalizedMatchPickerCategories(album);
            const matchesQuery = !q || norm([
                album && album.name,
                album && album.dateLabel,
                sides.home.name,
                sides.away.name,
                categories.join(' ')
            ].filter(Boolean).join(' ')).includes(q);
            const matchesCategory = selectedCategory === 'todas' || categories.some(cat => norm(cat) === norm(selectedCategory));
            const teamKeys = [matchPickerTeamFilterKey(sides.home), matchPickerTeamFilterKey(sides.away)];
            const matchesTeam = selectedTeam === 'todos' || teamKeys.includes(selectedTeam);
            return matchesQuery && matchesCategory && matchesTeam;
        });
    }, [albums, query, selectedCategory, selectedTeam]);

    useEffect(() => { setVisibleCount(10); }, [query, selectedCategory, selectedTeam]);

    const visibleAlbums = filtered.slice(0, visibleCount);
    const hasMoreMatches = filtered.length > visibleCount;
    const selectedTeamOption = availableTeams.find(team => team.key === selectedTeam) || null;

    const miniCrest = (team, extraClass = '') => {
        const logo = String((team && team.logo) || '').trim();
        return React.createElement('span', { className: `match-picker-mini-crest ${extraClass}`.trim(), title: team && team.name ? team.name : '' },
            React.createElement('span', { className: 'match-picker-mini-fallback' }, (team && team.initials) || matchPickerInitials(team && team.name)),
            logo ? React.createElement('img', {
                src: logo,
                alt: '',
                loading: 'lazy',
                decoding: 'async',
                onError: e => { e.currentTarget.style.display = 'none'; }
            }) : null);
    };

    const crest = (side, right = false) => {
        const logo = String((side && (side.logo || side.appLogo)) || '').trim();
        const isParque = isParqueVelezTeamName(side && side.name);
        const classes = `match-picker-crest-box ${right ? 'right' : ''} ${logo ? '' : 'no-logo'} ${isParque ? 'green-fallback' : ''}`.trim();
        return React.createElement('div', { className: classes },
            React.createElement('span', { className: 'match-picker-crest-fallback' }, (side && side.initials) || (isParque ? 'EPV' : matchPickerInitials(side && side.name))),
            logo ? React.createElement('img', {
                src: logo,
                alt: `Escudo ${side.name || ''}`,
                className: 'match-picker-crest',
                loading: 'lazy',
                decoding: 'async',
                onError: e => {
                    const fallback = String((side && side.appLogo) || findAppTeamLogo(side && side.name) || '');
                    if (fallback && e.currentTarget.src !== new URL(fallback, location.href).href) {
                        e.currentTarget.src = fallback;
                        return;
                    }
                    e.currentTarget.style.display = 'none';
                    const box = e.currentTarget.parentElement;
                    if (box) box.classList.add('no-logo');
                }
            }) : null);
    };

    return React.createElement(Modal, { onClose, max: 'max-w-4xl' },
        React.createElement('div', { className: 'match-picker-shell' },
            React.createElement('div', { className: 'match-picker-head' },
                React.createElement('span', { className: 'match-picker-kicker' }, React.createElement('i', { className: 'fas fa-bolt' }), 'Selector de partidos'),
                React.createElement('h2', { className: 'match-picker-title' }, 'Elegí el partido'),
                React.createElement('p', { className: 'match-picker-subtitle' }, 'Buscá o filtrá y entrá directamente a las fotos del cruce que quieras.')),

            React.createElement('div', { className: 'match-picker-search-wrap' },
                React.createElement('i', { className: 'fas fa-magnifying-glass match-picker-search-icon' }),
                React.createElement('input', { value: query, onChange: e => setQuery(e.target.value), className: 'match-picker-search', placeholder: 'Buscar por equipo...', autoFocus: true })),

            React.createElement('div', { className: 'match-picker-filter-bar' },
                React.createElement('button', {
                    type: 'button',
                    className: `match-picker-filter-toggle ${selectedTeam !== 'todos' ? 'active' : ''}`.trim(),
                    onClick: () => { setTeamFilterOpen(v => !v); setCategoryFilterOpen(false); },
                    'aria-expanded': teamFilterOpen
                },
                    React.createElement('i', { className: 'fas fa-shield-halved match-picker-filter-main-icon' }),
                    React.createElement('span', { className: 'match-picker-filter-toggle-copy' },
                        React.createElement('strong', null, 'Filtrar por equipo'),
                        selectedTeamOption ? React.createElement('small', null, selectedTeamOption.name) : null),
                    selectedTeamOption
                        ? miniCrest(selectedTeamOption, 'selected')
                        : React.createElement('span', { className: 'match-picker-filter-team-previews', 'aria-hidden': 'true' }, availableTeams.slice(0, 3).map(team => React.createElement(React.Fragment, { key: team.key }, miniCrest(team, 'preview')))),
                    React.createElement('i', { className: `fas fa-chevron-${teamFilterOpen ? 'up' : 'down'} match-picker-filter-chevron` })),

                React.createElement('button', {
                    type: 'button',
                    className: `match-picker-filter-toggle ${selectedCategory !== 'todas' ? 'active' : ''}`.trim(),
                    onClick: () => { setCategoryFilterOpen(v => !v); setTeamFilterOpen(false); },
                    'aria-expanded': categoryFilterOpen
                },
                    React.createElement('i', { className: 'fas fa-layer-group match-picker-filter-main-icon' }),
                    React.createElement('span', { className: 'match-picker-filter-toggle-copy' },
                        React.createElement('strong', null, 'Filtrar por categoría'),
                        selectedCategory !== 'todas' ? React.createElement('small', null, selectedCategory) : null),
                    React.createElement('i', { className: `fas fa-chevron-${categoryFilterOpen ? 'up' : 'down'} match-picker-filter-chevron` }))),

            teamFilterOpen ? React.createElement('div', { className: 'match-picker-filter-panel match-picker-team-panel' },
                React.createElement('button', {
                    type: 'button',
                    className: `match-picker-filter-option ${selectedTeam === 'todos' ? 'active' : ''}`.trim(),
                    onClick: () => { setSelectedTeam('todos'); setTeamFilterOpen(false); }
                }, React.createElement('span', { className: 'match-picker-filter-option-icon' }, React.createElement('i', { className: 'fas fa-shield-halved' })), React.createElement('span', null, 'Todos los equipos')),
                availableTeams.map(team => React.createElement('button', {
                    key: team.key,
                    type: 'button',
                    className: `match-picker-filter-option ${selectedTeam === team.key ? 'active' : ''}`.trim(),
                    onClick: () => { setSelectedTeam(team.key); setTeamFilterOpen(false); }
                }, miniCrest(team), React.createElement('span', null, team.name)))) : null,

            categoryFilterOpen ? React.createElement('div', { className: 'match-picker-filter-panel match-picker-category-panel' },
                React.createElement('button', {
                    type: 'button',
                    className: `match-picker-filter-option ${selectedCategory === 'todas' ? 'active' : ''}`.trim(),
                    onClick: () => { setSelectedCategory('todas'); setCategoryFilterOpen(false); }
                }, React.createElement('span', { className: 'match-picker-filter-option-icon' }, React.createElement('i', { className: 'fas fa-layer-group' })), React.createElement('span', null, 'Todas las categorías')),
                availableCategories.map(category => React.createElement('button', {
                    key: category,
                    type: 'button',
                    className: `match-picker-filter-option ${selectedCategory === category ? 'active' : ''}`.trim(),
                    onClick: () => { setSelectedCategory(category); setCategoryFilterOpen(false); }
                }, React.createElement('span', { className: 'match-picker-category-dot' }), React.createElement('span', null, category)))) : null,

            React.createElement('div', { className: 'match-picker-list' },
                visibleAlbums.length ? visibleAlbums.map(album => {
                    const { home, away } = matchPickerSides(album);
                    const homeCode = matchPickerInitials(home.name);
                    const awayCode = matchPickerInitials(away.name);
                    const normalizedCategories = normalizedMatchPickerCategories(album);
                    const category = normalizedCategories.length
                        ? normalizedCategories.slice(0, 3).join(' · ') + (normalizedCategories.length > 3 ? ` +${normalizedCategories.length - 3}` : '')
                        : 'Galería';
                    const photoCount = Array.isArray(album.photos) ? album.photos.length : 0;
                    const preferredSub = selectedCategory === 'todas' ? null : (Array.isArray(album.subalbums) ? album.subalbums.find(sa => norm(canonicalMatchPickerCategory(sa && sa.name)) === norm(selectedCategory)) : null);
                    const preferredSubId = preferredSub && preferredSub.id ? preferredSub.id : '';
                    return React.createElement('button', { key: album.id, type: 'button', className: 'match-picker-card', onClick: () => onSelect(album, preferredSubId) },
                        crest(home, false),
                        React.createElement('div', { className: 'match-picker-center' },
                            React.createElement('div', { className: 'match-picker-code-row' }, React.createElement('span', { className: 'match-picker-code' }, homeCode), React.createElement('span', { className: 'match-picker-vs' }, 'VS'), React.createElement('span', { className: 'match-picker-code' }, awayCode)),
                            React.createElement('div', { className: 'match-picker-names' }, `${home.name || 'Local'} · ${away.name || 'Visitante'}`),
                            React.createElement('div', { className: 'match-picker-meta' },
                                matchPickerDateLabel(album) ? React.createElement('span', { className: 'match-picker-chip' }, React.createElement('i', { className: 'far fa-calendar' }), matchPickerDateLabel(album)) : null,
                                React.createElement('span', { className: 'match-picker-chip' }, React.createElement('i', { className: 'fas fa-layer-group' }), category),
                                photoCount ? React.createElement('span', { className: 'match-picker-chip' }, React.createElement('i', { className: 'far fa-image' }), `${photoCount} fotos`) : null,
                                album.archived ? React.createElement('span', { className: 'match-picker-chip archive' }, React.createElement('i', { className: 'fas fa-box-archive' }), 'Archivo') : null)),
                        crest(away, true));
                }) : React.createElement('div', { className: 'match-picker-empty' }, React.createElement('i', { className: 'fas fa-magnifying-glass mb-2' }), React.createElement('div', null, 'No encontré partidos con esos filtros.'))),

            hasMoreMatches ? React.createElement('div', { className: 'match-picker-more-wrap' },
                React.createElement('button', { type: 'button', className: 'match-picker-more-btn', onClick: () => setVisibleCount(v => v + 10) }, React.createElement('span', null, 'Ver más'), React.createElement('i', { className: 'fas fa-chevron-down' }))) : null,
            React.createElement('div', { className: 'match-picker-count' }, `${visibleAlbums.length} de ${filtered.length} ${filtered.length === 1 ? 'partido' : 'partidos'}`)));
}'''

pattern = re.compile(r'function MatchPickerModal\(\{ albums, onClose, onSelect \}\) \{.*?\n\}\n\nfunction App\(\) \{', re.S)
match = pattern.search(s)
if not match:
    raise SystemExit('MatchPickerModal block not found')
s = pattern.sub(lambda m: new_block + '\n\nfunction App() {', s, count=1)

style = r'''
<style id="v117-match-picker-filters-style">
  /* Escudos un poco más grandes, pero con límites estrictos para no invadir el centro */
  .match-picker-crest-box{
    width:116px!important;
    height:108px!important;
    max-width:116px!important;
    max-height:108px!important;
    overflow:visible!important;
  }
  .match-picker-crest{
    width:104px!important;
    height:104px!important;
    max-width:104px!important;
    max-height:104px!important;
    object-fit:contain!important;
  }

  /* Los filtros son botones cerrados por defecto y despliegan contenido en el flujo normal. */
  .match-picker-filter-bar{
    display:grid;
    grid-template-columns:minmax(0,1fr) minmax(0,1fr);
    gap:8px;
    margin:1px 0 10px;
    position:relative;
    z-index:6;
  }
  .match-picker-filter-toggle{
    min-width:0;
    min-height:48px;
    display:flex;
    align-items:center;
    gap:9px;
    padding:8px 11px;
    border-radius:15px;
    border:1px solid rgba(125,211,252,.18);
    background:linear-gradient(145deg,rgba(9,18,36,.96),rgba(11,31,64,.90));
    color:#dbeafe!important;
    text-align:left;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
    transition:.18s ease;
  }
  .match-picker-filter-toggle:hover{border-color:rgba(96,165,250,.40);transform:translateY(-1px)}
  .match-picker-filter-toggle.active{border-color:rgba(56,189,248,.46);background:linear-gradient(145deg,rgba(7,39,75,.98),rgba(13,65,127,.94))}
  .match-picker-filter-main-icon{flex:0 0 auto;width:17px;text-align:center;color:#60a5fa;font-size:13px}
  .match-picker-filter-toggle-copy{display:flex;flex:1;min-width:0;flex-direction:column;gap:2px}
  .match-picker-filter-toggle-copy strong{font-size:10px;line-height:1.08;font-weight:950;letter-spacing:.035em;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .match-picker-filter-toggle-copy small{font-size:8px;line-height:1.1;color:#93c5fd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .match-picker-filter-chevron{flex:0 0 auto;color:#64748b;font-size:9px}

  .match-picker-filter-team-previews{display:flex;align-items:center;flex:0 0 auto;margin-left:auto;padding-left:2px}
  .match-picker-filter-team-previews .match-picker-mini-crest + .match-picker-mini-crest{margin-left:-7px}
  .match-picker-mini-crest{
    position:relative;
    width:30px;
    height:30px;
    flex:0 0 30px;
    display:grid;
    place-items:center;
    border-radius:9px;
    overflow:hidden;
    background:#07101f;
    border:1px solid rgba(148,163,184,.18);
    box-shadow:0 4px 12px rgba(0,0,0,.24);
  }
  .match-picker-mini-crest.preview{width:25px;height:25px;flex-basis:25px;border-radius:8px}
  .match-picker-mini-crest.selected{width:31px;height:31px;flex-basis:31px}
  .match-picker-mini-crest img{position:relative;z-index:2;width:88%;height:88%;object-fit:contain;display:block}
  .match-picker-mini-fallback{position:absolute;z-index:1;font-family:'Bebas Neue',Impact,sans-serif;font-size:11px;color:#93a4ba;letter-spacing:.03em}

  .match-picker-filter-panel{
    position:static!important;
    z-index:auto!important;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(145px,1fr));
    gap:7px;
    width:100%;
    max-height:250px;
    overflow-y:auto;
    overflow-x:hidden;
    margin:-2px 0 11px;
    padding:9px;
    border-radius:16px;
    border:1px solid rgba(96,165,250,.16);
    background:linear-gradient(180deg,rgba(4,10,22,.98),rgba(6,18,38,.97));
    box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
    scrollbar-width:thin;
  }
  .match-picker-filter-option{
    min-width:0;
    min-height:42px;
    display:flex;
    align-items:center;
    gap:9px;
    padding:7px 9px;
    border-radius:12px;
    border:1px solid rgba(148,163,184,.12);
    background:rgba(15,23,42,.68);
    color:#e2e8f0!important;
    font-size:9px;
    line-height:1.12;
    font-weight:900;
    text-align:left;
    text-transform:uppercase;
    transition:.15s ease;
  }
  .match-picker-filter-option:hover{background:rgba(30,64,175,.24);border-color:rgba(96,165,250,.32)}
  .match-picker-filter-option.active{background:linear-gradient(135deg,rgba(14,165,233,.32),rgba(37,99,235,.36));border-color:rgba(125,211,252,.44);color:#fff!important}
  .match-picker-filter-option .match-picker-mini-crest{width:29px;height:29px;flex-basis:29px;border-radius:8px}
  .match-picker-filter-option-icon{width:29px;height:29px;flex:0 0 29px;display:grid;place-items:center;border-radius:8px;background:rgba(37,99,235,.18);color:#60a5fa}
  .match-picker-category-dot{width:9px;height:9px;flex:0 0 9px;border-radius:999px;background:#38bdf8;box-shadow:0 0 0 4px rgba(56,189,248,.10)}

  @media(max-width:640px){
    .match-picker-crest-box{width:92px!important;height:94px!important;max-width:92px!important;max-height:94px!important}
    .match-picker-crest{width:84px!important;height:84px!important;max-width:84px!important;max-height:84px!important}
    .match-picker-filter-bar{gap:6px;margin-bottom:8px}
    .match-picker-filter-toggle{min-height:44px;padding:7px 8px;gap:6px;border-radius:13px}
    .match-picker-filter-main-icon{width:14px;font-size:11px}
    .match-picker-filter-toggle-copy strong{font-size:8.4px;letter-spacing:.02em}
    .match-picker-filter-toggle-copy small{font-size:7.2px}
    .match-picker-mini-crest.preview{width:21px;height:21px;flex-basis:21px;border-radius:7px}
    .match-picker-filter-team-previews .match-picker-mini-crest + .match-picker-mini-crest{margin-left:-6px}
    .match-picker-mini-crest.selected{width:25px;height:25px;flex-basis:25px}
    .match-picker-filter-panel{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;max-height:220px;padding:7px;margin-bottom:9px}
    .match-picker-filter-option{min-height:39px;padding:6px 7px;font-size:7.7px;gap:7px;border-radius:11px}
    .match-picker-filter-option .match-picker-mini-crest{width:26px;height:26px;flex-basis:26px}
    .match-picker-filter-option-icon{width:26px;height:26px;flex-basis:26px}
  }
  @media(max-width:390px){
    .match-picker-filter-bar{grid-template-columns:1fr}
    .match-picker-filter-panel{grid-template-columns:1fr 1fr}
  }
</style>
'''

s = re.sub(r'\n?<style id="v117-match-picker-filters-style">.*?</style>\n?', '\n', s, flags=re.S)
if '</head>' not in s:
    raise SystemExit('</head> not found')
s = s.replace('</head>', style + '\n</head>', 1)

p.write_text(s, encoding='utf-8')
print('Applied', VERSION)
