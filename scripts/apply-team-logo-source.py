#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'index.html'
s = INDEX.read_text(encoding='utf-8')

MARKER = '// v106: escudos APP por club + selector APP/Hoja por álbum'
if MARKER in s:
    print('Team logo source feature already applied.')
    raise SystemExit(0)

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    s = s.replace(old, new, 1)

def replace_count(old, new, expected, label):
    global s
    count = s.count(old)
    if count != expected:
        raise RuntimeError(f'{label}: expected {expected} matches, found {count}')
    s = s.replace(old, new)

logos = {
    'all_boys': 'https://i.postimg.cc/Vkvy6VmY/All-Boys.png',
    'almirante_brown': 'https://i.postimg.cc/K8jXzHxR/Almirante-Brown.png',
    'amsurbac': 'https://i.postimg.cc/cLCqHb0v/Amsurbac.png',
    'argentino_penarol': 'https://i.postimg.cc/8zc850Ns/Argentino-Penarol.png',
    'atalaya': 'https://i.postimg.cc/BnbW6V48/Atalaya.png',
    'atletico_carlos_paz': 'https://i.postimg.cc/wjMKvGgN/Atletico-Carlos-Paz.png',
    'avellaneda': 'https://i.postimg.cc/pLrNT6R8/Avellaneda.png',
    'banfield': 'https://i.postimg.cc/jS2V5FtP/Banfield.png',
    'barrio_parque': 'https://i.postimg.cc/rws6mPMC/Barrio-Parque.png',
    'belgrano': 'https://i.postimg.cc/RZhrFD4R/Belgrano.png',
    'bella_vista': 'https://i.postimg.cc/HknGxhdz/Bella-Vista.png',
    'calera_central': 'https://i.postimg.cc/dV3M1xw4/Calera-Central.png',
    'cambioneros': 'https://i.postimg.cc/K8H6gD8n/Cambioneros.png',
    'cibi': 'https://i.postimg.cc/T34zWJ3J/CIBI.png',
    'club_coronel_olmedo': 'https://i.postimg.cc/Jz2fB5zq/Club-Coronel-Olmedo.png',
    'defensores_central_cordoba': 'https://i.postimg.cc/bwB729wL/Defensores-Central-Cordoba.png',
    'deportivo_alberdi': 'https://i.postimg.cc/kgp0tvgf/Deportivo-Alberdi.png',
    'deportivo_defensores_juveniles': 'https://i.postimg.cc/Njz3rkjn/Deportivo-Defensores-Junveniles.png',
    'deportivo_norte': 'https://i.postimg.cc/7ZWFTnZc/Deportivo-Norte.png',
    'dief': 'https://i.postimg.cc/mg5vFyrf/DIEF.png',
    'el_carmen': 'https://i.postimg.cc/W1HBJw4c/El-Carmen.png',
    'escuela_presidente_roca': 'https://i.postimg.cc/SxvBzfKq/Escuela-Presidente-Roca.png',
    'general_paz_junior': 'https://i.postimg.cc/jjnG6nD1/General-Paz-Junior.png',
    'huracan': 'https://i.postimg.cc/VN0390JT/Huracan.png',
    'independiente': 'https://i.postimg.cc/VN0390Jp/Independiente.png',
    'instituto': 'https://i.postimg.cc/N02W82K3/Instituto.png',
    'juvenil_barrio_comercial': 'https://i.postimg.cc/q769c6tf/Juvenil-Barrio-Comercial.png',
    'la_union_malvinas': 'https://i.postimg.cc/Zqv1Pv9z/La-Union-Malvinas.png',
    'las_flores': 'https://i.postimg.cc/Zqv1Pv9m/Las-Flores.png',
    'las_palmas': 'https://i.postimg.cc/0NKLGK6P/Las-Palmas.png',
    'lasallano': 'https://i.postimg.cc/d0ZzRZ7q/Lasallano.png',
    'libertad': 'https://i.postimg.cc/25LPdLqk/Libertad.png',
    'lobos_del_sur': 'https://i.postimg.cc/CKnWCnZx/Lobos-del-Sur.png',
    'los_andes': 'https://i.postimg.cc/W4qQmqD4/Los-Andes.png',
    'medea': 'https://i.postimg.cc/5tQZ5QHy/Medea.png',
    'quilmes': 'https://i.postimg.cc/Lsgrkgqh/Quilmes.png',
    'racing': 'https://i.postimg.cc/Lsgrkgqg/Racing.png',
    'rancagua': 'https://i.postimg.cc/QMKRgKBT/Rancagua.png',
    'recreativo_municipalidad': 'https://i.postimg.cc/LsgrkgqZ/Recreativo-Municipalidad.png',
    'san_lorenzo': 'https://i.postimg.cc/76vjKP7Z/San-Lorenzo.png',
    'san_nicolas': 'https://i.postimg.cc/3RMztrpw/San-Nicolas.png',
    'talleres': 'https://i.postimg.cc/G206X3YH/Talleres.png',
    'union_florida': 'https://i.postimg.cc/cHqPF1Yv/Union-Florida.png',
    'union_san_vicente': 'https://i.postimg.cc/3RMztrp0/Union-San-Vicente.png',
    'union_serrana': 'https://i.postimg.cc/26pg0jvW/Union-Serrana.png',
    'universitario': 'https://i.postimg.cc/76vjKP77/Universitario.png',
    'valores': 'https://i.postimg.cc/sXFbTfS7/Valores.png',
    'villa_azalaiz': 'https://i.postimg.cc/hjFN24xV/Villa-Azalaiz.png',
    'villa_siburu': 'https://i.postimg.cc/j5VBMqNH/Villa-Siburu.png'
}

