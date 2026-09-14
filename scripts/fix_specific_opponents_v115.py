from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v115-specific-opponents'
s = s.replace('v114-mobile-categories-smart-logos', VERSION)

# 1) App crest registry: Unión Florida already exists as an asset but was not registered.
if '"union_florida": "assets/lcf-v2/union-florida.png?v=115"' not in s:
    anchor = '    "juvenil_barrio_comercial": "assets/lcf-v2/juvenil-barrio-comercial.png?v=108",\n'
    if anchor not in s:
        raise SystemExit('TEAM_APP_LOGOS anchor not found')
    s = s.replace(anchor, anchor + '    "union_florida": "assets/lcf-v2/union-florida.png?v=115",\n', 1)

# 2) Explicit aliases for the exact naming used by these albums.
alias_anchor = '    "juvenil_comercial": "juvenil_barrio_comercial",\n'
if '"club_union_florida": "union_florida"' not in s:
    if alias_anchor not in s:
        raise SystemExit('TEAM_APP_LOGO_ALIASES anchor not found')
    s = s.replace(
        alias_anchor,
        alias_anchor
        + '    "juvenil_barrio_comercial": "juvenil_barrio_comercial",\n'
        + '    "union_florida": "union_florida",\n'
        + '    "club_union_florida": "union_florida",\n',
        1
    )

# 3) Helpers for the three specifically identified opponents.
helper = r'''
function isParqueVelezTeamName(name) {
    const n = norm(name);
    return n === 'parque' || n.includes('parque_velez') || n.includes('velez_sarsfield') || n.includes('velez_sarfield');
}
function exactOpponentForAlbum(album) {
    const id = String((album && album.id) || '').trim();
    if (id === 'all_boys_union_florida_1784948400000') {
        return { name:'Unión Florida', appLogo:TEAM_APP_LOGOS.union_florida || 'assets/lcf-v2/union-florida.png?v=115', color:'#1d4ed8' };
    }
    if (id === 'all_boys_comercial_1784430000000') {
        return { name:'Juvenil Barrio Comercial', appLogo:TEAM_APP_LOGOS.juvenil_barrio_comercial || 'assets/lcf-v2/juvenil-barrio-comercial.png?v=108', color:'#2563eb' };
    }
    if (id === 'all_boys_parque_velez_1784948400000') {
        return { name:'Escuela Parque Vélez Sarsfield', appLogo:'', color:'#16a34a', initials:'EPV' };
    }
    return null;
}
function specialFallbackForTeam(name) {
    if (isParqueVelezTeamName(name)) return { label:'EPV', color:'#16a34a' };
    return { label:teamInitials(name || 'Equipo'), color:'' };
}
'''
if 'function exactOpponentForAlbum(' not in s:
    marker = "function isTalleresSanLorenzoAlbum(album) {"
    if marker not in s:
        raise SystemExit('helper insertion marker not found')
    s = s.replace(marker, helper + '\n' + marker, 1)

# 4) Force the known app crests for the two known clubs, and initials/green for Parque Vélez.
old_apply = '''    const teamEntries = (Array.isArray(album.teamEntries) ? album.teamEntries : []).map(team => {
        const sheetLogo = String((team && team.sheetLogo) || (team && team.logo) || '').trim();
        const appLogo = String((team && team.appLogo) || findAppTeamLogo((team && team.fullName) || (team && team.name) || '') || '').trim();
        const logo = logoSource === 'sheet' ? (sheetLogo || appLogo) : (appLogo || sheetLogo);
        return { ...(team || {}), sheetLogo, appLogo, logo, logoSource };
    });'''
new_apply = '''    const exactOpponent = exactOpponentForAlbum(album);
    const teamEntries = (Array.isArray(album.teamEntries) ? album.teamEntries : []).map((team, teamIndex) => {
        const base = { ...(team || {}) };
        const isOpponentSlot = teamIndex === 1;
        if (exactOpponent && isOpponentSlot) {
            base.name = exactOpponent.name;
            base.fullName = exactOpponent.name;
            base.color = exactOpponent.color || base.color || '';
            if (!exactOpponent.appLogo) {
                base.logo = '';
                base.sheetLogo = '';
                base.appLogo = '';
            }
        }
        const displayName = String(base.fullName || base.name || '').trim();
        const sheetLogo = String(base.sheetLogo || base.logo || '').trim();
        const detectedAppLogo = String(base.appLogo || findAppTeamLogo(displayName) || '').trim();
        const forcedAppLogo = exactOpponent && isOpponentSlot ? String(exactOpponent.appLogo || '').trim() : '';
        const appLogo = forcedAppLogo || detectedAppLogo;
        const forceApp = Boolean(forcedAppLogo) || ['union_florida','juvenil_barrio_comercial'].includes(canonicalAppTeamKey(displayName));
        const logo = (exactOpponent && isOpponentSlot && !exactOpponent.appLogo)
            ? ''
            : (forceApp ? (appLogo || sheetLogo) : (logoSource === 'sheet' ? (sheetLogo || appLogo) : (appLogo || sheetLogo)));
        return { ...base, sheetLogo, appLogo, logo, logoSource };
    });'''
