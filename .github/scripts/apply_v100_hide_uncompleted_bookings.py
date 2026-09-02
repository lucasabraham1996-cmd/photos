from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

old="""async function createDraft(data){const id=uid();const clean={id,type:'booking',status:'pendiente',createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),payment:Number(data.payment||0),adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}
"""
new="""async function createDraft(data){const id=uid();const clean={id,type:'booking',status:'pendiente',formCompleted:false,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),payment:Number(data.payment||0),adminNote:data.adminNote||'',date:'',home:'',away:'',category:'',venue:'',address:'',matchTime:'',arrivalTime:'',clientName:'',phone:'',notes:''};await bookingDoc(id).set(clean);return clean}
"""
if old not in s: raise SystemExit('createDraft marker not found')
s=s.replace(old,new,1)

old="""async function listBookings(){const snap=await db.collection(BOOKINGS_PATH).limit(500).get();let items=snap.docs.map(d=>({id:d.id,...d.data()}));items=await purgeExpiredBookings(items);return items.sort((a,b)=>{const am=bookingDateMs(a),bm=bookingDateMs(b);if(Number.isFinite(am)&&Number.isFinite(bm)&&bm!==am)return bm-am;if(Number.isFinite(bm)&&!Number.isFinite(am))return 1;if(Number.isFinite(am)&&!Number.isFinite(bm))return -1;return String(b.updatedAt||b.createdAt||'').localeCompare(String(a.updatedAt||a.createdAt||''))})}
"""
new="""function isAgendaBooking(b){if(!b)return false;if(b.formCompleted===true||b.confirmedAt)return true;return ['confirmado','realizado','cancelado'].includes(String(b.status||'').toLowerCase())&&Boolean(b.date&&b.home&&b.away)}
async function listBookings(){const snap=await db.collection(BOOKINGS_PATH).limit(500).get();let items=snap.docs.map(d=>({id:d.id,...d.data()}));items=await purgeExpiredBookings(items);items=items.filter(isAgendaBooking);return items.sort((a,b)=>{const am=bookingDateMs(a),bm=bookingDateMs(b);if(Number.isFinite(am)&&Number.isFinite(bm)&&bm!==am)return bm-am;if(Number.isFinite(bm)&&!Number.isFinite(am))return 1;if(Number.isFinite(am)&&!Number.isFinite(bm))return -1;return String(b.updatedAt||b.createdAt||'').localeCompare(String(a.updatedAt||a.createdAt||''))})}
"""
if old not in s: raise SystemExit('listBookings marker not found')
s=s.replace(old,new,1)

old="""try{await saveBooking(currentDraft.id,{...data,status:'confirmado',confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado'})}"""
new="""try{await saveBooking(currentDraft.id,{...data,status:'confirmado',formCompleted:true,confirmedAt:new Date().toISOString()});renderSuccess({...currentDraft,...data,status:'confirmado',formCompleted:true})}"""
if old not in s: raise SystemExit('submit marker not found')
s=s.replace(old,new,1)

if 'v100-hide-uncompleted-bookings' not in s:
    s=s.replace('<!-- v98-local-lcf-crests -->','<!-- v98-local-lcf-crests -->\n<!-- v100-hide-uncompleted-bookings -->',1)

p.write_text(s,encoding='utf-8')
print('v100 hide uncompleted bookings patched')