aliases = {
    'caab': 'all_boys',
    'club_atletico_all_boys': 'all_boys',
    'club_all_boys': 'all_boys',
    'all_boys_cordoba': 'all_boys',
    'club_atletico_almirante_brown': 'almirante_brown',
    'club_amsurbac': 'amsurbac',
    'argentino_penarol_cordoba': 'argentino_penarol',
    'club_atalaya': 'atalaya',
    'club_atletico_carlos_paz': 'atletico_carlos_paz',
    'carlos_paz': 'atletico_carlos_paz',
    'club_avellaneda': 'avellaneda',
    'club_atletico_barrio_parque': 'barrio_parque',
    'cabp': 'barrio_parque',
    'club_atletico_belgrano': 'belgrano',
    'belgrano_de_cordoba': 'belgrano',
    'club_bella_vista': 'bella_vista',
    'club_calera_central': 'calera_central',
    'camioneros': 'cambioneros',
    'club_camioneros': 'cambioneros',
    'coronel_olmedo': 'club_coronel_olmedo',
    'central_cordoba': 'defensores_central_cordoba',
    'defensores_central_cordoba': 'defensores_central_cordoba',
    'defensores_juveniles': 'deportivo_defensores_juveniles',
    'deportivo_defensores_juveniles_cordoba': 'deportivo_defensores_juveniles',
    'deportivo_defensores_junveniles': 'deportivo_defensores_juveniles',
    'presidente_roca': 'escuela_presidente_roca',
    'general_paz_juniors': 'general_paz_junior',
    'general_paz_junior': 'general_paz_junior',
    'huracan_de_cordoba': 'huracan',
    'independiente_de_cordoba': 'independiente',
    'instituto_atletico_central_cordoba': 'instituto',
    'instituto_acc': 'instituto',
    'comercial': 'juvenil_barrio_comercial',
    'barrio_comercial': 'juvenil_barrio_comercial',
    'juvenil_comercial': 'juvenil_barrio_comercial',
    'la_union': 'la_union_malvinas',
    'union_malvinas': 'la_union_malvinas',
    'club_las_flores': 'las_flores',
    'club_las_palmas': 'las_palmas',
    'deportivo_lasallano': 'lasallano',
    'club_libertad': 'libertad',
    'club_los_andes': 'los_andes',
    'medeA': 'medea',
    'racing_de_cordoba': 'racing',
    'club_atletico_racing': 'racing',
    'recreativo_municipalidad_de_cordoba': 'recreativo_municipalidad',
    'club_atletico_san_lorenzo': 'san_lorenzo',
    'club_san_nicolas': 'san_nicolas',
    'club_atletico_talleres': 'talleres',
    'talleres_de_cordoba': 'talleres',
    'club_union_florida': 'union_florida',
    'club_union_san_vicente': 'union_san_vicente',
    'club_union_serrana': 'union_serrana',
    'universitario_de_cordoba': 'universitario',
    'club_valores': 'valores',
    'club_villa_azalaiz': 'villa_azalaiz',
    'club_villa_siburu': 'villa_siburu'
}
# Fix the one intentionally mixed-case source key before serializing.
aliases['medea'] = aliases.pop('medeA')

if len(logos) != 49:
    raise RuntimeError(f'Expected 49 supplied team logos, got {len(logos)}')

replace_once('const LS_COVER_KEY = "la_cover_overrides_v2";\n', 'const LS_COVER_KEY = "la_cover_overrides_v2";\nconst LS_LOGO_SOURCE_KEY = "la_album_logo_sources_v1";\n', 'local logo source key')

