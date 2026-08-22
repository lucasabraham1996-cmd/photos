from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

# Status-aware full booking cards.
old_css='.booking{border:1px solid var(--line);background:linear-gradient(135deg,#0b0e15,#07090d);border-radius:22px;padding:16px;display:grid;grid-template-columns:95px 1fr auto;gap:14px;align-items:center}'
new_css='''.booking{border:1px solid var(--line);background:linear-gradient(135deg,#0b0e15,#07090d);border-radius:22px;padding:16px;display:grid;grid-template-columns:95px 1fr auto;gap:14px;align-items:center;transition:border-color .2s ease,background .2s ease,box-shadow .2s ease}
    .booking.status-pendiente{border-color:rgba(245,158,11,.34);background:linear-gradient(135deg,rgba(73,49,8,.42),rgba(17,13,6,.93));box-shadow:inset 4px 0 0 rgba(245,158,11,.62)}
    .booking.status-confirmado{border-color:rgba(34,197,94,.34);background:linear-gradient(135deg,rgba(10,61,30,.40),rgba(5,20,11,.94));box-shadow:inset 4px 0 0 rgba(34,197,94,.68)}
    .booking.status-realizado{border-color:rgba(59,130,246,.38);background:linear-gradient(135deg,rgba(15,49,91,.44),rgba(6,16,32,.95));box-shadow:inset 4px 0 0 rgba(59,130,246,.72)}
    .booking.status-cancelado{border-color:rgba(239,68,68,.34);background:linear-gradient(135deg,rgba(81,20,20,.40),rgba(27,7,7,.94));box-shadow:inset 4px 0 0 rgba(239,68,68,.68)}'''
once(old_css,new_css,'booking status css')

# Helper for 10-day automatic retention and newest-first ordering.
old='''async function listBookings(){const s=await db.collection(BOOKINGS_PATH).limit(500).get();return s.docs.map(d=>({id:d.id,...d.data()})).sort((a,b)=>String(a.date||'9999').localeCompare(String(b.date||'9999'))||String(a.arrivalTime||'').localeCompare(String(b.arrivalTime||'')))}'''
new='''function bookingDateMs(b){if(!b||!b.date)return NaN;const t=b.matchTime||b.arrivalTime||'12:00';const ms=Date.parse(`${b.date}T${t}:00`);return Number.isFinite(ms)?ms:NaN}
async function purgeExpiredBookings(items){const cutoff=Date.now()-10*24*60*60*1000;const expired=(items||[]).filter(b=>{const ms=bookingDateMs(b);return Number.isFinite(ms)&&ms<cutoff});if(!expired.length)return items||[];await Promise.allSettled(expired.map(b=>bookingDoc(b.id).delete()));const gone=new Set(expired.map(b=>b.id));return (items||[]).filter(b=>!gone.has(b.id))}
async function listBookings(){const snap=await db.collection(BOOKINGS_PATH).limit(500).get();let items=snap.docs.map(d=>({id:d.id,...d.data()}));items=await purgeExpiredBookings(items);return items.sort((a,b)=>{const am=bookingDateMs(a),bm=bookingDateMs(b);if(Number.isFinite(am)&&Number.isFinite(bm)&&bm!==am)return bm-am;if(Number.isFinite(bm)&&!Number.isFinite(am))return 1;if(Number.isFinite(am)&&!Number.isFinite(bm))return -1;return String(b.updatedAt||b.createdAt||'').localeCompare(String(a.updatedAt||a.createdAt||''))})}'''
once(old,new,'list newest and purge')

# Add status class to full card.
old_card='''return `<article class="booking" data-id="${esc(b.id)}" data-status="${esc(b.status||'pendiente')}">'''
new_card='''const safeStatus=['pendiente','confirmado','realizado','cancelado'].includes(b.status)?b.status:'pendiente';return `<article class="booking status-${esc(safeStatus)}" data-id="${esc(b.id)}" data-status="${esc(safeStatus)}">'''
once(old_card,new_card,'booking class')

# Keep select consistent with normalized status in status class area only; no functional behavior change required.

p.write_text(s,encoding='utf-8')
print('v90 agenda patched')
