/* lucasabraham.ph | Recordatorios de cobro (solo panel administrador)
   Almacenamiento LOCAL al dispositivo. WhatsApp no se envía automáticamente.
   Las notificaciones del sistema solo pueden mostrarse con la app abierta. */
(function(){
"use strict";
var KEY="LA_ADMIN_COBROS_REMINDERS_V1";
var eventName="la-admin-reminders-updated";
var money=new Intl.NumberFormat("es-AR",{style:"currency",currency:"ARS",maximumFractionDigits:0});
var h=function(tag,props){return React.createElement.apply(React,[tag,props].concat(Array.prototype.slice.call(arguments,2)));};
function cleanItems(raw){
  if(!Array.isArray(raw))return [];
  return raw.filter(function(x){return x&&typeof x==="object"&&x.id;}).slice(0,500).map(function(x){
    return {id:String(x.id).slice(0,100),name:String(x.name||"").slice(0,120),
      phone:String(x.phone||"").slice(0,35),amount:Number(x.amount)||0,
      concept:String(x.concept||"").slice(0,180),dueAt:String(x.dueAt||"").slice(0,30),
      status:x.status==="paid"?"paid":"pending",
      createdAt:String(x.createdAt||""),paidAt:String(x.paidAt||""),
      waOpenedAt:String(x.waOpenedAt||""),notifiedForAt:String(x.notifiedForAt||"")};
  });
}
function load(){
  try{return cleanItems(JSON.parse(localStorage.getItem(KEY)||"[]"));}catch(_){return [];}
}
function save(items){
  var clean=cleanItems(items);
  try{localStorage.setItem(KEY,JSON.stringify(clean));}catch(e){return false;}
  try{window.dispatchEvent(new Event(eventName));}catch(_){}
  return true;
}
function dateNumber(r){var n=Date.parse(r&&r.dueAt||"");return Number.isFinite(n)?n:Infinity;}
function dueItems(items){var now=Date.now();return (items||load()).filter(function(x){return x.status!=="paid"&&dateNumber(x)<=now;});}
function pendingCount(){return load().filter(function(x){return x.status!=="paid";}).length;}
function getDueCount(){return dueItems(load()).length;}
function whenString(d){try{return new Intl.DateTimeFormat("es-AR",{dateStyle:"medium",timeStyle:"short"}).format(new Date(d));}catch(_){return d||"Sin fecha";}}
function numberForWhatsapp(input){
  var d=String(input||"").replace(/\D/g,"");
  if(d.indexOf("00")===0)d=d.slice(2);
  if(d.indexOf("0")===0)d=d.replace(/^0+/,"");
  if(d.indexOf("54")!==0&&d.length===10)d="549"+d;
  if(d.indexOf("54")===0&&d.indexOf("549")!==0&&d.length===12)d="549"+d.slice(2);
  return d.length>=11&&d.length<=15?d:"";
}
function reminderMessage(item){
  var name=String(item.name||"").trim()||"";
  var total=money.format(Number(item.amount)||0);
  return "¡Hola! 😊 "+name+" ¿Cómo estás?\n\n"+
    "Te escribimos un recordatorio automático: quedó pendiente el pago de *"+total+"* correspondiente a las fotos adquiridas la última vez.\n\n"+
    "Mi alias es lucasabraham.mp, luego me podés enviar comprobante por este medio.\n\n"+
    "Si ya pagaste, por favor desestimá este mensaje. 🙏\n\n"+
    "¡Muchas gracias por elegir lucasabraham.ph! 📸⚽\n\n"+
    "🤖 *Recordatorio automático de pago*";
}
function whatsappLink(item){var phone=numberForWhatsapp(item.phone);return phone?"https://wa.me/"+phone+"?text="+encodeURIComponent(reminderMessage(item)):"";}
function exportCalendar(r){
  var start=new Date(r.dueAt);
  if(!Number.isFinite(start.getTime()))return;
  var utc=function(d){return d.toISOString().replace(/[-:]/g,"").replace(/\.\d{3}Z$/,"Z");};
  var esc=function(x){return String(x||"").replace(/\\/g,"\\\\").replace(/\n/g,"\\n").replace(/[,;]/g,function(c){return "\\"+c;});};
  var end=new Date(start.getTime()+15*60*1000);
  var lines=[
    "BEGIN:VCALENDAR","VERSION:2.0","CALSCALE:GREGORIAN","PRODID:-//lucasabraham.ph//Recordatorios de cobro//ES",
    "BEGIN:VEVENT","UID:"+r.id.replace(/[^a-z0-9-]/gi,"")+"@lucasabraham.ph",
    "DTSTAMP:"+utc(new Date()),"DTSTART:"+utc(start),"DTEND:"+utc(end),
    "SUMMARY:"+esc("Cobrar "+money.format(r.amount)+" a "+r.name),
    "DESCRIPTION:"+esc("Cobro pendiente de "+money.format(r.amount)+(r.concept?" por "+r.concept:"")+". Abrí lucasabraham.ph para preparar el mensaje de WhatsApp."),
    "BEGIN:VALARM","ACTION:DISPLAY","TRIGGER:-PT0M",
    "DESCRIPTION:"+esc("Recordatorio: "+r.name+" debe abonar "+money.format(r.amount)),
    "END:VALARM","END:VEVENT","END:VCALENDAR"
  ];
  try{
    var blob=new Blob([lines.join("\r\n")+"\r\n"],{type:"text/calendar;charset=utf-8"});
    var uri=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=uri;a.download="recordatorio-cobro-"+r.id+".ics";
    document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(uri);},5000);
  }catch(e){window.alert("No se pudo generar el aviso de calendario en este navegador.");}
}
function localDateTime(d){var pad=function(x){return String(x).padStart(2,"0");};return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate())+"T"+pad(d.getHours())+":"+pad(d.getMinutes());}
function defaultDue(){return localDateTime(new Date(Date.now()+24*60*60*1000));}
function notifyDue(){
  if(!("Notification" in window)||Notification.permission!=="granted")return;
  var items=load(),now=dueItems(items).filter(function(x){return x.notifiedForAt!==x.dueAt;});
  if(!now.length)return;
  var first=now[0],body=now.length===1?
    first.name+" te debe abonar "+money.format(first.amount)+". Entrá al panel para abrir WhatsApp.":
    "Tenés "+now.length+" recordatorios de cobro vencidos. Abrí el panel de administrador.";
  try{
    var n=new Notification("lucasabraham.ph · Cobro pendiente",{body:body,tag:"la-cobros-"+(now.length===1?first.id:"resumen"),icon:"./site-icon-dark-la.png"});
    n.onclick=function(){window.focus();location.hash="#/admin";};
    var ids=new Set(now.map(function(x){return x.id;}));
    save(items.map(function(x){return ids.has(x.id)?Object.assign({},x,{notifiedForAt:x.dueAt}):x;}));
  }catch(e){/* Algunos navegadores móviles no permiten Notification() sin push. */}
}
var css=
".la-reminders-shell{background:linear-gradient(135deg,#111827,#0b1220 60%,#05080e);border:1px solid rgba(56,189,248,.23);border-radius:24px;padding:clamp(16px,2.6vw,26px);color:#f9fafb;margin-bottom:22px;}"+
".la-reminders-title{font-size:23px;font-weight:900;margin:0;}"+
".la-reminders-sub{color:#a8b3c6;font-size:13px;line-height:1.6;margin:8px 0 15px;}"+
".la-reminders-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px;}"+
".la-reminders-field{display:block;color:#c8d9ea;font-size:12px;font-weight:700;}"+
".la-reminders-field input,.la-reminders-field textarea{display:block;width:100%;min-width:0;box-sizing:border-box;background:#090f1e;border:1px solid #334155;color:#fff;border-radius:12px;padding:12px;margin-top:6px;font-size:14px;outline:none;}"+
".la-reminders-field input:focus,.la-reminders-field textarea:focus{border-color:#38bdf8;}"+
".la-reminders-wide{grid-column:1/-1;}"+
".la-reminders-actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-top:16px;}"+
".la-reminders-btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:10px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.16);font-size:12px;font-weight:850;cursor:pointer;text-decoration:none;}"+
".la-reminders-primary{background:#38bdf8;color:#06111d;border-color:#38bdf8;}"+
".la-reminders-wa{background:#159e57;color:white;border-color:#159e57;}"+
".la-reminders-muted{background:#1e293b;color:#e2e8f0;}"+
".la-reminders-paid{background:#064e3b;color:#bdf7d9;border-color:#047857;}"+
".la-reminders-summary{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0;}"+
".la-reminders-chip{background:#0a1525;border:1px solid #25344b;border-radius:14px;padding:11px 14px;font-size:12px;color:#afbed1;}"+
".la-reminders-chip strong{font-size:20px;display:block;color:#fff;}"+
".la-reminders-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,310px),1fr));gap:13px;margin-top:16px;}"+
".la-reminders-card{border:1px solid #334155;border-radius:18px;background:#0b1424;padding:15px;min-width:0;}"+
".la-reminders-card.due{border-color:#fb923c;background:linear-gradient(145deg,#28180e,#0d1522 75%);}"+
".la-reminders-card.paid{opacity:.75;}"+
".la-reminders-card-head{display:flex;gap:8px;justify-content:space-between;align-items:start;}"+
".la-reminders-card-name{font-size:16px;font-weight:850;overflow-wrap:anywhere;}"+
".la-reminders-card-amount{font-size:23px;font-weight:950;color:#86efac;margin:8px 0;}"+
".la-reminders-card-meta{font-size:12px;color:#cbd5e1;line-height:1.7;overflow-wrap:anywhere;}"+
".la-reminders-pill{border-radius:999px;background:#1d4ed8;color:white;padding:4px 9px;font-size:10px;font-weight:900;white-space:nowrap;}"+
".la-reminders-card.due .la-reminders-pill{background:#ea580c;}"+
".la-reminders-card.paid .la-reminders-pill{background:#047857;}"+
".la-reminders-privacy{margin-top:14px;border-left:3px solid #fbbf24;padding:7px 10px;font-size:12px;line-height:1.6;background:#42200630;color:#fde68a;}"+
".la-reminders-feedback{font-size:12px;color:#7dd3fc;margin-top:9px;}"+
"@media(max-width:600px){.la-reminders-grid{grid-template-columns:1fr;}.la-reminders-shell{padding:16px;}.la-reminders-card{padding:12px;}}";
try{var st=document.createElement("style");st.id="la-admin-reminders-styles";st.textContent=css;document.head.appendChild(st);}catch(_){}
function PaymentReminders(){
  var useState=React.useState,useEffect=React.useEffect;
  var state=useState(load),items=state[0],setItems=state[1];
  var formState=useState({name:"",phone:"",amount:"",concept:"",dueAt:defaultDue()}),form=formState[0],setForm=formState[1];
  var editingState=useState(""),editing=editingState[0],setEditing=editingState[1];
  var infoState=useState(""),info=infoState[0],setInfo=infoState[1];
  var filterState=useState("open"),filter=filterState[0],setFilter=filterState[1];
  var permissionState=useState(("Notification" in window)?Notification.permission:"unsupported"),permission=permissionState[0],setPermission=permissionState[1];
  useEffect(function(){
    var refresh=function(){setItems(load());};
    window.addEventListener(eventName,refresh);
    window.addEventListener("storage",refresh);
    return function(){window.removeEventListener(eventName,refresh);window.removeEventListener("storage",refresh);};
  },[]);
  function updateField(key,v){setForm(function(p){return Object.assign({},p,{[key]:v});});}
  function reset(){setEditing("");setForm({name:"",phone:"",amount:"",concept:"",dueAt:defaultDue()});}
  function persist(next,msg){if(!save(next)){setInfo("No se pudo guardar en este dispositivo. Revisá el almacenamiento.");return;}setItems(next);setInfo(msg);}
  function submit(e){
    e.preventDefault();
    var name=String(form.name||"").trim(),phone=String(form.phone||"").trim(),amount=Number(form.amount),dueAt=String(form.dueAt||"");
    if(!name||!numberForWhatsapp(phone)||!Number.isFinite(amount)||amount<=0||!Number.isFinite(Date.parse(dueAt))){setInfo("Completá nombre, teléfono con código de área, importe válido y fecha/hora.");return;}
    var old=items.find(function(x){return x.id===editing;});
    var item={id:editing||String(Date.now())+"-"+Math.random().toString(36).slice(2,9),name:name,phone:phone,
      amount:Math.round(amount),concept:String(form.concept||"").trim(),dueAt:dueAt,status:old?old.status:"pending",
      createdAt:old?old.createdAt:new Date().toISOString(),paidAt:old?old.paidAt:"",
      waOpenedAt:old?old.waOpenedAt:"",notifiedForAt:old&&old.dueAt===dueAt?old.notifiedForAt:""};
    var next=editing?items.map(function(x){return x.id===editing?item:x;}):[item].concat(items);
    persist(next,editing?"Recordatorio actualizado.":"Recordatorio programado.");
    reset();
  }
  function edit(r){setEditing(r.id);setForm({name:r.name,phone:r.phone,amount:String(r.amount),concept:r.concept,dueAt:r.dueAt});setInfo("Editando recordatorio de "+r.name+".");}
  function status(r,status){
    persist(items.map(function(x){return x.id===r.id?Object.assign({},x,{status:status,paidAt:status==="paid"?new Date().toISOString():"",notifiedForAt:status==="pending"?"":x.notifiedForAt}):x;}),status==="paid"?"Cobro marcado como recibido.":"Cobro reactivado.");
  }
  function remove(r){if(!window.confirm("¿Eliminar el recordatorio de "+r.name+"?"))return;persist(items.filter(function(x){return x.id!==r.id;}),"Recordatorio eliminado.");}
  function opened(r){persist(items.map(function(x){return x.id===r.id?Object.assign({},x,{waOpenedAt:new Date().toISOString()}):x;}),"WhatsApp abierto. El envío se confirma únicamente desde WhatsApp.");}
  function requestPermission(){
    if(!("Notification" in window)){setInfo("Este navegador no permite notificaciones del sistema. Los avisos siguen visibles en el panel.");return;}
    Notification.requestPermission().then(function(p){setPermission(p);if(p==="granted"){setInfo("Notificaciones activadas. Recibirás avisos mientras la app esté abierta.");notifyDue();}else setInfo("Podés consultar los cobros vencidos desde el panel sin notificaciones del sistema.");}).catch(function(){setInfo("El navegador bloqueó el permiso de notificaciones.");});
  }
  var list=items.filter(function(r){return filter==="all"||(filter==="paid"?r.status==="paid":r.status!=="paid");}).slice().sort(function(a,b){return dateNumber(a)-dateNumber(b);});
  var open=items.filter(function(x){return x.status!=="paid";});
  var total=open.reduce(function(sum,x){return sum+x.amount;},0);
  return h("section",{className:"la-reminders-shell",id:"la-admin-cobros", "aria-label":"Recordatorios de cobro"},
    h("h2",{className:"la-reminders-title"},"Recordatorios de cobro"),
    h("p",{className:"la-reminders-sub"},"Programá cuándo querés que te avisemos sobre una persona que te debe abonar. El día indicado aparecerá una alerta en el panel y podrás abrir WhatsApp con un mensaje empático, listo para enviar."),
    h("div",{className:"la-reminders-summary"},
      h("div",{className:"la-reminders-chip"},h("strong",null,String(open.length)),"Cobros pendientes"),
      h("div",{className:"la-reminders-chip"},h("strong",null,String(dueItems(items).length)),"Para recordar ahora"),
      h("div",{className:"la-reminders-chip"},h("strong",null,money.format(total)),"Importe pendiente")),
    h("form",{onSubmit:submit},
      h("div",{className:"la-reminders-grid"},
        h("label",{className:"la-reminders-field"},"Nombre y apellido",h("input",{required:true,maxLength:120,value:form.name,onChange:function(e){updateField("name",e.target.value);},placeholder:"Ej.: María Pérez",autoComplete:"off"})),
        h("label",{className:"la-reminders-field"},"WhatsApp del cliente",h("input",{required:true,type:"tel",inputMode:"tel",value:form.phone,onChange:function(e){updateField("phone",e.target.value);},placeholder:"Ej.: 351 1234567 o +54 9...",autoComplete:"off"})),
        h("label",{className:"la-reminders-field"},"Monto pendiente en pesos ($)",h("input",{required:true,type:"number",min:"1",step:"1",inputMode:"numeric",value:form.amount,onChange:function(e){updateField("amount",e.target.value);},placeholder:"Ej.: 15000"})),
        h("label",{className:"la-reminders-field"},"Fecha y hora del aviso",h("input",{required:true,type:"datetime-local",value:form.dueAt,onChange:function(e){updateField("dueAt",e.target.value);}})),
        h("label",{className:"la-reminders-field la-reminders-wide"},"Concepto (opcional)",h("input",{maxLength:180,value:form.concept,onChange:function(e){updateField("concept",e.target.value);},placeholder:"Ej.: Fotos del partido All Boys – Medea"}))),
      h("div",{className:"la-reminders-actions"},
        h("button",{type:"submit",className:"la-reminders-btn la-reminders-primary"},editing?"Guardar cambios":"Programar recordatorio"),
        editing&&h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:reset},"Cancelar edición"),
        h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:requestPermission},permission==="granted"?"🔔 Notificaciones activadas":"🔔 Activar avisos del navegador")),
      info&&h("p",{role:"status",className:"la-reminders-feedback"},info)),
    h("p",{className:"la-reminders-privacy"},"Importante: por ahora los cobros se guardan solamente en este navegador y dispositivo. Las notificaciones del sistema funcionan con la app abierta y el permiso concedido. Para un aviso aunque esté cerrada, exportá el recordatorio al calendario y activá su alerta al importarlo. WhatsApp NO envía mensajes solo: al tocar el botón se abre el texto preparado para que confirmes su envío."),
    h("div",{className:"la-reminders-actions"},
      h("button",{type:"button",onClick:function(){setFilter("open");},className:"la-reminders-btn "+(filter==="open"?"la-reminders-primary":"la-reminders-muted")},"Pendientes"),
      h("button",{type:"button",onClick:function(){setFilter("paid");},className:"la-reminders-btn "+(filter==="paid"?"la-reminders-primary":"la-reminders-muted")},"Cobrados"),
      h("button",{type:"button",onClick:function(){setFilter("all");},className:"la-reminders-btn "+(filter==="all"?"la-reminders-primary":"la-reminders-muted")},"Todos")),
    h("div",{className:"la-reminders-list"},
      list.length===0&&h("p",{className:"la-reminders-sub"},"Todavía no hay cobros en esta vista."),
      list.map(function(r){
        var due=r.status!=="paid"&&dateNumber(r)<=Date.now(),url=whatsappLink(r);
        return h("article",{key:r.id,className:"la-reminders-card "+(r.status==="paid"?"paid":due?"due":"")},
          h("div",{className:"la-reminders-card-head"},
            h("div",{className:"la-reminders-card-name"},r.name),
            h("span",{className:"la-reminders-pill"},r.status==="paid"?"COBRADO":due?"RECORDAR AHORA":"PROGRAMADO")),
          h("div",{className:"la-reminders-card-amount"},money.format(r.amount)),
          h("div",{className:"la-reminders-card-meta"},
            h("div",null,"📅 "+whenString(r.dueAt)),
            h("div",null,"📱 "+r.phone),
            r.concept&&h("div",null,"📷 "+r.concept),
            r.waOpenedAt&&h("div",null,"WhatsApp abierto: "+whenString(r.waOpenedAt))),
          h("div",{className:"la-reminders-actions"},
            r.status!=="paid"&&url&&h("a",{href:url,target:"_blank",rel:"noopener noreferrer",className:"la-reminders-btn la-reminders-wa",onClick:function(){opened(r);}},"Enviar WhatsApp"),
            h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:function(){exportCalendar(r);}},"📅 Agregar al calendario"),
            r.status!=="paid"&&h("button",{type:"button",className:"la-reminders-btn la-reminders-paid",onClick:function(){status(r,"paid");}},"✓ Marcar cobrado"),
            r.status==="paid"&&h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:function(){status(r,"pending");}},"Reabrir"),
            h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:function(){edit(r);}},"Editar"),
            h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:function(){remove(r);}},"Eliminar")),
          r.status!=="paid"&&h("details",{className:"la-reminders-card-meta",style:{marginTop:12}},
            h("summary",{style:{cursor:"pointer",color:"#7dd3fc"}},"Ver / copiar mensaje"),
            h("textarea",{readOnly:true,value:reminderMessage(r),rows:9,style:{width:"100%",marginTop:8,borderRadius:10,padding:10,background:"#040c19",color:"#f8fafc",border:"1px solid #334155",boxSizing:"border-box"}}),
            h("button",{type:"button",className:"la-reminders-btn la-reminders-muted",onClick:function(){if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(reminderMessage(r)).then(function(){setInfo("Mensaje copiado.");}).catch(function(){setInfo("Seleccioná el mensaje para copiarlo.");});}},"Copiar mensaje")));
      })));
}
window.LAAdminReminders={Panel:PaymentReminders,getDueCount:getDueCount,getPendingCount:pendingCount,notifyDue:notifyDue,read:load,formatMessage:reminderMessage,whatsappLink:whatsappLink};
})();