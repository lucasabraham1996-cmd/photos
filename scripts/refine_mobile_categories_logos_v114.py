from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v114-mobile-categories-smart-logos'
s = s.replace('v113-match-picker-filters', VERSION)

smart_canonical = r'''function teamLogoTokens(value) {
    const stop = new Set([
        'club','atletico','atletica','atleticos','ca','c','fc','sc','de','del','la','las','los','el','y',
        'cordoba','cordobes','cordobesa','futbol','football','sociedad','deportivo','deportiva',
        'primera','reserva','cebollitas','inferiores','femenino','masculino','categoria','cat'
    ]);
    return norm(value).split('_').filter(t => t && t.length > 1 && !stop.has(t));
}
function canonicalAppTeamKey(name) {
    const n = norm(name);
    if (!n) return '';
    if (TEAM_APP_LOGOS[n]) return n;
    if (TEAM_APP_LOGO_ALIASES[n] && TEAM_APP_LOGOS[TEAM_APP_LOGO_ALIASES[n]]) return TEAM_APP_LOGO_ALIASES[n];

    const directCandidates = [...Object.keys(TEAM_APP_LOGO_ALIASES), ...Object.keys(TEAM_APP_LOGOS)]
        .filter(Boolean)
        .sort((a, b) => b.length - a.length);
    for (const candidate of directCandidates) {
        if (candidate.length < 4) continue;
        const bounded = n === candidate || n.startsWith(candidate + '_') || n.endsWith('_' + candidate) || n.includes('_' + candidate + '_');
        if (!bounded) continue;
        const key = TEAM_APP_LOGO_ALIASES[candidate] || candidate;
        if (TEAM_APP_LOGOS[key]) return key;
    }

    const inputTokens = teamLogoTokens(n);
    if (!inputTokens.length) return '';
    const inputSet = new Set(inputTokens);
    const seenKeys = new Set();
    const scored = [];

    for (const aliasOrKey of directCandidates) {
        const key = TEAM_APP_LOGO_ALIASES[aliasOrKey] || aliasOrKey;
        if (!TEAM_APP_LOGOS[key]) continue;
        const fingerprint = key + '|' + aliasOrKey;
        if (seenKeys.has(fingerprint)) continue;
        seenKeys.add(fingerprint);

        const candidateTokens = teamLogoTokens(aliasOrKey);
        if (!candidateTokens.length) continue;
        const common = candidateTokens.filter(t => inputSet.has(t));
        const commonCount = common.length;
        const candidateSet = new Set(candidateTokens);
        const inputInsideCandidate = inputTokens.filter(t => candidateSet.has(t)).length;
        let score = 0;

        if (commonCount === candidateTokens.length && commonCount >= 2) score = 110 + commonCount * 10;
        else if (inputInsideCandidate === inputTokens.length && inputTokens.length >= 2) score = 100 + inputTokens.length * 8;
        else if (commonCount >= 2) score = 72 + commonCount * 9 - Math.abs(candidateTokens.length - inputTokens.length) * 2;
        else if (commonCount === 1 && candidateTokens.length === 1 && inputTokens.length <= 3 && common[0].length >= 5) score = 48;

        const flatInput = inputTokens.join('_');
        const flatCandidate = candidateTokens.join('_');
        if (flatInput && flatCandidate && (flatInput.includes(flatCandidate) || flatCandidate.includes(flatInput))) score += 18;
        if (score > 0) scored.push({ key, score });
    }

    scored.sort((a, b) => b.score - a.score);
    const best = scored[0];
    const second = scored[1];
    if (!best) return '';
    if (best.score >= 70) return best.key;
    if (best.score >= 48 && (!second || best.score - second.score >= 15)) return best.key;
    return '';
}
function findAppTeamLogo(name) {
    const key = canonicalAppTeamKey(name);
    return key ? TEAM_APP_LOGOS[key] || '' : '';
}'''

