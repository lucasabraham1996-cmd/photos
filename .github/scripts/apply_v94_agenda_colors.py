from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')
repls={
".booking.status-pendiente{border-color:rgba(245,158,11,.34);background:linear-gradient(135deg,rgba(73,49,8,.42),rgba(17,13,6,.93));box-shadow:inset 4px 0 0 rgba(245,158,11,.62)}":".booking.status-pendiente{border-color:rgba(59,130,246,.38);background:linear-gradient(135deg,rgba(15,49,91,.44),rgba(6,16,32,.95));box-shadow:inset 4px 0 0 rgba(59,130,246,.72)}",
".booking.status-confirmado{border-color:rgba(34,197,94,.34);background:linear-gradient(135deg,rgba(10,61,30,.40),rgba(5,20,11,.94));box-shadow:inset 4px 0 0 rgba(34,197,94,.68)}":".booking.status-confirmado{border-color:rgba(245,158,11,.34);background:linear-gradient(135deg,rgba(73,49,8,.42),rgba(17,13,6,.93));box-shadow:inset 4px 0 0 rgba(245,158,11,.62)}",
".booking.status-realizado{border-color:rgba(59,130,246,.38);background:linear-gradient(135deg,rgba(15,49,91,.44),rgba(6,16,32,.95));box-shadow:inset 4px 0 0 rgba(59,130,246,.72)}":".booking.status-realizado{border-color:rgba(34,197,94,.34);background:linear-gradient(135deg,rgba(10,61,30,.40),rgba(5,20,11,.94));box-shadow:inset 4px 0 0 rgba(34,197,94,.68)}",
".status.pendiente{background:rgba(245,158,11,.13);color:#fde68a}":".status.pendiente{background:rgba(59,130,246,.14);color:#bfdbfe}",
".status.confirmado{background:rgba(34,197,94,.12);color:#bbf7d0}":".status.confirmado{background:rgba(245,158,11,.13);color:#fde68a}",
".status.realizado{background:rgba(59,130,246,.14);color:#bfdbfe}":".status.realizado{background:rgba(34,197,94,.12);color:#bbf7d0}"
}
for old,new in repls.items():
    if old not in s: raise SystemExit('marker not found: '+old[:40])
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('v94 agenda colors patched')
