/* lucasabraham.ph — Checkout Pro de PRUEBA; no apto para ventas reales ni facturación. */
const MP = "https://api.mercadopago.com/v1/orders";
const ORIGIN = "https://lucasabraham1996-cmd.github.io";
const PRICE = 2000;
function result(data, status=200, origin="") {
  const h = {"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff"};
  if(origin===ORIGIN){h["Access-Control-Allow-Origin"]=ORIGIN;h["Access-Control-Allow-Methods"]="POST, OPTIONS";h["Access-Control-Allow-Headers"]="Content-Type, X-Setup-Key";h.Vary="Origin";}
  return new Response(JSON.stringify(data),{status,headers:h});
}
const hex=bytes=>Array.from(bytes,x=>x.toString(16).padStart(2,"0")).join("");
const randomToken=()=>hex(crypto.getRandomValues(new Uint8Array(32)));
async function hash(value){return hex(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(value))));}
function driveId(link) {
  try{
    const u=new URL(link);
    if(u.protocol!=="https:"||u.hostname!=="drive.google.com")return "";
    const m=u.pathname.match(/^\/file\/d\/([A-Za-z0-9_-]{10,100})(?:\/|$)/);
    const id=m?m[1]:u.searchParams.get("id");
    return /^[A-Za-z0-9_-]{10,100}$/.test(id||"")?id:"";
  }catch(_){return "";}
}
const cleanId=id=>/^[A-Za-z0-9_-]{6,100}$/.test(String(id||""))?String(id):"";
async function bodyJSON(request){const b=await request.text();if(b.length>8000)throw Error("Too long");return JSON.parse(b);}
async function getMP(env,id) {
  const response=await fetch(MP+"/"+encodeURIComponent(id),{headers:{Authorization:"Bearer "+env.MP_ACCESS_TOKEN_TEST,Accept:"application/json"}});
  return response.ok?response.json():null;
}
async function refresh(db,id,order) {
  const status=String(order.status||"");
  const detail=String(order.status_detail||"");
  await db.prepare("UPDATE la_mp_test_orders SET mp_status=?, status_detail=?, updated_at=? WHERE mp_order_id=?").bind(status,detail,new Date().toISOString(),id).run();
  return {status,detail,paid:status==="processed"&&detail==="accredited"};
}
async function receipt(db,id,token) {
  if(!cleanId(id)||!/^[a-f0-9]{64}$/.test(String(token||"")))return null;
  const row=await db.prepare("SELECT * FROM la_mp_test_orders WHERE mp_order_id=?").bind(id).first();
  return row&&(await hash(token))===row.receipt_hash?row:null;
}
async function verifyWebhook(req,url,secret) {
  if(!secret)return false;
  const sig=req.headers.get("x-signature")||"";
  const rid=req.headers.get("x-request-id")||"";
  const id=url.searchParams.get("data.id")||"";
  const ts=sig.match(/(?:^|,)\s*ts=([^,]+)/i)?.[1];
  const v1=sig.match(/(?:^|,)\s*v1=([a-f0-9]{64})(?:,|$)/i)?.[1];
  if(!rid||!id||!ts||!v1)return false;
  const key=await crypto.subtle.importKey("raw",new TextEncoder().encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  for(const variant of new Set([id.toLowerCase(),id])) {
    const plain="id:"+variant+";request-id:"+rid+";ts:"+ts+";";
    const signed=hex(new Uint8Array(await crypto.subtle.sign("HMAC",key,new TextEncoder().encode(plain))));
    if(signed===v1.toLowerCase())return true;
  }
  return false;
}
export default {
  async fetch(request,env) {
    const url=new URL(request.url);
    const origin=request.headers.get("Origin")||"";
    const path=url.pathname;
    if(request.method==="OPTIONS"&&path.startsWith("/api/")){
      if(origin!==ORIGIN)return result({error:"Origen no autorizado"},403);
      return new Response(null,{status:204,headers:{"Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Methods":"POST, OPTIONS","Access-Control-Allow-Headers":"Content-Type, X-Setup-Key","Access-Control-Max-Age":"600"}});
    }
    if(path==="/health")return result({ok:true,trial:true,database:Boolean(env.LA_ORDERS_DB)});
    if(!env.LA_ORDERS_DB||!env.MP_ACCESS_TOKEN_TEST)return result({error:"Faltan D1 o credenciales de prueba"},503,origin);
    try{
      if(path==="/api/test-checkout"&&request.method==="POST"){
        if(!env.MP_SETUP_KEY||request.headers.get("X-Setup-Key")!==env.MP_SETUP_KEY)return result({error:"Clave de pruebas incorrecta"},401,origin);
        const body=await bodyJSON(request);
        const p=body.photo||{};
        const id=driveId(p.driveLink);
        const photoId=String(p.id||"").slice(0,180);
        const name=String(p.name||"").trim().slice(0,180);
        if(!id||!photoId||!name)return result({error:"Seleccioná una fotografía válida"},400,origin);
        // Solo una foto digital; el cliente no decide cuánto paga.
        const key=crypto.randomUUID();
        const payload={type:"online",processing_mode:"manual",total_amount:PRICE.toFixed(2),external_reference:"LA-TRIAL-"+key,items:[{title:"Fotografia deportiva digital",quantity:1,unit_price:PRICE.toFixed(2)}]};
        const mpRes=await fetch(MP,{method:"POST",headers:{Authorization:"Bearer "+env.MP_ACCESS_TOKEN_TEST,"Content-Type":"application/json",Accept:"application/json","X-Idempotency-Key":key},body:JSON.stringify(payload)});
        const order=await mpRes.json();
        if(!mpRes.ok||!cleanId(order.id)||!/^https:\/\//.test(order.checkout_url||""))return result({error:String(order.message||order.error||"Mercado Pago rechazó la orden").slice(0,200)},502,origin);
        const token=randomToken();
        try{
          await env.LA_ORDERS_DB.prepare("INSERT INTO la_mp_test_orders (mp_order_id,receipt_hash,photo_id,photo_name,drive_id,amount,mp_status,status_detail,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)")
            .bind(order.id,await hash(token),photoId,name,id,PRICE,String(order.status||"created"),String(order.status_detail||""),new Date().toISOString(),new Date().toISOString()).run();
        }catch(e){
          console.error("MP_ORDER_DB_WRITE",{message:String(e?.message||e).slice(0,100)});
          return result({error:"No se pudo registrar la compra. No pagues esta orden."},503,origin);
        }
        return result({ok:true,order_id:order.id,receipt_token:token,checkout_url:order.checkout_url,amount:PRICE,test:true},200,origin);
      }
      if(path==="/api/trial-status"&&request.method==="POST"){
        const data=await bodyJSON(request);
        const row=await receipt(env.LA_ORDERS_DB,data.order_id,data.receipt_token);
        if(!row)return result({error:"Compra inexistente o enlace inválido"},404,origin);
        const live=await getMP(env,row.mp_order_id);
        if(!live)return result({error:"No se pudo consultar Mercado Pago"},502,origin);
        const info=await refresh(env.LA_ORDERS_DB,row.mp_order_id,live);
        return result({ok:true,paid:info.paid,status:info.status,status_detail:info.detail,photo_name:row.photo_name,amount:row.amount,download_url:info.paid?"/api/trial-download/"+encodeURIComponent(row.mp_order_id)+"?token="+encodeURIComponent(data.receipt_token):null},200,origin);
      }
      if(path.startsWith("/api/trial-download/")&&request.method==="GET"){
        const orderId=decodeURIComponent(path.split("/").pop());
        const row=await receipt(env.LA_ORDERS_DB,orderId,url.searchParams.get("token"));
        if(!row)return result({error:"Acceso inválido"},403);
        if(row.mp_status!=="processed"||row.status_detail!=="accredited")return result({error:"Pago pendiente"},403);
        return new Response(null,{status:302,headers:{Location:"https://drive.google.com/uc?export=download&id="+encodeURIComponent(row.drive_id),"Cache-Control":"no-store","Referrer-Policy":"no-referrer"}});
      }
      if(path==="/webhook/mp"&&request.method==="POST"){
        if(!await verifyWebhook(request,url,env.MP_WEBHOOK_SECRET_TEST))return result({error:"Firma inválida"},401);
        const id=cleanId(url.searchParams.get("data.id"));
        if(!id)return result({ok:true});
        const row=await env.LA_ORDERS_DB.prepare("SELECT mp_order_id FROM la_mp_test_orders WHERE mp_order_id=?").bind(id).first();
        if(!row)return result({ok:true}); // IDs antiguos/simulador
        const current=await getMP(env,id);
        if(!current)return result({error:"Error consultando orden"},502);
        await refresh(env.LA_ORDERS_DB,id,current);
        return result({ok:true});
      }
      return result({error:"Ruta inexistente"},404,origin);
    }catch(err){
      console.error("MP_TRIAL_ERROR",{route:path,error:String(err?.message||err).slice(0,150)});
      return result({error:"Error interno; reintentá"},500,origin);
    }
  }
};