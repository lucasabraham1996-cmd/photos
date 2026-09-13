from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Bump version so installed/mobile copies refresh the UI.
s = s.replace('v111-match-picker', 'v112-match-picker-broadcast')

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

# Helpers also repair already-cached albums whose label was generated as "01 ene 46256".
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
'''
if 'function matchPickerChrono(' not in s:
    s = s.replace('function MatchPickerModal({ albums, onClose, onSelect }) {', helpers + '\nfunction MatchPickerModal({ albums, onClose, onSelect }) {', 1)

# Selector: newest real match first, oldest last.
s = s.replace(
    '    const all = Array.isArray(albums) ? albums : [];',
    "    const all = Array.isArray(albums) ? [...albums].sort((a, b) => matchPickerChrono(b) - matchPickerChrono(a) || String(a.name || '').localeCompare(String(b.name || ''), 'es', { numeric:true, sensitivity:'base' })) : [];",
    1
)

# Show the corrected date inside each card as well.
s = s.replace(
    'album.dateLabel ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-calendar" }), album.dateLabel) : null,',
    'matchPickerDateLabel(album) ? React.createElement("span", { className: "match-picker-chip" }, React.createElement("i", { className: "far fa-calendar" }), matchPickerDateLabel(album)) : null,',
    1
)

# Broadcast-style override: names are the hero; crests bleed off the edges with no boxes.
style = r'''
<style id="v112-match-picker-broadcast-style">
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
  .match-picker-crest-box.right{
    justify-self:end!important;
    transform:translateX(24px)!important;
  }
  .match-picker-crest-fallback{display:none!important}
  .match-picker-crest{
    width:98px!important;
    height:98px!important;
    max-width:none!important;
    object-fit:contain!important;
    filter:drop-shadow(0 10px 18px rgba(0,0,0,.42))!important;
  }
  .match-picker-meta{position:relative;z-index:5!important;margin-top:9px!important}

  @media(max-width:640px){
    .match-picker-card{
      min-height:102px!important;
      grid-template-columns:66px minmax(0,1fr) 66px!important;
      gap:2px!important;
      padding:10px 3px!important;
    }
    .match-picker-names{
      font-size:clamp(16px,5.1vw,22px)!important;
      line-height:.94!important;
      letter-spacing:.018em!important;
    }
    .match-picker-crest-box{
      width:88px!important;
      height:92px!important;
      transform:translateX(-26px)!important;
    }
    .match-picker-crest-box.right{transform:translateX(26px)!important}
    .match-picker-crest{width:80px!important;height:80px!important}
    .match-picker-meta{gap:3px!important;margin-top:7px!important}
    .match-picker-chip{font-size:6.6px!important;padding:3px 5px!important;min-height:19px!important}
  }
</style>
'''
s = re.sub(r'<style id="v112-match-picker-broadcast-style">.*?</style>\s*', '', s, count=1, flags=re.S)
s = s.replace('</head>', style + '</head>', 1)

p.write_text(s, encoding='utf-8')
print('v112 match picker broadcast patch applied')