pattern = r'function canonicalAppTeamKey\(name\) \{.*?\n\}\nfunction findAppTeamLogo\(name\) \{.*?\n\}'
s, count = re.subn(pattern, lambda _m: smart_canonical, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit('No se pudo reemplazar canonicalAppTeamKey/findAppTeamLogo')

smart_side = r'''function albumTeamSide(album, index, useFullName = false) {
    const entries = Array.isArray(album === null || album === void 0 ? void 0 : album.teamEntries) ? album.teamEntries : [];
    const names = Array.isArray(album === null || album === void 0 ? void 0 : album.teamNames) ? album.teamNames : [];
    const colors = Array.isArray(album === null || album === void 0 ? void 0 : album.teamColors) ? album.teamColors : [];
    const entry = entries[index] || {};
    const albumName = String((album && album.name) || '').trim();
    const sourceName = String((album && album.sourceName) || '').trim();
    const parsedAlbumNames = parseTeamsFromAlbumName(albumName || sourceName);
    const parsedSourceNames = parseTeamsFromAlbumName(sourceName || albumName);
    const fallbackName = parsedAlbumNames[index] || parsedSourceNames[index] || '';
    const displayName = (useFullName && entry.fullName) || entry.name || names[index] || fallbackName || (index === 0 ? albumName : '') || '';

    const logoCandidates = [
        entry.fullName,
        entry.name,
        names[index],
        fallbackName,
        parsedSourceNames[index],
        displayName
    ].filter(Boolean);
    const appLogo = logoCandidates.map(findAppTeamLogo).find(Boolean) || '';
    const sheetLogo = String(entry.logo || (index === 0 ? (album && album.teamLogo) || '' : '') || '').trim();

    return {
        name: displayName,
        logo: sheetLogo || appLogo,
        appLogo,
        color: entry.color || colors[index] || colors[0] || ''
    };
}'''

s, count = re.subn(r'function albumTeamSide\(album, index, useFullName = false\) \{.*?\n\}', lambda _m: smart_side, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit('No se pudo reemplazar albumTeamSide')

old_crest = "side && side.logo ? React.createElement(\"img\", { src: side.logo, alt: `Escudo ${side.name || ''}`, className: \"match-picker-crest\", loading: \"lazy\", decoding: \"async\", onError: e => { e.currentTarget.style.display = 'none'; } }) : null"
new_crest = "side && (side.logo || side.appLogo) ? React.createElement(\"img\", { src: side.logo || side.appLogo, alt: `Escudo ${side.name || ''}`, className: \"match-picker-crest\", loading: \"lazy\", decoding: \"async\", onError: e => { const fallback = String((side && side.appLogo) || findAppTeamLogo(side && side.name) || ''); if (fallback && e.currentTarget.src !== new URL(fallback, location.href).href) { e.currentTarget.src = fallback; return; } e.currentTarget.style.display = 'none'; } }) : null"
if old_crest in s:
    s = s.replace(old_crest, new_crest, 1)
elif new_crest not in s:
    raise SystemExit('No se pudo actualizar fallback del escudo en MatchPickerModal')

style = r'''
<style id="v114-mobile-category-tabs-smart-logo">
@media(max-width:640px),(hover:none),(pointer:coarse){
  .subalbum-panel{
    padding:10px 10px 9px!important;
    border-radius:20px!important;
    background:linear-gradient(145deg,rgba(3,7,18,.92),rgba(7,16,34,.94))!important;
    border:1px solid rgba(96,165,250,.18)!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 12px 28px rgba(0,0,0,.18)!important;
    overflow:hidden!important;
  }
  .subalbum-panel>p{
    margin:0 4px 9px!important;
    color:#7dd3fc!important;
    font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important;
    font-size:8px!important;
    line-height:1!important;
    font-weight:900!important;
    letter-spacing:.14em!important;
    text-transform:uppercase!important;
    opacity:.9!important;
  }
  .subalbum-showcase{
    display:flex!important;
    align-items:center!important;
    gap:7px!important;
    margin:0!important;
    padding:0 1px 2px!important;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    scroll-snap-type:x proximity!important;
    scrollbar-width:none!important;
    -webkit-overflow-scrolling:touch!important;
  }
  .subalbum-showcase::-webkit-scrollbar{display:none!important}
  .subalbum-visual-card{
    position:relative!important;
    flex:0 0 clamp(96px,30vw,116px)!important;
    min-width:96px!important;
    max-width:116px!important;
    height:43px!important;
    min-height:43px!important;
    margin:0!important;
    padding:0 12px!important;
    clip-path:none!important;
    border-radius:14px!important;
    border:1px solid rgba(148,163,184,.15)!important;
    background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.025))!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.04)!important;
    color:#cbd5e1!important;
    scroll-snap-align:start!important;
    transform:none!important;
    transition:background .18s ease,border-color .18s ease,box-shadow .18s ease,transform .18s ease!important;
    overflow:hidden!important;
  }
  .subalbum-visual-card:hover,.subalbum-visual-card:active{
    transform:translateY(-1px)!important;
    background:rgba(59,130,246,.10)!important;
    border-color:rgba(96,165,250,.26)!important;
  }
  .subalbum-visual-card.active{
    background:linear-gradient(135deg,rgba(14,165,233,.26),rgba(37,99,235,.30) 62%,rgba(30,64,175,.22))!important;
    border-color:rgba(125,211,252,.58)!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.13),0 8px 20px rgba(37,99,235,.16),0 0 0 1px rgba(56,189,248,.05)!important;
  }
  .subalbum-visual-card::before{display:none!important}
  .subalbum-visual-card::after{
    content:""!important;
    display:block!important;
    position:absolute!important;
    left:16px!important;
    right:16px!important;
    bottom:5px!important;
    top:auto!important;
    width:auto!important;
    height:2px!important;
    border-radius:999px!important;
    background:#7dd3fc!important;
    box-shadow:0 0 10px rgba(125,211,252,.48)!important;
    opacity:0!important;
    transform:scaleX(.25)!important;
    transition:opacity .18s ease,transform .18s ease!important;
  }
  .subalbum-visual-card.active::after{opacity:1!important;transform:scaleX(1)!important}
  .subalbum-copy-wrap{
    width:100%!important;
    min-width:0!important;
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    padding:0!important;
    margin:0!important;
  }
  .subalbum-copy-title{
    width:100%!important;
    margin:0!important;
    padding:0 0 2px!important;
    color:#cbd5e1!important;
    font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important;
    font-size:10.5px!important;
    line-height:1!important;
    font-weight:850!important;
    letter-spacing:.025em!important;
    text-transform:uppercase!important;
    text-align:center!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    text-overflow:ellipsis!important;
    text-shadow:none!important;
  }
  .subalbum-visual-card.active .subalbum-copy-title{color:#fff!important}
  .subalbum-thumb-wrap,.subalbum-floating-badge,.subalbum-thumb-overlay,.subalbum-copy-meta{display:none!important}
}
</style>
'''

s = re.sub(r'<style id="v114-mobile-category-tabs-smart-logo">.*?</style>\s*', '', s, flags=re.S)
s = s.replace('</head>', style + '\n</head>', 1)

p.write_text(s, encoding='utf-8')
print('v114 mobile category tabs + smart team logo fallback applied')