catalog = MARKER + '\nconst TEAM_APP_LOGOS = Object.freeze(' + json.dumps(logos, ensure_ascii=False, indent=4) + ');\nconst TEAM_APP_LOGO_ALIASES = Object.freeze(' + json.dumps(aliases, ensure_ascii=False, indent=4) + ');\n'
replace_once('const BRAND_LOGO_URL = "./brand-logo.png?v=105";\n', 'const BRAND_LOGO_URL = "./brand-logo.png?v=105";\n' + catalog, 'team logo catalog')

helpers = r'''function canonicalAppTeamKey(name) {
    const n = norm(name);
    if (!n) return '';
    if (TEAM_APP_LOGOS[n]) return n;
    if (TEAM_APP_LOGO_ALIASES[n] && TEAM_APP_LOGOS[TEAM_APP_LOGO_ALIASES[n]]) return TEAM_APP_LOGO_ALIASES[n];
    const candidates = [...Object.keys(TEAM_APP_LOGO_ALIASES), ...Object.keys(TEAM_APP_LOGOS)]
        .filter(Boolean)
        .sort((a, b) => b.length - a.length);
    for (const candidate of candidates) {
        if (candidate.length < 5) continue;
        const bounded = n === candidate || n.startsWith(candidate + '_') || n.endsWith('_' + candidate) || n.includes('_' + candidate + '_');
        if (!bounded) continue;
        const key = TEAM_APP_LOGO_ALIASES[candidate] || candidate;
        if (TEAM_APP_LOGOS[key]) return key;
    }
    return '';
}
function findAppTeamLogo(name) {
    const key = canonicalAppTeamKey(name);
    return key ? TEAM_APP_LOGOS[key] || '' : '';
}
function isTalleresSanLorenzoAlbum(album) {
    const labels = [album && album.name, album && album.sourceName]
        .concat(Array.isArray(album && album.subalbums) ? album.subalbums.map(sa => sa && sa.sourceName) : [])
        .filter(Boolean);
    return labels.some(label => {
        const n = norm(label);
        return n.includes('talleres') && n.includes('san_lorenzo');
    });
}
function getAlbumLogoSource(album, overrides = {}) {
    const selected = album && album.id ? overrides[album.id] : '';
    if (selected === 'app' || selected === 'sheet') return selected;
    return isTalleresSanLorenzoAlbum(album) ? 'sheet' : 'app';
}
function applyAlbumLogoSource(album, overrides = {}) {
    if (!album) return album;
    const logoSource = getAlbumLogoSource(album, overrides);
    const teamEntries = (Array.isArray(album.teamEntries) ? album.teamEntries : []).map(team => {
        const sheetLogo = String((team && team.sheetLogo) || (team && team.logo) || '').trim();
        const appLogo = String((team && team.appLogo) || findAppTeamLogo((team && team.fullName) || (team && team.name) || '') || '').trim();
        const logo = logoSource === 'sheet' ? (sheetLogo || appLogo) : (appLogo || sheetLogo);
        return { ...(team || {}), sheetLogo, appLogo, logo, logoSource };
    });
    return {
        ...album,
        logoSource,
        teamEntries,
        teamLogo: (teamEntries[0] && teamEntries[0].logo) || album.teamLogo || ''
    };
}
'''
replace_once('function parseTeamCell(rawValue, fallbackName = \'\', sourceCell = \'\') {\n', helpers + 'function parseTeamCell(rawValue, fallbackName = \'\', sourceCell = \'\') {\n', 'team logo resolver helpers')

storage_helpers = '''function readAlbumLogoSources() { try {\n    const saved = JSON.parse(localStorage.getItem(LS_LOGO_SOURCE_KEY) || '{}');\n    return saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {};\n}\ncatch (_a) {\n    return {};\n} }\nfunction saveAlbumLogoSources(data) { try { localStorage.setItem(LS_LOGO_SOURCE_KEY, JSON.stringify(data || {})); } catch (e) { } }\n'''
replace_once('function loadCoverOverrides() { try {\n', storage_helpers + 'function loadCoverOverrides() { try {\n', 'logo source local storage helpers')

