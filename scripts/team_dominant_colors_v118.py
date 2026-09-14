from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v118-team-dominant-colors'
s = re.sub(r'<meta name="app-version" content="[^"]+"\s*/?>', f'<meta name="app-version" content="{VERSION}" />', s, count=1)

helper = r'''
const TEAM_DOMINANT_COLORS = Object.freeze({
    cibi: '#facc15',
    lasallano: '#2563eb',
    union_florida: '#facc15',
    juvenil_barrio_comercial: '#dc2626',
    escuela_parque_velez_sarsfield: '#16a34a'
});
function dominantTeamColor(name, logo = '') {
    const directKey = canonicalAppTeamKey(name);
    if (directKey && TEAM_DOMINANT_COLORS[directKey]) return TEAM_DOMINANT_COLORS[directKey];

    const rawLogo = String(logo || '').toLowerCase();
    if (rawLogo) {
        for (const [key, src] of Object.entries(TEAM_APP_LOGOS || {})) {
            if (!src) continue;
            const normalizedSrc = String(src).toLowerCase().split('?')[0];
            if (rawLogo.split('?')[0].endsWith(normalizedSrc) || rawLogo.includes('/' + normalizedSrc.split('/').pop())) {
                if (TEAM_DOMINANT_COLORS[key]) return TEAM_DOMINANT_COLORS[key];
            }
        }
    }
    return '';
}
'''

if 'const TEAM_DOMINANT_COLORS = Object.freeze({' not in s:
    anchor = "function findAppTeamLogo(name) {\n    const key = canonicalAppTeamKey(name);\n    return key ? TEAM_APP_LOGOS[key] || '' : '';\n}\n"
    if anchor not in s:
        raise SystemExit('findAppTeamLogo anchor not found')
    s = s.replace(anchor, anchor + '\n' + helper, 1)

old = """        const appLogo = forcedAppLogo || detectedAppLogo;\n        const forceApp = Boolean(forcedAppLogo) || ['union_florida','juvenil_barrio_comercial'].includes(canonicalAppTeamKey(displayName));\n        const logo = (exactOpponent && isOpponentSlot && !exactOpponent.appLogo)\n            ? ''\n            : (forceApp ? (appLogo || sheetLogo) : (logoSource === 'sheet' ? (sheetLogo || appLogo) : (appLogo || sheetLogo)));\n        return { ...base, sheetLogo, appLogo, logo, logoSource };"""
new = """        const appLogo = forcedAppLogo || detectedAppLogo;\n        const dominantColor = dominantTeamColor(displayName, appLogo);\n        if (dominantColor) base.color = dominantColor;\n        const forceApp = Boolean(forcedAppLogo) || ['union_florida','juvenil_barrio_comercial'].includes(canonicalAppTeamKey(displayName));\n        const logo = (exactOpponent && isOpponentSlot && !exactOpponent.appLogo)\n            ? ''\n            : (forceApp ? (appLogo || sheetLogo) : (logoSource === 'sheet' ? (sheetLogo || appLogo) : (appLogo || sheetLogo)));\n        return { ...base, sheetLogo, appLogo, logo, logoSource };"""
if old in s:
    s = s.replace(old, new, 1)
elif 'const dominantColor = dominantTeamColor(displayName, appLogo);' not in s:
    raise SystemExit('applyAlbumLogoSource color block not found')

old_return = """    return {\n        ...album,\n        logoSource,\n        teamEntries,\n        teamLogo: (teamEntries[0] && teamEntries[0].logo) || album.teamLogo || ''\n    };"""
new_return = """    return {\n        ...album,\n        logoSource,\n        teamEntries,\n        teamColors: teamEntries.map((team, index) => validHexColor(team && team.color) || ((Array.isArray(album.teamColors) && album.teamColors[index]) || '')),\n        teamLogo: (teamEntries[0] && teamEntries[0].logo) || album.teamLogo || ''\n    };"""
if old_return in s:
    s = s.replace(old_return, new_return, 1)
elif 'teamColors: teamEntries.map((team, index)' not in s:
    raise SystemExit('applyAlbumLogoSource return block not found')

# Make the two requested aliases explicit so spreadsheet variations still resolve to the same dominant color.
alias_anchor = '    "deportivo_lasallano": "lasallano",\n'
extra_aliases = '    "club_lasallano": "lasallano",\n    "deportivo_cibi": "cibi",\n    "club_cibi": "cibi",\n'
if '"club_lasallano": "lasallano"' not in s:
    if alias_anchor not in s:
        raise SystemExit('Lasallano alias anchor not found')
    s = s.replace(alias_anchor, alias_anchor + extra_aliases, 1)

p.write_text(s, encoding='utf-8')