if old_apply not in s:
    raise SystemExit('applyAlbumLogoSource block not found')
s = s.replace(old_apply, new_apply, 1)

# 5) Exact names/logos in the match picker, independent of spreadsheet text quality.
old_return = '''    return { home, away };
}

function matchPickerChrono(album) {'''
new_return = '''    const exactOpponent = exactOpponentForAlbum(album);
    if (exactOpponent) {
        away = {
            ...away,
            name: exactOpponent.name,
            fullName: exactOpponent.name,
            logo: exactOpponent.appLogo || '',
            appLogo: exactOpponent.appLogo || '',
            color: exactOpponent.color || away.color || '',
            initials: exactOpponent.initials || ''
        };
    }
    return { home, away };
}

function matchPickerChrono(album) {'''
if old_return not in s:
    raise SystemExit('matchPickerSides return marker not found')
s = s.replace(old_return, new_return, 1)

# 6) Match picker fallback: show initials when no crest exists; Parque Vélez gets a green badge.
old_crest = '''    const crest = (side, right = false) => React.createElement("div", { className: `match-picker-crest-box ${right ? 'right' : ''}`.trim() },
        React.createElement("span", { className: "match-picker-crest-fallback" }, matchPickerInitials(side && side.name)),
        side && (side.logo || side.appLogo) ? React.createElement("img", { src: side.logo || side.appLogo, alt: `Escudo ${side.name || ''}`, className: "match-picker-crest", loading: "lazy", decoding: "async", onError: e => { const fallback = String((side && side.appLogo) || findAppTeamLogo(side && side.name) || ''); if (fallback && e.currentTarget.src !== new URL(fallback, location.href).href) { e.currentTarget.src = fallback; return; } e.currentTarget.style.display = 'none'; } }) : null);'''
new_crest = '''    const crest = (side, right = false) => {
        const logo = String((side && (side.logo || side.appLogo)) || '').trim();
        const isParque = isParqueVelezTeamName(side && side.name);
        const classes = `match-picker-crest-box ${right ? 'right' : ''} ${logo ? '' : 'no-logo'} ${isParque ? 'green-fallback' : ''}`.trim();
        return React.createElement("div", { className: classes },
            React.createElement("span", { className: "match-picker-crest-fallback" }, (side && side.initials) || (isParque ? 'EPV' : matchPickerInitials(side && side.name))),
            logo ? React.createElement("img", { src: logo, alt: `Escudo ${side.name || ''}`, className: "match-picker-crest", loading: "lazy", decoding: "async", onError: e => { const fallback = String((side && side.appLogo) || findAppTeamLogo(side && side.name) || ''); if (fallback && e.currentTarget.src !== new URL(fallback, location.href).href) { e.currentTarget.src = fallback; return; } e.currentTarget.style.display = 'none'; const box = e.currentTarget.parentElement; if (box) box.classList.add('no-logo'); } }) : null);
    };'''
if old_crest not in s:
    raise SystemExit('match picker crest block not found')
s = s.replace(old_crest, new_crest, 1)

# 7) Album hero/mobile rendering: prefer app fallback and show EPV as a green badge.
s = s.replace(
    "    const teamLogo = String((team && team.logo) || '').trim();\n    return React.createElement(\"div\", { className: `team-sight ${side}` },",
    "    const teamLogo = String((team && (team.logo || team.appLogo)) || findAppTeamLogo(teamName) || '').trim();\n    const specialFallback = specialFallbackForTeam(teamName);\n    return React.createElement(\"div\", { className: `team-sight ${side}` },",
    1
)
s = s.replace(
    '            React.createElement("div", { className: "team-sight-text", style: { display: teamLogo ? \'none\' : \'block\' } }, teamName || (side === \'left\' ? \'Equipo local\' : \'Equipo visitante\'))));',
    '            React.createElement("div", { className: `team-sight-text${specialFallback.color ? \' special-green-fallback\' : \'\'}`, style: { display: teamLogo ? \'none\' : \'flex\', "--fallback-color": specialFallback.color || \'\' } }, specialFallback.color ? specialFallback.label : (teamName || (side === \'left\' ? \'Equipo local\' : \'Equipo visitante\')))));',
    1
)

s = s.replace(
    "    const teamLogo = String((team && team.logo) || '').trim();\n    return React.createElement(\"div\", { className: \"duel-mobile-mark\" },",
    "    const teamLogo = String((team && (team.logo || team.appLogo)) || findAppTeamLogo(teamName) || '').trim();\n    const specialFallback = specialFallbackForTeam(teamName);\n    return React.createElement(\"div\", { className: `duel-mobile-mark${specialFallback.color ? ' special-green-fallback' : ''}`, style: { \"--fallback-color\": specialFallback.color || '' } },",
    1
)
s = s.replace(
    '        React.createElement("div", { className: "duel-mobile-fallback", style: { display: teamLogo ? \'none\' : \'block\' } }, teamName || fallbackName || \'Equipo\'));',
    '        React.createElement("div", { className: "duel-mobile-fallback", style: { display: teamLogo ? \'none\' : \'flex\' } }, specialFallback.color ? specialFallback.label : (teamName || fallbackName || \'Equipo\')));',
    1
)

