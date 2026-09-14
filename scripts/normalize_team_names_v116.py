from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version
s = re.sub(r'<meta name="app-version" content="[^"]*"\s*/?>', '<meta name="app-version" content="v116-team-identity-cleanup" />', s, count=1)

VELEZ_LOGO = 'https://sp-ao.shortpixel.ai/client/to_webp,q_glossy,ret_img,w_500,h_500/https://acbb.ar/wp-content/uploads/2023/11/velez.png'

# Exact colors, names and crest for the three identified matches.
s = s.replace("return { name:'Unión Florida', appLogo:TEAM_APP_LOGOS.union_florida || 'assets/lcf-v2/union-florida.png?v=115', color:'#1d4ed8' };",
              "return { name:'Unión Florida', appLogo:TEAM_APP_LOGOS.union_florida || 'assets/lcf-v2/union-florida.png?v=115', color:'#facc15' };")
s = s.replace("return { name:'Juvenil Barrio Comercial', appLogo:TEAM_APP_LOGOS.juvenil_barrio_comercial || 'assets/lcf-v2/juvenil-barrio-comercial.png?v=108', color:'#2563eb' };",
              "return { name:'Juvenil Comercial', appLogo:TEAM_APP_LOGOS.juvenil_barrio_comercial || 'assets/lcf-v2/juvenil-barrio-comercial.png?v=108', color:'#dc2626' };")
s = s.replace("return { name:'Escuela Parque Vélez Sarsfield', appLogo:'', color:'#16a34a', initials:'EPV' };",
              f"return {{ name:'Escuela Parque Vélez Sarsfield', appLogo:'{VELEZ_LOGO}', color:'#16a34a', initials:'EPV' }};")

# Register Parque Vélez's crest in the app registry so all views can resolve it.
registry_anchor = '    "union_florida": "assets/lcf-v2/union-florida.png?v=115",\n'
velez_registry = f'    "escuela_parque_velez_sarsfield": "{VELEZ_LOGO}",\n'
if velez_registry not in s:
    if registry_anchor not in s:
        raise SystemExit('union_florida registry anchor not found')
    s = s.replace(registry_anchor, registry_anchor + velez_registry, 1)

# Aliases for the spelling/forms actually used by the albums/sheets.
alias_anchor = '    "club_union_florida": "union_florida",\n'
alias_lines = (
    '    "parque": "escuela_parque_velez_sarsfield",\n'
    '    "parque_velez": "escuela_parque_velez_sarsfield",\n'
    '    "escuela_parque_velez": "escuela_parque_velez_sarsfield",\n'
    '    "velez_sarsfield": "escuela_parque_velez_sarsfield",\n'
    '    "velez_sarfield": "escuela_parque_velez_sarsfield",\n'
)
if '"parque_velez": "escuela_parque_velez_sarsfield"' not in s:
    if alias_anchor not in s:
        raise SystemExit('team alias anchor not found')
    s = s.replace(alias_anchor, alias_anchor + alias_lines, 1)