replace_once('            coverOverrides: cached.coverOverrides || loadCoverOverrides(),\n            highlightIds: Array.isArray(cached.highlightIds) ? cached.highlightIds : readHighlightIds(),', '            coverOverrides: cached.coverOverrides || loadCoverOverrides(),\n            albumLogoSources: cached.albumLogoSources || readAlbumLogoSources(),\n            highlightIds: Array.isArray(cached.highlightIds) ? cached.highlightIds : readHighlightIds(),', 'shared cache read')
replace_once('        return { discountSettings: readDiscountSettings(), coupons: readCoupons(), bannerSettings: { ...readBannerSettings(), visible: false }, priceSettings: defaultPriceSettings(), watermarkSettings: readWatermarkSettings(), coverOverrides: loadCoverOverrides(), highlightIds: readHighlightIds(), updatedAt: \'\' };', '        return { discountSettings: readDiscountSettings(), coupons: readCoupons(), bannerSettings: { ...readBannerSettings(), visible: false }, priceSettings: defaultPriceSettings(), watermarkSettings: readWatermarkSettings(), coverOverrides: loadCoverOverrides(), albumLogoSources: readAlbumLogoSources(), highlightIds: readHighlightIds(), updatedAt: \'\' };', 'shared cache fallback')
replace_once('    if (next.coverOverrides)\n        saveCoverOverrides(next.coverOverrides);\n    if (Array.isArray(next.highlightIds))', '    if (next.coverOverrides)\n        saveCoverOverrides(next.coverOverrides);\n    if (next.albumLogoSources)\n        saveAlbumLogoSources(next.albumLogoSources);\n    if (Array.isArray(next.highlightIds))', 'shared cache write')
replace_once('        coverOverrides: (state === null || state === void 0 ? void 0 : state.coverOverrides) || loadCoverOverrides(),\n        highlightIds:', '        coverOverrides: (state === null || state === void 0 ? void 0 : state.coverOverrides) || loadCoverOverrides(),\n        albumLogoSources: (state === null || state === void 0 ? void 0 : state.albumLogoSources) || readAlbumLogoSources(),\n        highlightIds:', 'shared state normalize')

replace_once('    const [coverOverrides, setCoverOverrides] = useState(loadCoverOverrides());\n', '    const [coverOverrides, setCoverOverrides] = useState(loadCoverOverrides());\n    const [albumLogoSources, setAlbumLogoSources] = useState(readAlbumLogoSources());\n', 'app logo source state')

cover_effect = '''    useEffect(() => {\n        saveCoverOverrides(coverOverrides);\n        if (sharedReady) saveSharedAdminState({ coverOverrides }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar la portada. El cambio quedó solo en este dispositivo.'); });\n    }, [coverOverrides, sharedReady]);\n'''
logo_effect = cover_effect + '''    useEffect(() => {\n        saveAlbumLogoSources(albumLogoSources);\n        if (sharedReady) saveSharedAdminState({ albumLogoSources }).catch(e => { console.warn(e); setAdminMessage('No se pudo sincronizar la fuente de escudos. El cambio quedó solo en este dispositivo.'); });\n    }, [albumLogoSources, sharedReady]);\n'''
replace_once(cover_effect, logo_effect, 'logo source persistence effect')

replace_count('            if (state.coverOverrides)\n                setCoverOverrides(state.coverOverrides);\n            if (Array.isArray(state.highlightIds))', '            if (state.coverOverrides)\n                setCoverOverrides(state.coverOverrides);\n            if (state.albumLogoSources)\n                setAlbumLogoSources(state.albumLogoSources);\n            if (Array.isArray(state.highlightIds))', 2, 'load shared logo sources')

old_display = '    const displayAlbums = useMemo(() => albums.map(a => ({ ...a, cover: coverOverrides[a.id] || a.cover })).sort((a, b) => (b.dateTs || 0) - (a.dateTs || 0) || a.name.localeCompare(b.name)), [albums, coverOverrides]);'
new_display = '    const displayAlbums = useMemo(() => albums.map(a => applyAlbumLogoSource({ ...a, cover: coverOverrides[a.id] || a.cover }, albumLogoSources)).sort((a, b) => (b.dateTs || 0) - (a.dateTs || 0) || a.name.localeCompare(b.name)), [albums, coverOverrides, albumLogoSources]);'
replace_once(old_display, new_display, 'apply selected team logos')

replace_once('    const toggleHighlight = (albumId) => setHighlightIds(ids => ids.includes(albumId) ? ids.filter(id => id !== albumId) : [albumId, ...ids].slice(0, 12));\n', '''    const toggleHighlight = (albumId) => setHighlightIds(ids => ids.includes(albumId) ? ids.filter(id => id !== albumId) : [albumId, ...ids].slice(0, 12));\n    const chooseAlbumLogoSource = (albumId, source) => {\n        if (!albumId || !['app', 'sheet'].includes(source)) return;\n        setAlbumLogoSources(prev => ({ ...prev, [albumId]: source }));\n        setAdminMessage(source === 'app' ? 'Escudos del álbum: APP.' : 'Escudos del álbum: hoja de cálculo.');\n    };\n''', 'admin logo source setter')