s = s.replace(
    "    const teamLogo = String((team && team.logo) || '').trim();\n    return React.createElement(\"div\", { className: `duel-cover-mark ${side}` },",
    "    const teamLogo = String((team && (team.logo || team.appLogo)) || findAppTeamLogo(teamName) || '').trim();\n    const specialFallback = specialFallbackForTeam(teamName);\n    return React.createElement(\"div\", { className: `duel-cover-mark ${side}${specialFallback.color ? ' special-green-fallback' : ''}`, style: { \"--fallback-color\": specialFallback.color || '' } },",
    1
)
s = s.replace(
    '        React.createElement("div", { className: `duel-cover-fallback${teamLogo ? \'\' : \' show\'}` }, teamInitials(teamName || fallbackName || \'Equipo\')));',
    '        React.createElement("div", { className: `duel-cover-fallback${teamLogo ? \'\' : \' show\'}` }, specialFallback.color ? specialFallback.label : teamInitials(teamName || fallbackName || \'Equipo\')));',
    1
)

# Also prefer an internal app crest in the versus scene if the spreadsheet logo is absent/broken.
s = s.replace(
    "    const leftLogo = String((teamA && teamA.logo) || '').trim();\n    const rightLogo = String((teamB && teamB.logo) || '').trim();",
    "    const leftLogo = String((teamA && (teamA.logo || teamA.appLogo)) || findAppTeamLogo((teamA && teamA.name) || '') || '').trim();\n    const rightLogo = String((teamB && (teamB.logo || teamB.appLogo)) || findAppTeamLogo((teamB && teamB.name) || '') || '').trim();",
    1
)

# 8) CSS for initials-only fallback, especially Parque Vélez in green.
style = r'''
<style id="v115-specific-opponents-style">
  .match-picker-crest-box.no-logo .match-picker-crest-fallback{
    display:flex!important;align-items:center;justify-content:center!important;
    width:68px;height:68px;border-radius:999px!important;
    background:rgba(15,23,42,.92)!important;border:1px solid rgba(148,163,184,.28)!important;
    color:#e2e8f0!important;font-size:25px!important;line-height:1!important;
    box-shadow:0 10px 22px rgba(0,0,0,.26)!important;
  }
  .match-picker-crest-box.green-fallback .match-picker-crest-fallback{
    background:linear-gradient(145deg,#15803d,#16a34a 58%,#22c55e)!important;
    border-color:rgba(187,247,208,.48)!important;color:#fff!important;
    box-shadow:0 12px 28px rgba(22,163,74,.28)!important;
  }
  .team-sight-text.special-green-fallback{
    width:58px!important;height:58px!important;max-width:none!important;border-radius:999px!important;
    align-items:center!important;justify-content:center!important;
    background:linear-gradient(145deg,#15803d,#16a34a 58%,#22c55e)!important;
    border:1px solid rgba(187,247,208,.48)!important;color:#fff!important;
    font-family:'Bebas Neue',Impact,sans-serif!important;font-size:22px!important;letter-spacing:.05em!important;
    box-shadow:0 10px 26px rgba(22,163,74,.24)!important;
  }
  .duel-mobile-mark.special-green-fallback .duel-mobile-fallback{
    width:54px!important;height:54px!important;border-radius:999px!important;
    align-items:center!important;justify-content:center!important;
    background:linear-gradient(145deg,#15803d,#16a34a 58%,#22c55e)!important;
    border:1px solid rgba(187,247,208,.48)!important;color:#fff!important;
    font-family:'Bebas Neue',Impact,sans-serif!important;font-size:21px!important;letter-spacing:.05em!important;
    box-shadow:0 10px 24px rgba(22,163,74,.24)!important;
  }
  .duel-cover-mark.special-green-fallback .duel-cover-fallback.show{
    width:58px!important;height:58px!important;border-radius:999px!important;margin:auto!important;
    display:flex!important;align-items:center!important;justify-content:center!important;
    background:linear-gradient(145deg,#15803d,#16a34a 58%,#22c55e)!important;
    border:1px solid rgba(187,247,208,.42)!important;color:#fff!important;opacity:.96!important;
    font-family:'Bebas Neue',Impact,sans-serif!important;font-size:22px!important;letter-spacing:.05em!important;
    text-shadow:none!important;box-shadow:0 10px 24px rgba(22,163,74,.22)!important;
  }
  @media(max-width:640px){
    .match-picker-crest-box.no-logo .match-picker-crest-fallback{width:52px;height:52px;font-size:20px!important}
    .team-sight-text.special-green-fallback{width:48px!important;height:48px!important;font-size:18px!important}
    .duel-mobile-mark.special-green-fallback .duel-mobile-fallback{width:50px!important;height:50px!important;font-size:19px!important}
  }
</style>
'''
if 'id="v115-specific-opponents-style"' not in s:
    s = s.replace('</head>', style + '</head>', 1)

p.write_text(s, encoding='utf-8')
print('v115 specific opponent patch applied')