# Clean display names globally when spreadsheet metadata accidentally contains a URL/image link.
helper = r'''
const TEAM_DISPLAY_NAME_OVERRIDES = Object.freeze({
    all_boys: 'All Boys',
    union_florida: 'Unión Florida',
    juvenil_barrio_comercial: 'Juvenil Comercial',
    escuela_parque_velez_sarsfield: 'Escuela Parque Vélez Sarsfield'
});
function looksLikeTeamLink(value) {
    const raw = String(value || '').trim();
    if (!raw) return false;
    return /^(?:https?:\/\/|www\.)/i.test(raw)
        || /(?:drive\.google\.com|docs\.google\.com|githubusercontent\.com|github\.io|shortpixel\.ai)/i.test(raw)
        || /\.(?:png|jpe?g|webp|gif|svg)(?:[?#]|$)/i.test(raw);
}
function humanizeTeamKey(key) {
    const canonical = canonicalAppTeamKey(key) || norm(key);
    if (TEAM_DISPLAY_NAME_OVERRIDES[canonical]) return TEAM_DISPLAY_NAME_OVERRIDES[canonical];
    return String(canonical || '')
        .split('_').filter(Boolean)
        .map(word => word.length <= 2 ? word.toUpperCase() : word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
        .replace(/\bFc\b/g, 'FC');
}
function knownTeamsFromAlbumIdentity(album) {
    const identity = norm([
        album && album.id,
        album && album.sourceName,
        album && album.name
    ].filter(Boolean).join(' '));
    if (!identity) return [];
    const candidates = [];
    const aliases = (typeof TEAM_APP_LOGO_ALIASES === 'object' && TEAM_APP_LOGO_ALIASES) || {};
    Object.keys(TEAM_APP_LOGOS || {}).forEach(key => {
        const probes = [key, ...Object.keys(aliases).filter(alias => aliases[alias] === key)];
        let pos = Infinity;
        probes.forEach(probe => {
            const at = identity.indexOf(norm(probe));
            if (at >= 0 && at < pos) pos = at;
        });
        if (Number.isFinite(pos)) candidates.push({ key, pos });
    });
    candidates.sort((a, b) => a.pos - b.pos || b.key.length - a.key.length);
    const seen = new Set();
    return candidates.filter(item => {
        if (seen.has(item.key)) return false;
        seen.add(item.key);
        return true;
    });
}
function inferTeamNameFromAlbum(album, index) {
    const exact = exactOpponentForAlbum(album);
    if (exact) return index === 0 ? 'All Boys' : exact.name;
    const known = knownTeamsFromAlbumIdentity(album);
    if (known[index]) return humanizeTeamKey(known[index].key);
    let id = norm((album && album.id) || (album && album.sourceName) || '');
    id = id.replace(/_\d{10,16}(?:_.*)?$/, '');
    id = id.replace(/_(?:primera|reserva|cebollitas|escuelita|galeria|femenino)$/, '');
    if (id.startsWith('all_boys_')) {
        if (index === 0) return 'All Boys';
        const opponent = id.slice('all_boys_'.length);
        if (opponent) return humanizeTeamKey(opponent);
    }
    const vsParts = id.split(/_(?:vs|versus)_/).filter(Boolean);
    if (vsParts[index]) return humanizeTeamKey(vsParts[index]);
    return '';
}
function cleanTeamDisplayName(value, album, index) {
    const raw = String(value || '').trim();
    if (raw && !looksLikeTeamLink(raw)) {
        const canonical = canonicalAppTeamKey(raw);
        if (TEAM_DISPLAY_NAME_OVERRIDES[canonical]) return TEAM_DISPLAY_NAME_OVERRIDES[canonical];
        return raw;
    }
    return inferTeamNameFromAlbum(album, index) || (index === 0 ? 'Equipo local' : 'Equipo visitante');
}
'''
if 'function cleanTeamDisplayName(' not in s:
    marker = 'function albumTeamSide(album, index, useFullName = false) {'
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit('albumTeamSide marker not found')
    s = s[:pos] + helper + '\n' + s[pos:]

# Use cleaned names everywhere albumTeamSide feeds the UI.
old_display = "    const displayName = (useFullName && entry.fullName) || entry.name || names[index] || fallbackName || (index === 0 ? albumName : '') || '';"
new_display = "    const rawDisplayName = (useFullName && entry.fullName) || entry.name || names[index] || fallbackName || (index === 0 ? albumName : '') || '';\n    const displayName = cleanTeamDisplayName(rawDisplayName, album, index);"
if old_display in s:
    s = s.replace(old_display, new_display, 1)
elif 'const displayName = cleanTeamDisplayName(rawDisplayName, album, index);' not in s:
    raise SystemExit('albumTeamSide displayName line not found')

# Also sanitize stored team entries before logos/colors are resolved, so direct consumers never show URLs as names.
old_base = "        const base = { ...(team || {}) };\n        const isOpponentSlot = teamIndex === 1;"
new_base = "        const base = { ...(team || {}) };\n        const cleanedStoredName = cleanTeamDisplayName(base.fullName || base.name || '', album, teamIndex);\n        if (cleanedStoredName) { base.name = cleanedStoredName; base.fullName = cleanedStoredName; }\n        const isOpponentSlot = teamIndex === 1;"
if old_base in s:
    s = s.replace(old_base, new_base, 1)
elif 'const cleanedStoredName = cleanTeamDisplayName' not in s:
    raise SystemExit('applyAlbumLogoSource base marker not found')

# Ensure the old special no-logo branch no longer blanks Parque Vélez now that a crest exists.
s = s.replace("            if (!exactOpponent.appLogo) {\n                base.logo = '';\n                base.sheetLogo = '';\n                base.appLogo = '';\n            }", "            if (exactOpponent.appLogo) { base.appLogo = exactOpponent.appLogo; base.logo = exactOpponent.appLogo; }")

p.write_text(s, encoding='utf-8')
