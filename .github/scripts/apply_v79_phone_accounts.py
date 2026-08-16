from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="const phone=normalizeClubPhone(clubLookupDni); if(!phone||phone.length<10){ setClubMessage('Ingresá un celular válido.'); return; }"
new="const phone=normalizeClubPhone(clubSessionPhone || clubLookupDni); if(!phone||phone.length<10){ setClubMessage('Ingresá un celular válido.'); return; }"
if old not in s: raise SystemExit('lookup phone marker not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('session lookup fixed')