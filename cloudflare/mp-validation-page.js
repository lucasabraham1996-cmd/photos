export default String.raw`<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Validación privada · lucasabraham.ph</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#07101e;color:#e7eef8;font:16px/1.55 system-ui,sans-serif}
main{max-width:720px;margin:36px auto;padding:24px}h1{font-size:30px;line-height:1.2}p{color:#b6c4d8}
.card{background:#111f33;border:1px solid #28435f;border-radius:20px;padding:24px;margin:20px 0}
label{display:block;font-weight:700;margin-bottom:8px}input{width:100%;padding:13px;background:#06111f;color:white;border:1px solid #40617f;border-radius:10px}
button,.action{display:block;width:100%;border:0;border-radius:12px;background:#157bc5;padding:14px;margin-top:16px;color:white;font-weight:750;font-size:16px;text-align:center;text-decoration:none;cursor:pointer}
button:disabled{opacity:.45;cursor:default}.secondary{background:#273d56}.success{color:#87e3b1}small{color:#9eafc5}
ol{padding-left:23px}li{margin:14px 0}#message{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#8fcaf2}[hidden]{display:none!important}
</style></head><body><main>
<small>lucasabraham.ph · Acceso de administración</small>
<h1>Una compra real para verificar la descarga</h1>
<p>Esta página permite una foto digital por <strong id="amount">$200</strong>. Los cobros al público permanecen cerrados.</p>
<section class="card"><form id="form">
<label for="key">Clave de administración</label><input id="key" type="password" autocomplete="off" required>
<button id="create" disabled>Preparar compra privada</button>
<button id="recover" type="button" class="secondary" disabled>Recuperar compra ya pagada</button>
</form><p id="photo"></p><a id="pay" class="action" hidden target="_blank" rel="noopener noreferrer">Abrir Mercado Pago</a>
<button id="status" class="secondary" hidden>Revisar estado</button>
<button id="download" hidden>Descargar fotografía</button><p id="message" role="status" aria-live="polite">Comprobando disponibilidad…</p></section>
<section class="card"><ol>
<li id="blocked">Confirmar que la descarga se bloquea antes de pagar.</li>
<li id="paid">Completar el pago desde una cuenta compradora real diferente de la cuenta vendedora.</li>
<li id="file">Recibir la fotografía después de acreditar el pago.</li>
<li id="webhook">Confirmar la notificación automática de Mercado Pago.</li>
</ol><small>Si la descarga falla, podés reintentar sin pagar otra vez. El importe de esta validación se muestra antes de abrir Mercado Pago.</small></section>
</main><script>
'use strict';
const $=id=>document.getElementById(id), money=n=>new Intl.NumberFormat('es-AR',{style:'currency',currency:'ARS',maximumFractionDigits:0}).format(n);
let purchase=null, busy=false, autoDownloaded='', config=null, attempts=0;
try{purchase=JSON.parse(localStorage.getItem('LA_MP_VALIDATION_PURCHASE')||'null')}catch(_){}
async function call(path,data,key){
 const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',...(key?{'X-Setup-Key':key}:{})},body:JSON.stringify(data)});
 const result=await response.json();if(!response.ok||!result.ok)throw Error(result.error||'No se pudo completar la operación');return result;
}
function message(text){$('message').textContent=text}
function saved(){
 localStorage.setItem('LA_MP_VALIDATION_PURCHASE',JSON.stringify(purchase));
 $('photo').textContent=purchase.name||'';
 $('status').hidden=false;
 $('pay').href=purchase.checkout_url;
 $('pay').textContent='Pagar '+money(purchase.amount)+' en Mercado Pago';
 $('pay').hidden=!purchase.before_blocked||purchase.paid;
 if(purchase.before_blocked){$('blocked').textContent='Verificado: la descarga fue bloqueada antes de pagar.';$('blocked').className='success'}
}
async function getFile(){
 const response=await fetch('/api/live-download/'+purchase.checkout_id+'/0',{headers:{'X-Receipt-Token':purchase.receipt_token}});
 if(!response.ok){const data=await response.json().catch(()=>({}));throw Error(data.error||'No se pudo descargar la fotografía')}
 const blob=await response.blob(),href=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=href;link.download=purchase.name||'foto.jpg';document.body.appendChild(link);link.click();link.remove();
 setTimeout(()=>URL.revokeObjectURL(href),60000);
 purchase.downloaded=true;saved();$('file').textContent='Verificado: fotografía recibida. Revisá tus descargas.';$('file').className='success';
}
async function check(){
 if(!purchase||busy)return;busy=true;
 try{
  const state=await call('/api/live-status',{checkout_id:purchase.checkout_id,receipt_token:purchase.receipt_token});
  purchase.webhook_received=Boolean(state.verification&&state.verification.webhook_received);
  if(purchase.webhook_received){$('webhook').textContent='Verificado: notificación de pago recibida y autenticada.';$('webhook').className='success'}
  purchase.paid=state.paid;saved();$('download').hidden=!state.paid;
  if(!state.paid){
   if(!purchase.before_blocked&&state.status==='created'){
    const denied=await fetch('/api/live-download/'+purchase.checkout_id+'/0',{headers:{'X-Receipt-Token':purchase.receipt_token}});
    purchase.before_blocked=denied.status===403;saved();
   }
   message('Pago todavía no acreditado. La descarga sigue bloqueada.');return;
  }
  $('paid').textContent='Verificado: Mercado Pago acreditó '+money(state.amount)+'.';$('paid').className='success';
  message('Pago acreditado. Tu fotografía está lista.');
  if(!purchase.downloaded&&autoDownloaded!==purchase.checkout_id){autoDownloaded=purchase.checkout_id;try{await getFile()}catch(e){autoDownloaded='';message(e.message)}}
 }catch(e){$('download').hidden=true;message(e.message)}
 finally{busy=false}
}
$('form').addEventListener('submit',async event=>{
 event.preventDefault();if(busy||!config||!config.available||config.mode!=='validation')return;
 busy=true;$('create').disabled=true;
 const key=$('key').value;$('key').value='';
 try{
  if(purchase){message('Ya hay una compra preparada. Revisá su estado antes de iniciar otra.');return}
  let pending=null;try{pending=JSON.parse(localStorage.getItem('LA_MP_VALIDATION_REQUEST')||'null')}catch(_){}
  if(!pending){
   const sample=await call('/api/live-sample',{},key);
   pending={...sample,request_id:crypto.randomUUID(),receipt_token:Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,'0')).join('')};
   localStorage.setItem('LA_MP_VALIDATION_REQUEST',JSON.stringify(pending));
  }
  const created=await call('/api/live-checkout',{selection:pending.selection,expected_total:pending.expected_total,
   request_id:pending.request_id,receipt_token:pending.receipt_token,return_to:'validation'},key);
  purchase={...created,name:pending.name,amount:created.quote.amount,before_blocked:false,paid:false};saved();
  localStorage.removeItem('LA_MP_VALIDATION_REQUEST');
  const denied=await fetch('/api/live-download/'+purchase.checkout_id+'/0',{headers:{'X-Receipt-Token':purchase.receipt_token}});
  if(denied.status!==403)throw Error('No se confirmó el bloqueo antes del pago. No pagues esta orden todavía.');
  const state=await call('/api/live-status',{checkout_id:purchase.checkout_id,receipt_token:purchase.receipt_token});
  if(state.status!=='created'||state.paid)throw Error('No se pudo verificar el estado inicial de esta orden.');
  purchase.before_blocked=true;saved();message('Descarga bloqueada correctamente. Podés pagar '+money(purchase.amount)+'.');
 }catch(e){message(e.message)}
 finally{busy=false;$('create').disabled=Boolean(purchase)}
});
$('recover').addEventListener('click',async()=>{
 if(busy||!config||!config.available||config.mode!=='validation')return;
 const key=$('key').value;
 if(!key){message('Ingresá la clave de administración para recuperar la compra acreditada.');$('key').focus();return}
 busy=true;$('recover').disabled=true;$('key').value='';let recovered=false;
 try{
  const result=await call('/api/live-recover',{},key);
  purchase={...result,name:result.name,amount:result.quote.amount,paid:true,downloaded:false,
   before_blocked:Boolean(result.verification&&result.verification.before_payment_blocked),
   webhook_received:Boolean(result.verification&&result.verification.webhook_received)};
  saved();localStorage.removeItem('LA_MP_VALIDATION_REQUEST');$('create').disabled=true;
  message('Compra acreditada recuperada. Comprobando la descarga…');recovered=true;
 }catch(e){message(e.message)}
 finally{busy=false;$('recover').disabled=false}
 if(recovered)await check();
});
$('status').addEventListener('click',check);
$('download').addEventListener('click',()=>getFile().catch(e=>message(e.message)));
const initialization=fetch('/api/payment-config').then(r=>r.json()).then(async data=>{
 config=data;$('amount').textContent=money(data.validation_amount||200);
 $('create').disabled=!data.available||data.mode!=='validation'||Boolean(purchase);
 $('recover').disabled=!data.available||data.mode!=='validation';
 message(data.available&&data.mode==='validation'?'Ingresá la clave de administración para preparar una foto.':'La validación privada todavía no está habilitada.');
 if(purchase){saved();await check()}
}).catch(()=>message('No se pudo comprobar la configuración. Los cobros permanecen cerrados.'));
const timer=setInterval(()=>{if(!document.hidden&&attempts++<90&&purchase&&(!purchase.paid||!purchase.downloaded||!purchase.webhook_received))check()},10000);
window.addEventListener('focus',check);
</script></body></html>`;