admin_map_old = '''            React.createElement("div", { className: "grid md:grid-cols-2 xl:grid-cols-3 gap-5" }, displayAlbums.filter(album => { const q = norm(albumSearch); return !q || norm(album.name).includes(q) || norm(album.dateLabel).includes(q); }).map(album => {\n                var _a, _b;\n                return React.createElement("div", { key: album.id,'''
admin_map_new = '''            React.createElement("div", { className: "grid md:grid-cols-2 xl:grid-cols-3 gap-5" }, displayAlbums.filter(album => { const q = norm(albumSearch); return !q || norm(album.name).includes(q) || norm(album.dateLabel).includes(q); }).map(album => {\n                var _a, _b;\n                const currentLogoSource = album.logoSource || getAlbumLogoSource(album, albumLogoSources);\n                return React.createElement("div", { key: album.id,'''
replace_once(admin_map_old, admin_map_new, 'admin album logo source current value')

button_anchor = '''                        React.createElement("div", { className: "grid gap-2" },\n                            React.createElement("button", { onClick: () => openPhotoCoverPicker(album), className: "bg-neutral-800 hover:bg-neutral-700 text-sm rounded-xl px-4 py-3 text-left" },'''
selector = '''                        React.createElement("div", { className: "grid gap-2" },\n                            React.createElement("div", { className: "bg-black/35 border border-sky-500/20 rounded-2xl p-3" },\n                                React.createElement("div", { className: "flex items-center justify-between gap-3 mb-2" },\n                                    React.createElement("div", null,\n                                        React.createElement("p", { className: "text-xs font-black text-sky-100" }, "Escudos del álbum"),\n                                        React.createElement("p", { className: "text-[10px] text-neutral-500 mt-0.5" }, "APP busca el escudo por nombre del equipo; Hoja usa A2/A3.")),\n                                    React.createElement("span", { className: `text-[9px] uppercase tracking-widest font-black px-2 py-1 rounded-full ${currentLogoSource === 'app' ? 'bg-sky-500/15 text-sky-200 border border-sky-400/25' : 'bg-amber-500/15 text-amber-200 border border-amber-400/25'}` }, currentLogoSource === 'app' ? 'APP' : 'Hoja')),\n                                React.createElement("div", { className: "grid grid-cols-2 gap-2" },\n                                    React.createElement("button", { type: "button", onClick: () => chooseAlbumLogoSource(album.id, 'app'), className: `${currentLogoSource === 'app' ? 'bg-sky-500 text-black border-sky-300' : 'bg-neutral-900 text-white border-neutral-700 hover:bg-neutral-800'} border rounded-xl px-3 py-2.5 text-xs font-black` },\n                                        React.createElement("i", { className: "fas fa-shield-halved mr-1.5" }),\n                                        "Escudo APP"),\n                                    React.createElement("button", { type: "button", onClick: () => chooseAlbumLogoSource(album.id, 'sheet'), className: `${currentLogoSource === 'sheet' ? 'bg-amber-400 text-black border-amber-200' : 'bg-neutral-900 text-white border-neutral-700 hover:bg-neutral-800'} border rounded-xl px-3 py-2.5 text-xs font-black` },\n                                        React.createElement("i", { className: "fas fa-table-cells mr-1.5" }),\n                                        "Escudo hoja")),\n                                isTalleresSanLorenzoAlbum(album) && React.createElement("p", { className: "text-[10px] text-amber-200/80 mt-2 leading-relaxed" }, "Talleres vs San Lorenzo (AFA): por defecto conserva los escudos de la hoja de cálculo.")),\n                            React.createElement("button", { onClick: () => openPhotoCoverPicker(album), className: "bg-neutral-800 hover:bg-neutral-700 text-sm rounded-xl px-4 py-3 text-left" },'''
replace_once(button_anchor, selector, 'admin per-album logo source selector')

# Bump only the application version string; image asset versions stay independent.
s = s.replace('v105-gallery-recovery-brand', 'v106-team-logo-source')

# Feature invariants.
for url in logos.values():
    if url not in s:
        raise RuntimeError('Missing supplied logo URL: ' + url)
for token in ['TEAM_APP_LOGOS', 'albumLogoSources', 'chooseAlbumLogoSource', 'isTalleresSanLorenzoAlbum', "return isTalleresSanLorenzoAlbum(album) ? 'sheet' : 'app';"]:
    if token not in s:
        raise RuntimeError('Missing feature token: ' + token)

INDEX.write_text(s, encoding='utf-8')
print(f'Applied {len(logos)} APP shields and per-album APP/Sheet selector.')
