const legacy = (()=>{
/* lucasabraham.ph — Checkout Pro de PRUEBA; no apto para ventas reales ni facturación. */
const MP = "https://api.mercadopago.com/v1/orders";
const ORIGIN = "https://lucasabraham1996-cmd.github.io";
const PRICE = 2000;
// El panel de Mercado Pago expone el USUARIO de prueba, NO su correo.
// Orders sandbox requiere un payer.email con dominio @testuser.com cuando se envía payer.
// Se usa un correo genérico de prueba; si el secreto trae un correo válido, se respeta.
// El correo de payer NO sustituye el login con la cuenta de prueba del checkout.
function getTestBuyerEmail(env) {
  const email=String(env.MP_TEST_BUYER_EMAIL||"").trim().toLowerCase();
  return /^[^\s@]+@testuser\.com$/.test(email)?email:"test@testuser.com";
}
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

/* === PILOTO: cesta completa + álbum + promociones — fuente de precios en D1 === */
const MAX_CART = 500;
function intMoney(v) { const n=Number(v);return Number.isSafeInteger(n)&&n>=0&&n<=100000000?n:null; }
function pct(v,max=100){const n=Number(v);return Number.isFinite(n)&&n>=0&&n<=max?n:null;}
function normalizeCoupon(v){return String(v||"").trim().toUpperCase().replace(/\s+/g,"");}
function safePhotos(raw, albumId) {
  if(!Array.isArray(raw)||raw.length===0||raw.length>1800)throw Error("Un álbum debe contener entre 1 y 1800 fotos");
  const seen=new Set();
  return raw.map(photo=>{
    const id=String(photo.id||"").slice(0,180);
    const name=String(photo.name||"").trim().slice(0,200);
    const file=driveId(photo.driveLink||photo.rawUrl||"");
    if(!id||!name||!file||seen.has(id))throw Error("Foto duplicada o enlace Drive inválido en "+albumId);
    seen.add(id);
    return {id,name,drive_id:file};
  });
}
function computePriceBasket(requested,catalogRows,coupons) {
  const kind=requested.kind==="album"?"album":requested.kind==="photos"?"photos":"";
  if(!kind)throw Error("Tipo de compra inválido");
  const rows=new Map(catalogRows.map(r=>[r.album_id,r]));
  if(kind==="album"){
    const id=String(requested.album_id||"");
    const album=rows.get(id);
    if(!album)throw Error("Álbum sin sincronizar; consultá al administrador");
    if(requested.print_ids?.length)throw Error("La impresión no forma parte del álbum completo");
    if(normalizeCoupon(requested.coupon))throw Error("Los cupones actuales se aplican al carrito de fotografías");
    const photos=JSON.parse(album.photos_json);
    const total=Math.round(album.full_price*(1-album.discount_percent/100));
    if(total<1)throw Error("El precio del álbum no está configurado");
    return {kind,amount:total,items:photos.map(p=>({...p,album_id:id})),printed:[],quantity:photos.length,base_total:album.full_price,percent:album.discount_percent,coupon:""};
  }
  const ids=requested.items;
  if(!Array.isArray(ids)||ids.length<1||ids.length>MAX_CART)throw Error("Elegí entre 1 y 500 fotografías");
  const seen=new Set();
  const selected=ids.map(item=>{
    const albumId=String(item.album_id||"");
    const photoId=String(item.photo_id||"");
    if(!albumId||!photoId)throw Error("Selección de fotos incompleta");
    const key=albumId+"::"+photoId;
    if(seen.has(key))throw Error("La misma foto no puede cobrarse dos veces");
    seen.add(key);
    const album=rows.get(albumId);
    if(!album)throw Error("La galería todavía no está sincronizada con Mercado Pago");
    const photo=JSON.parse(album.photos_json).find(p=>p.id===photoId);
    if(!photo)throw Error("Una foto ya no está disponible; recargá la galería");
    return {...photo,album_id:albumId,site_percent:album.discount_percent};
  });
  const cartDiscount=selected.length>=5?.15:selected.length>=3?.10:0;
  // Misma regla que la app: cada foto se redondea después de aplicar ambos descuentos.
  const discounted=selected.reduce((sum,p)=>sum+Math.round(2000*(1-cartDiscount)*(1-p.site_percent/100)),0);
  let couponPct=0;
  const couponCode=normalizeCoupon(requested.coupon);
  if(couponCode){
    const found=coupons.find(c=>normalizeCoupon(c.code)===couponCode&&c.active!==false);
    if(!found)throw Error("El cupón no existe o no está activo");
    couponPct=pct(found.percent,90);
    if(couponPct===null)throw Error("Configuración de cupón inválida");
  }
  const printIds=Array.isArray(requested.print_ids)?requested.print_ids.map(String):[];
  if(printIds.length>MAX_CART||new Set(printIds).size!==printIds.length)throw Error("Selección de impresiones inválida");
  for(const id of printIds)if(!selected.some(p=>p.id===id))throw Error("Solo se pueden imprimir fotos incluidas en el carrito");
  const digital=Math.round(discounted*(1-couponPct/100));
  const amount=digital+printIds.length*3000;
  if(amount<1)throw Error("El total de la compra debe ser mayor a cero");
  return {kind,amount,items:selected.map(({site_percent,...rest})=>rest),printed:printIds,quantity:selected.length,
    base_total:selected.length*2000,cart_discount_percent:cartDiscount*100,coupon:couponCode,coupon_percent:couponPct,print_surcharge:printIds.length*3000};
}
async function multiRead(request,maxSize=1500000) {
  const raw=await request.text();
  if(raw.length>maxSize)throw Error("Solicitud demasiado grande");
  return JSON.parse(raw);
}
async function syncCatalogue(request,env,origin) {
  if(!env.MP_SETUP_KEY||request.headers.get("X-Setup-Key")!==env.MP_SETUP_KEY)return result({error:"No autorizado"},401,origin);
  let data;
  try{data=await multiRead(request,6000000);}catch(e){return result({error:String(e.message||e)},400,origin);}
  const albums=data.albums;
  const config=data.discountSettings||{};
  const coupons=data.coupons;
  if(!Array.isArray(albums)||albums.length===0||albums.length>120)return result({error:"El catálogo debe tener entre 1 y 120 álbumes"},400,origin);
  if(!Array.isArray(coupons)||coupons.length>300)return result({error:"Cupones inválidos"},400,origin);
  const global=pct(config.percent||0);
  if(global===null)return result({error:"Descuento web inválido"},400,origin);
  const cleanCoupons=[];
  for(const c of coupons){
    if(!normalizeCoupon(c.code)||pct(c.percent,90)===null)return result({error:"Cupón inválido"},400,origin);
    cleanCoupons.push({code:normalizeCoupon(c.code),percent:Number(c.percent),active:c.active!==false});
  }
  let totalPhotos=0;
  const commands=[];
  const now=new Date().toISOString();
  try{
    const distinct=new Set();
    for(const album of albums){
      const id=String(album.id||"").slice(0,180);
      const name=String(album.name||"").trim().slice(0,200);
      if(!id||!name||distinct.has(id))throw Error("ID de álbum inválido o duplicado");
      distinct.add(id);
      const fullPrice=intMoney(album.fullPrice);
      if(fullPrice===null||fullPrice===0)throw Error("Precio de álbum inválido: "+name);
      const photos=safePhotos(album.photos,id);
      totalPhotos+=photos.length;
      const discount=(config.excludedAlbums||{})[id]?0:global;
      commands.push(env.LA_ORDERS_DB.prepare(
        "INSERT INTO la_mp_catalog(album_id,album_name,full_price,discount_percent,photos_json,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(album_id) DO UPDATE SET album_name=excluded.album_name,full_price=excluded.full_price,discount_percent=excluded.discount_percent,photos_json=excluded.photos_json,updated_at=excluded.updated_at"
      ).bind(id,name,fullPrice,discount,JSON.stringify(photos),now));
    }
  }catch(e){return result({error:String(e.message||e)},400,origin);}
  commands.push(env.LA_ORDERS_DB.prepare(
    "INSERT INTO la_mp_pricing(id,coupons_json,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET coupons_json=excluded.coupons_json,updated_at=excluded.updated_at"
  ).bind(JSON.stringify(cleanCoupons),now));
  try{await env.LA_ORDERS_DB.batch(commands);}catch(e){
    console.error("MP_CATALOG_SYNC",{error:String(e.message||e).slice(0,180)});
    return result({error:"No se pudo sincronizar el catálogo. Revisá las tablas D1."},503,origin);
  }
  return result({ok:true,albums:albums.length,photos:totalPhotos,discount_web:global,synced_at:now},200,origin);
}
async function createBasket(request,env,origin) {
  // Las compras de este piloto solo se crean con la clave de pruebas.
  // En producción se reemplazará por un checkout público autenticado, con rate limiting.
  if(!env.MP_SETUP_KEY||request.headers.get("X-Setup-Key")!==env.MP_SETUP_KEY){
    return result({error:"Clave de pruebas incorrecta"},401,origin);
  }
  let input;
  try{input=await multiRead(request);}catch(_){return result({error:"Solicitud inválida"},400,origin);}
  const requested=input.selection||{};
  let albumIds=requested.kind==="album"?[String(requested.album_id||"")]:
    Array.isArray(requested.items)?requested.items.map(x=>String(x.album_id||"")):[];
  albumIds=[...new Set(albumIds)];
  if(!albumIds.length||albumIds.length>80)return result({error:"Selección inválida"},400,origin);
  const placeholders=albumIds.map(()=>"?" ).join(",");
  const catalog=await env.LA_ORDERS_DB.prepare(
    "SELECT * FROM la_mp_catalog WHERE album_id IN ("+placeholders+")"
  ).bind(...albumIds).all();
  const couponsRow=await env.LA_ORDERS_DB.prepare("SELECT coupons_json FROM la_mp_pricing WHERE id=1").first();
  if(!couponsRow)return result({error:"Sin catálogo sincronizado. Contactá al administrador."},409,origin);
  let quote;
  try{quote=computePriceBasket(requested,catalog.results||[],JSON.parse(couponsRow.coupons_json));}
  catch(e){return result({error:String(e.message||e)},409,origin);}
  const expected=intMoney(input.expected_total);
  if(expected===null||expected!==quote.amount)return result({
    error:"El precio cambió o el catálogo no coincide. Actualizá la página o sincronizá promociones.",
    expected_total:quote.amount,
    shown_total:expected,
    needs_refresh:true
  },409,origin);
  const payerEmail=getTestBuyerEmail(env);
  const requestId=crypto.randomUUID();
  const orderData={
    type:"online",processing_mode:"manual",total_amount:quote.amount.toFixed(2),
    external_reference:"LA-CART-TEST-"+requestId,
    payer:{email:payerEmail},
    items:[{title:quote.kind==="album"?"Album digital completo - "+String(requested.album_id||"").slice(0,60):"Fotografias deportivas digitales",quantity:1,unit_price:quote.amount.toFixed(2)}]
  };
  let response,mp;
  try{
    response=await fetch(MP,{method:"POST",headers:{Authorization:"Bearer "+env.MP_ACCESS_TOKEN_TEST,"Content-Type":"application/json",Accept:"application/json","X-Idempotency-Key":requestId},body:JSON.stringify(orderData)});
    mp=await response.json();
  }catch(_){return result({error:"Error al conectar con Mercado Pago"},502,origin);}
  if(!response.ok||!cleanId(mp.id)||!/^https:\/\//.test(mp.checkout_url||""))return result({error:String(mp.message||mp.error||"Mercado Pago rechazó el pago").slice(0,220)},502,origin);
  const token=randomToken();
  try{
    await env.LA_ORDERS_DB.prepare("INSERT INTO la_mp_bundle_orders(mp_order_id,receipt_hash,kind,amount,mp_status,status_detail,items_json,print_ids_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)")
      .bind(mp.id,await hash(token),quote.kind,quote.amount,String(mp.status||"created"),String(mp.status_detail||""),JSON.stringify(quote.items),JSON.stringify(quote.printed),new Date().toISOString(),new Date().toISOString()).run();
  }catch(e){
    console.error("MP_MULTI_SAVE",{error:String(e.message||e).slice(0,150)});
    return result({error:"No se registró el pedido. No pagues esta orden."},503,origin);
  }
  return result({ok:true,order_id:mp.id,receipt_token:token,checkout_url:mp.checkout_url,quote:{
    kind:quote.kind,amount:quote.amount,quantity:quote.quantity,
    print_count:quote.printed.length,base_total:quote.base_total,
    coupon:quote.coupon||"",coupon_percent:quote.coupon_percent||0,
    discount_percent:quote.cart_discount_percent||quote.percent||0
  },mode:"test"},200,origin);
}
async function basketReceipt(env,id,token) {
  if(!cleanId(id)||!/^[a-f0-9]{64}$/.test(String(token||"")))return null;
  const row=await env.LA_ORDERS_DB.prepare("SELECT * FROM la_mp_bundle_orders WHERE mp_order_id=?").bind(id).first();
  if(!row||await hash(token)!==row.receipt_hash)return null;
  return row;
}
async function basketStatus(request,env,origin) {
  let input;
  try{input=await multiRead(request);}catch(_){return result({error:"Solicitud inválida"},400,origin);}
  const row=await basketReceipt(env,input.order_id,input.receipt_token);
  if(!row)return result({error:"No se encontró la compra"},404,origin);
  const mp=await getMP(env,row.mp_order_id);
  if(!mp)return result({error:"No se pudo consultar el pago"},502,origin);
  const status=String(mp.status||"");
  const detail=String(mp.status_detail||"");
  await env.LA_ORDERS_DB.prepare("UPDATE la_mp_bundle_orders SET mp_status=?,status_detail=?,updated_at=? WHERE mp_order_id=?").bind(status,detail,new Date().toISOString(),row.mp_order_id).run();
  const paid=status==="processed"&&detail==="accredited";
  const items=JSON.parse(row.items_json);
  return result({
    ok:true,paid,status,status_detail:detail,kind:row.kind,amount:row.amount,
    print_requested:JSON.parse(row.print_ids_json).length>0,
    downloads:paid?items.map((p,index)=>({name:p.name,url:"/api/basket-download/"+encodeURIComponent(row.mp_order_id)+"/"+index+"?token="+encodeURIComponent(input.receipt_token)})):[]
  },200,origin);
}
async function basketDownload(request,env,url){
  const parts=url.pathname.split("/");
  const orderId=decodeURIComponent(parts[3]||"");
  const index=Number(parts[4]||"-1");
  if(!Number.isSafeInteger(index)||index<0)return result({error:"Índice inválido"},400);
  const row=await basketReceipt(env,orderId,url.searchParams.get("token"));
  if(!row)return result({error:"Acceso inválido"},403);
  if(row.mp_status!=="processed"||row.status_detail!=="accredited")return result({error:"Pago pendiente"},403);
  const items=JSON.parse(row.items_json);
  if(index>=items.length)return result({error:"Fotografía inexistente"},404);
  const id=String(items[index].drive_id||"");
  if(!/^[A-Za-z0-9_-]{10,100}$/.test(id))return result({error:"Imagen inválida"},500);
  return new Response(null,{status:302,headers:{Location:"https://drive.google.com/uc?export=download&id="+encodeURIComponent(id),"Cache-Control":"no-store","Referrer-Policy":"no-referrer"}});
}
async function multiWebhook(request,env,url) {
  if(!await verifyWebhook(request,url,env.MP_WEBHOOK_SECRET_TEST))return result({error:"Firma inválida"},401);
  const id=cleanId(url.searchParams.get("data.id"));
  if(!id)return result({ok:true});
  const row=await env.LA_ORDERS_DB.prepare("SELECT mp_order_id FROM la_mp_bundle_orders WHERE mp_order_id=?").bind(id).first();
  if(row){
    const mp=await getMP(env,id);
    if(!mp)return result({error:"Error consultando la orden"},502);
    await env.LA_ORDERS_DB.prepare("UPDATE la_mp_bundle_orders SET mp_status=?,status_detail=?,updated_at=? WHERE mp_order_id=?")
      .bind(String(mp.status||""),String(mp.status_detail||""),new Date().toISOString(),id).run();
    return result({ok:true});
  }
  const old=await env.LA_ORDERS_DB.prepare("SELECT mp_order_id FROM la_mp_test_orders WHERE mp_order_id=?").bind(id).first();
  if(old){
    const mp=await getMP(env,id);
    if(!mp)return result({error:"Error consultando la orden"},502);
    await refresh(env.LA_ORDERS_DB,id,mp);
  }
  return result({ok:true});
}

const trial = {
  async fetch(request,env) {
    const url=new URL(request.url);
    const origin=request.headers.get("Origin")||"";
    const path=url.pathname;
    if(request.method==="OPTIONS"&&path.startsWith("/api/")){
      if(origin!==ORIGIN)return result({error:"Origen no autorizado"},403);
      return new Response(null,{status:204,headers:{"Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Methods":"POST, OPTIONS","Access-Control-Allow-Headers":"Content-Type, X-Setup-Key","Access-Control-Max-Age":"600"}});
    }
    if(path==="/health")return result({ok:true,trial:true,database:Boolean(env.LA_ORDERS_DB),test_buyer_email_configured:Boolean(getTestBuyerEmail(env))});
    if(!env.LA_ORDERS_DB||!env.MP_ACCESS_TOKEN_TEST)return result({error:"Faltan D1 o credenciales de prueba"},503,origin);
    try{
      if(path==="/api/admin-catalog-sync"&&request.method==="POST")return await syncCatalogue(request,env,origin);
      if(path==="/api/basket-checkout"&&request.method==="POST")return await createBasket(request,env,origin);
      if(path==="/api/basket-status"&&request.method==="POST")return await basketStatus(request,env,origin);
      if(path.startsWith("/api/basket-download/")&&request.method==="GET")return await basketDownload(request,env,url);
      if(path==="/api/test-checkout"&&request.method==="POST"){
        if(!env.MP_SETUP_KEY||request.headers.get("X-Setup-Key")!==env.MP_SETUP_KEY)return result({error:"Clave de pruebas incorrecta"},401,origin);
        const body=await bodyJSON(request);
        const p=body.photo||{};
        const id=driveId(p.driveLink);
        const photoId=String(p.id||"").slice(0,180);
        const name=String(p.name||"").trim().slice(0,180);
        if(!id||!photoId||!name)return result({error:"Seleccioná una fotografía válida"},400,origin);
        // Solo una foto digital; el cliente no decide cuánto paga.
        const payerEmail=getTestBuyerEmail(env);
        const key=crypto.randomUUID();
        const payload={type:"online",processing_mode:"manual",total_amount:PRICE.toFixed(2),external_reference:"LA-TRIAL-"+key,payer:{email:payerEmail},items:[{title:"Fotografia deportiva digital",quantity:1,unit_price:PRICE.toFixed(2)}]};
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
      if(path==="/webhook/mp"&&request.method==="POST")return await multiWebhook(request,env,url);
      return result({error:"Ruta inexistente"},404,origin);
    }catch(err){
      console.error("MP_TRIAL_ERROR",{route:path,error:String(err?.message||err).slice(0,150)});
      return result({error:"Error interno; reintentá"},500,origin);
    }
  }
};

// El Worker productivo reutiliza el cálculo del piloto sin duplicar las tarifas.

return { trial, computePriceBasket, hash };
})();
const {trial,computePriceBasket,hash} = legacy;
const validationPage = String.raw`<!doctype html>
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

/* lucasabraham.ph: Orders API real, cerrada por defecto y compatible con el piloto.
 * Desplegar este módulo (o el bundle del script) conservando bindings y secretos.
 * MP_LIVE_MODE: disabled -> validation -> public, con evidencia real en D1.
 */

const API = 'https://api.mercadopago.com/v1/orders';
const APP_ORIGIN = 'https://lucasabraham1996-cmd.github.io';
const APP_URL = APP_ORIGIN + '/photos/';
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const TOKEN = /^[a-f0-9]{64}$/;
const ORDER = /^ORD(?!TST)[A-Z0-9]{10,100}$/;
const now = () => new Date().toISOString();

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
function json(data, status = 200, origin = '') {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'
  };
  if (origin === APP_ORIGIN) {
    headers['Access-Control-Allow-Origin'] = APP_ORIGIN;
    headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS';
    headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Setup-Key, X-Receipt-Token';
    headers.Vary = 'Origin';
  }
  return new Response(JSON.stringify(data), { status, headers });
}
async function readJSON(request) {
  const reader = request.body?.getReader();
  if (!reader) throw new HttpError(400, 'Solicitud vacía');
  const chunks = [];
  let size = 0;
  for (;;) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > 128000) { await reader.cancel(); throw new HttpError(413, 'Solicitud demasiado grande'); }
    chunks.push(part.value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const part of chunks) { bytes.set(part, offset); offset += part.length; }
  try { return JSON.parse(new TextDecoder().decode(bytes)); }
  catch (_) { throw new HttpError(400, 'Solicitud inválida'); }
}
function cents(value) {
  const match = String(value ?? '').match(/^(\d{1,10})(?:\.(\d{1,2}))?$/);
  if (!match) return null;
  const n = Number(match[1]) * 100 + Number((match[2] || '').padEnd(2, '0'));
  return Number.isSafeInteger(n) ? n : null;
}
function validationAmount(env) {
  const amount = Number(env.MP_VALIDATION_AMOUNT || 200);
  return Number.isSafeInteger(amount) && amount >= 100 && amount <= 500 ? amount : 200;
}
function requireAdmin(request, env) {
  if (!env.MP_SETUP_KEY || request.headers.get('X-Setup-Key') !== env.MP_SETUP_KEY)
    throw new HttpError(401, 'Esta validación requiere la clave de administración');
}
function liveReady(env) {
  return Boolean(env.LA_ORDERS_DB && env.MP_ACCESS_TOKEN_PROD && env.MP_WEBHOOK_SECRET_PROD && env.MP_SETUP_KEY);
}
async function verifiedValidation(env) {
  if (!env.LA_ORDERS_DB) return false;
  const row = await env.LA_ORDERS_DB.prepare(
    "SELECT checkout_id FROM la_mp_live_orders WHERE mode='validation' AND payment_valid=1 AND mp_status='processed' AND status_detail='accredited' AND before_payment_blocked_at IS NOT NULL AND paid_verified_at IS NOT NULL AND webhook_verified_at IS NOT NULL AND download_verified_at IS NOT NULL LIMIT 1"
  ).first();
  return Boolean(row);
}
async function paymentConfig(env) {
  const configured = String(env.MP_LIVE_MODE || 'disabled');
  const verified = configured === 'public' ? await verifiedValidation(env) : false;
  const publicEnabled = configured === 'public' && verified && liveReady(env);
  return {
    ok: true, mode: publicEnabled ? 'public' : configured === 'validation' ? 'validation' : 'disabled',
    public_enabled: publicEnabled, available: liveReady(env) && (configured === 'validation' || publicEnabled),
    validation_amount: validationAmount(env)
  };
}
async function rateLimit(request, env, category, limit) {
  const minute = Math.floor(Date.now() / 60000);
  const key = await hash((request.headers.get('CF-Connecting-IP') || 'unknown') + ':' + category + ':' + minute);
  const row = await env.LA_ORDERS_DB.prepare(
    'INSERT INTO la_mp_live_rate_limits(bucket_hash,attempts,expires_at) VALUES(?,1,?) ON CONFLICT(bucket_hash) DO UPDATE SET attempts=attempts+1 RETURNING attempts'
  ).bind(key, (minute + 2) * 60000).first();
  if (row.attempts > limit) throw new HttpError(429, 'Demasiados intentos. Esperá un minuto');
  if (category === 'checkout') await env.LA_ORDERS_DB.prepare(
    'DELETE FROM la_mp_live_rate_limits WHERE expires_at<?'
  ).bind(Date.now()).run();
}
async function fetchOrder(env, id) {
  try {
    const res = await fetch(API + '/' + encodeURIComponent(id), {
      headers: { Authorization: 'Bearer ' + env.MP_ACCESS_TOKEN_PROD, Accept: 'application/json' },
      signal: AbortSignal.timeout(10000)
    });
    if (!res.ok) throw Error('MP');
    return await res.json();
  } catch (_) { throw new HttpError(502, 'No se pudo verificar el pago con Mercado Pago'); }
}
function sameOrder(mp, row) {
  return ORDER.test(String(mp.id || '')) && (!row.mp_order_id || mp.id === row.mp_order_id) &&
    mp.live_mode !== false && mp.type === 'online' && mp.currency === row.currency &&
    mp.country_code === 'ARG' && mp.external_reference === row.external_reference &&
    cents(mp.total_amount) === row.amount * 100 &&
    /^\d+$/.test(String(mp.user_id || '')) &&
    (!row.seller_id || String(mp.user_id) === row.seller_id) &&
    /^\d+$/.test(String(mp.integration_data?.application_id || '')) &&
    (!row.application_id || String(mp.integration_data?.application_id) === row.application_id);
}
function paidOrder(mp, row) {
  return sameOrder(mp, row) && mp.status === 'processed' && mp.status_detail === 'accredited' &&
    cents(mp.total_paid_amount) === row.amount * 100;
}
async function refreshOrder(env, row) {
  const mp = await fetchOrder(env, row.mp_order_id);
  const paid = paidOrder(mp, row);
  const valid = sameOrder(mp, row);
  const status = valid ? String(mp.status || 'pending').slice(0,80) : 'verification_failed';
  const detail = valid ? String(mp.status_detail || '').slice(0,80) : 'order_mismatch';
  await env.LA_ORDERS_DB.prepare(
    'UPDATE la_mp_live_orders SET mp_status=?,status_detail=?,payment_valid=?,paid_verified_at=CASE WHEN ?=1 THEN COALESCE(paid_verified_at,?) ELSE paid_verified_at END,updated_at=? WHERE checkout_id=?'
  ).bind(status, detail, paid ? 1 : 0, paid ? 1 : 0, now(), now(), row.checkout_id).run();
  return { paid, status, status_detail: detail };
}
async function receipt(env, checkoutId, token) {
  if (!UUID.test(String(checkoutId || '')) || !TOKEN.test(String(token || ''))) return null;
  const row = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_live_orders WHERE checkout_id=?'
  ).bind(checkoutId).first();
  return row && await hash(token) === row.receipt_hash ? row : null;
}
function checkoutResult(row, token) {
  return {
    ok: true, checkout_id: row.checkout_id, order_id: row.mp_order_id, receipt_token: token,
    checkout_url: row.checkout_url, mode: row.mode,
    quote: { kind: row.kind, amount: row.amount, catalog_amount: row.catalog_amount,
      quantity: JSON.parse(row.items_json).length, print_count: JSON.parse(row.print_ids_json).length }
  };
}
function checkoutURL(value, id) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'www.mercadopago.com.ar' &&
      url.pathname.startsWith('/checkout/') && url.searchParams.get('order_id') === id;
  } catch (_) { return false; }
}
function returnURL(input, request, env, mode) {
  // El navegador no puede introducir una URL de retorno arbitraria.
  if (mode === 'validation' && input.return_to === 'validation')
    return new URL('/validation?mp_return=1', request.url).href;
  const url = new URL(env.MP_APP_URL || APP_URL);
  if (url.origin !== APP_ORIGIN || !url.pathname.startsWith('/photos/'))
    throw new HttpError(503, 'La URL de la aplicación no está configurada');
  url.search = '?mp_live=1&mp_return=1';
  // El fragmento contiene un comprobante de alta entropía, no se envía en la petición HTTP.
  // Permite recuperar el ticket cuando Mercado Pago vuelve a otro navegador del celular.
  url.hash = '#/compra/' + input.request_id + '/' + input.receipt_token;
  return url.href;
}
async function createCheckout(request, env) {
  const config = await paymentConfig(env);
  if (!config.available) throw new HttpError(503, 'Los cobros automáticos todavía no están habilitados');
  await rateLimit(request, env, 'checkout', 6);
  if (config.mode === 'validation') requireAdmin(request, env);
  const input = await readJSON(request);
  if (!UUID.test(String(input.request_id || '')) || !TOKEN.test(String(input.receipt_token || '')))
    throw new HttpError(400, 'Identificador de compra inválido');
  const requestHash = await hash(JSON.stringify({ selection: input.selection, expected_total: input.expected_total }));
  let row = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_live_orders WHERE checkout_id=?'
  ).bind(input.request_id).first();
  if (row) {
    if (row.receipt_hash !== await hash(input.receipt_token) || row.request_hash !== requestHash)
      throw new HttpError(409, 'El identificador pertenece a otra selección');
    if (row.mode !== config.mode) throw new HttpError(409, 'El modo de pago cambió; iniciá una nueva compra');
    if (row.mp_order_id) return checkoutResult(row, input.receipt_token);
  } else {
    const selection = input.selection || {};
    const ids = [...new Set(selection.kind === 'album' ? [String(selection.album_id || '')] :
      Array.isArray(selection.items) ? selection.items.map(p => String(p.album_id || '')) : [])];
    if (!ids.length || ids.length > 80) throw new HttpError(400, 'Selección inválida');
    const pricing = await env.LA_ORDERS_DB.prepare('SELECT * FROM la_mp_pricing WHERE id=1').first();
    if (!pricing) throw new HttpError(409, 'El catálogo todavía no está sincronizado');
    const albums = await env.LA_ORDERS_DB.prepare(
      'SELECT * FROM la_mp_catalog WHERE album_id IN (' + ids.map(() => '?').join(',') + ') AND updated_at=?'
    ).bind(...ids, pricing.updated_at).all();
    let quote;
    try { quote = computePriceBasket(selection, albums.results || [], JSON.parse(pricing.coupons_json)); }
    catch (err) { throw new HttpError(409, err.message); }
    if (input.expected_total !== quote.amount)
      throw new HttpError(409, 'El precio cambió. Actualizá el catálogo antes de continuar');
    if (config.mode === 'validation' &&
      (quote.kind !== 'photos' || quote.quantity !== 1 || quote.printed.length || quote.coupon))
      throw new HttpError(400, 'La validación real permite una sola foto digital, sin cupón ni impresiones');
    const stamp = now();
    const amount = config.mode === 'validation' ? validationAmount(env) : quote.amount;
    await env.LA_ORDERS_DB.prepare(
      'INSERT INTO la_mp_live_orders(checkout_id,receipt_hash,request_hash,external_reference,mode,kind,amount,catalog_amount,items_json,print_ids_json,return_url,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(checkout_id) DO NOTHING'
    ).bind(input.request_id, await hash(input.receipt_token), requestHash, 'LA-LIVE-' + input.request_id,
      config.mode, quote.kind, amount, quote.amount, JSON.stringify(quote.items), JSON.stringify(quote.printed),
      returnURL(input, request, env, config.mode), stamp, stamp).run();
    row = await receipt(env, input.request_id, input.receipt_token);
    if (!row || row.request_hash !== requestHash) throw new HttpError(409, 'Otro intento usa ese identificador');
  }
  // Payload y UUID persistidos antes del POST: reintentos conservan la misma orden.
  const payload = {
    type: 'online', processing_mode: 'manual', total_amount: row.amount.toFixed(2),
    external_reference: row.external_reference, expiration_time: 'P1D',
    description: row.mode === 'validation' ? 'Validacion real privada: fotografia digital' : 'Fotografias lucasabraham.ph',
    items: [{ title: row.mode === 'validation' ? 'Una fotografia digital - validacion privada' :
      row.kind === 'album' ? 'Album digital completo' : 'Fotografias deportivas e impresiones seleccionadas',
      quantity: 1, unit_price: row.amount.toFixed(2) }],
    config: { online: { success_url: row.return_url, failure_url: row.return_url,
      pending_url: row.return_url, auto_return: 'all' } }
  };
  // Se omite el payer ficticio del sandbox: el comprador usa su cuenta real.
  let res, mp;
  try {
    res = await fetch(API, { method: 'POST',
      headers: { Authorization: 'Bearer ' + env.MP_ACCESS_TOKEN_PROD, 'Content-Type': 'application/json',
        Accept: 'application/json', 'X-Idempotency-Key': row.checkout_id },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(10000) });
    mp = await res.json();
  } catch (_) { throw new HttpError(502, 'No se pudo crear la orden. Reintentá la misma compra'); }
  if (!res.ok || !sameOrder(mp, row) || !checkoutURL(mp.checkout_url, mp.id))
    throw new HttpError(502, 'Mercado Pago no devolvió una orden real válida. No se inició el pago');
  await env.LA_ORDERS_DB.prepare(
    'UPDATE la_mp_live_orders SET mp_order_id=?,checkout_url=?,seller_id=?,application_id=?,mp_status=?,status_detail=?,updated_at=? WHERE checkout_id=?'
  ).bind(mp.id, mp.checkout_url, String(mp.user_id), String(mp.integration_data.application_id),
    String(mp.status || 'created'), String(mp.status_detail || ''), now(), row.checkout_id).run();
  row = await receipt(env, row.checkout_id, input.receipt_token);
  return checkoutResult(row, input.receipt_token);
}
async function checkoutStatus(request, env) {
  await rateLimit(request, env, 'status', 60);
  const input = await readJSON(request);
  const row = await receipt(env, input.checkout_id, input.receipt_token);
  if (!row || !row.mp_order_id) throw new HttpError(404, 'Compra inexistente o comprobante inválido');
  const state = await refreshOrder(env, row);
  const items = JSON.parse(row.items_json);
  return { ok: true, ...state, checkout_id: row.checkout_id, order_id: row.mp_order_id,
    mode: row.mode, kind: row.kind, amount: row.amount,
    verification: { before_payment_blocked: Boolean(row.before_payment_blocked_at),
      webhook_received: Boolean(row.webhook_verified_at), download_verified: Boolean(row.download_verified_at) },
    print_requested: JSON.parse(row.print_ids_json).length > 0,
    downloads: state.paid ? items.map((p, i) => ({ name: p.name,
      url: '/api/live-download/' + row.checkout_id + '/' + i })) : [] };
}
// Solo administración. Nunca se entregan enlaces originales ni información de pedidos al público.
async function adminOrders(request,env) {
  requireAdmin(request,env);
  await rateLimit(request,env,'admin-orders',40);
  const body=await readJSON(request);
  const offset=Number(body.offset||0);
  if(!Number.isSafeInteger(offset)||offset<0||offset>100000)
    throw new HttpError(400,'Página inválida');
  const limit=50;
  const rows=await env.LA_ORDERS_DB.prepare(
    'SELECT checkout_id,mp_order_id,mode,kind,amount,items_json,print_ids_json,mp_status,status_detail,payment_valid,created_at,paid_verified_at,download_verified_at FROM la_mp_live_orders ORDER BY created_at DESC LIMIT ? OFFSET ?'
  ).bind(limit+1,offset).all();
  const records=rows.results||[];
  return {ok:true,offset,has_more:records.length>limit,orders:records.slice(0,limit).map(r=>{
    const photos=JSON.parse(r.items_json||'[]');
    return {
      checkout_id:r.checkout_id,order_id:r.mp_order_id||'',mode:r.mode,kind:r.kind,
      amount:r.amount,created_at:r.created_at,paid_at:r.paid_verified_at||null,
      payment_status:r.mp_status,payment_detail:r.status_detail,
      paid:r.payment_valid===1,downloaded:Boolean(r.download_verified_at),
      print_count:JSON.parse(r.print_ids_json||'[]').length,
      invoice_status:r.payment_valid===1?'pendiente_emision_arca':'no_corresponde',
      photos:photos.map(p=>({name:p.name||'Fotografía',album_id:p.album_id||'',photo_id:p.id||'',
        download_url:/^[a-zA-Z0-9_-]{10,100}$/.test(String(p.drive_id||''))?
          'https://drive.google.com/uc?export=download&id='+encodeURIComponent(p.drive_id):null}))
    };
  })};
}

async function recoverValidation(request, env) {
  requireAdmin(request, env);
  const config = await paymentConfig(env);
  if (!config.available || config.mode !== 'validation')
    throw new HttpError(503, 'La recuperación privada solo está disponible durante la validación');
  await rateLimit(request, env, 'recover', 6);
  const row = await env.LA_ORDERS_DB.prepare(
    "SELECT * FROM la_mp_live_orders WHERE mode='validation' AND paid_verified_at IS NOT NULL ORDER BY paid_verified_at DESC LIMIT 1"
  ).first();
  if (!row) throw new HttpError(404, 'No se encontró una compra de validación acreditada');
  const state = await refreshOrder(env, row);
  if (!state.paid) throw new HttpError(409, 'Mercado Pago no confirma la acreditación de esa compra. El pedido sigue registrado');
  // La clave de administración permite recuperar únicamente la validación privada.
  // Reemplazar el recibo perdido, conservando la orden, el pago y sus evidencias.
  const token = Array.from(crypto.getRandomValues(new Uint8Array(32)), x => x.toString(16).padStart(2,'0')).join('');
  await env.LA_ORDERS_DB.prepare(
    "UPDATE la_mp_live_orders SET receipt_hash=?,updated_at=? WHERE checkout_id=? AND mode='validation'"
  ).bind(await hash(token), now(), row.checkout_id).run();
  return { ...checkoutResult(row, token), name: JSON.parse(row.items_json)[0].name,
    verification: { before_payment_blocked: Boolean(row.before_payment_blocked_at),
      webhook_received: Boolean(row.webhook_verified_at) } };
}
function imageMime(bytes) {
  if (bytes.length >= 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if (bytes.length >= 8 && bytes.slice(0,8).every((v,i) => v === [137,80,78,71,13,10,26,10][i])) return 'image/png';
  if (bytes.length >= 12 && new TextDecoder().decode(bytes.slice(0,4)) === 'RIFF' &&
    new TextDecoder().decode(bytes.slice(8,12)) === 'WEBP') return 'image/webp';
  return '';
}
async function imageStream(file, onComplete) {
  if (!file.body) throw new HttpError(502, 'Drive no devolvió una imagen válida');
  const reader = file.body.getReader(), pending = [], prefix = new Uint8Array(100);
  const declared = file.headers.get('Content-Length') || '';
  const encoding = (file.headers.get('Content-Encoding') || 'identity').toLowerCase();
  const expected = encoding === 'identity' && /^\d+$/.test(declared) && Number.isSafeInteger(Number(declared))
    ? Number(declared) : null;
  let size = 0, prefixSize = 0, cancelled = false;
  const incomplete = () => new HttpError(502, 'No se pudo completar la fotografía. Tu pago sigue registrado; reintentá la descarga');
  try {
    // Solo conservar la cabecera de imagen y el bloque inicial, sin cargar el original completo.
    while (prefixSize < prefix.length) {
      const part = await reader.read();
      if (part.done) break;
      if (!part.value.byteLength) continue;
      size += part.value.byteLength;
      if (expected !== null && size > expected) throw incomplete();
      pending.push(part.value);
      const n = Math.min(prefix.length - prefixSize, part.value.byteLength);
      prefix.set(part.value.subarray(0, n), prefixSize);
      prefixSize += n;
    }
    if (prefixSize < prefix.length || !imageMime(prefix))
      throw new HttpError(502, 'Drive no devolvió una imagen válida');
  } catch (err) {
    await reader.cancel().catch(() => {});
    throw err instanceof HttpError ? err : incomplete();
  }
  const body = new ReadableStream({
    async pull(controller) {
      try {
        if (pending.length) { controller.enqueue(pending.shift()); return; }
        const part = await reader.read();
        if (cancelled) return;
        if (part.done) {
          if (expected !== null && size !== expected) throw incomplete();
          // Registrar evidencia solo tras EOF completo, nunca ante cancelación o error de Drive.
          if (onComplete) await onComplete();
          if (!cancelled) controller.close();
          return;
        }
        size += part.value.byteLength;
        if (expected !== null && size > expected) throw incomplete();
        controller.enqueue(part.value);
      } catch (_) {
        await reader.cancel().catch(() => {});
        if (!cancelled) controller.error(incomplete());
      }
    },
    cancel(reason) { cancelled = true; pending.length = 0; return reader.cancel(reason); }
  }, { highWaterMark: 0 });
  return { body, mime: imageMime(prefix) };
}
async function download(request, env, url) {
  await rateLimit(request, env, 'download', 60);
  const parts = url.pathname.split('/');
  const token = request.headers.get('X-Receipt-Token') || url.searchParams.get('token');
  const row = await receipt(env, parts[3], token);
  if (!row || !row.mp_order_id) throw new HttpError(403, 'Comprobante de compra inválido');
  const index = /^\d+$/.test(parts[4] || '') ? Number(parts[4]) : -1;
  const items = JSON.parse(row.items_json);
  if (!Number.isSafeInteger(index) || index < 0 || index >= items.length)
    throw new HttpError(404, 'Fotografía inexistente');
  const state = await refreshOrder(env, row); // Nunca confiar solo en un estado almacenado.
  if (!state.paid) {
    if (row.mode === 'validation' && state.status === 'created') await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET before_payment_blocked_at=COALESCE(before_payment_blocked_at,?),updated_at=? WHERE checkout_id=?'
    ).bind(now(), now(), row.checkout_id).run();
    throw new HttpError(403, 'La descarga se habilita cuando el pago está acreditado');
  }
  const item = items[index];
  if (!/^[A-Za-z0-9_-]{10,100}$/.test(item.drive_id)) throw new HttpError(503, 'Archivo no disponible');
  let file;
  try {
    file = await fetch('https://drive.google.com/uc?export=download&id=' + encodeURIComponent(item.drive_id),
      { redirect: 'follow', signal: AbortSignal.timeout(120000) });
  } catch (_) { throw new HttpError(502, 'No se pudo obtener la fotografía. Reintentá la descarga'); }
  const contentType = (file.headers.get('Content-Type') || '').split(';')[0].toLowerCase();
  if (!file.ok || !['image/jpeg','image/png','image/webp','application/octet-stream'].includes(contentType))
    throw new HttpError(502, 'El original de Drive no se pudo descargar. Tu pago sigue registrado');
  const { body, mime } = await imageStream(file, row.mode === 'validation' ? async () => {
    await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET download_verified_at=COALESCE(download_verified_at,?),updated_at=? WHERE checkout_id=?'
    ).bind(now(), now(), row.checkout_id).run();
  } : undefined);
  const filename = String(item.name || 'foto.jpg').replace(/[\r\n/\\]/g, '_').slice(0,200);
  return new Response(body, { headers: {
    'Content-Type': mime, 'Content-Disposition': "attachment; filename*=UTF-8''" + encodeURIComponent(filename),
    'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'
  } });
}
async function signatureValid(request, url, secret) {
  if (!secret) return false;
  const sig = request.headers.get('x-signature') || '';
  const timestamp = sig.match(/(?:^|,)\s*ts=(\d+)(?:,|$)/)?.[1];
  const signed = sig.match(/(?:^|,)\s*v1=([a-f0-9]{64})(?:,|$)/i)?.[1];
  const requestId = request.headers.get('x-request-id') || '';
  const id = url.searchParams.get('data.id') || '';
  if (!timestamp || !signed || !requestId || !ORDER.test(id) || requestId.length > 180) return false;
  const ms = Number(timestamp) < 100000000000 ? Number(timestamp) * 1000 : Number(timestamp);
  if (!Number.isSafeInteger(ms) || Math.abs(Date.now() - ms) > 15 * 60000) return false;
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['verify']);
  const bytes = new Uint8Array(signed.match(/../g).map(v => parseInt(v,16)));
  const text = 'id:' + id.toLowerCase() + ';request-id:' + requestId + ';ts:' + timestamp + ';';
  return crypto.subtle.verify('HMAC', key, bytes, new TextEncoder().encode(text));
}
async function webhook(request, env, url) {
  if (!await signatureValid(request, url, env.MP_WEBHOOK_SECRET_PROD))
    throw new HttpError(401, 'Firma de notificación inválida');
  const body = await readJSON(request);
  const id = url.searchParams.get('data.id');
  if (body.type !== 'order' || String(body.data?.id || '') !== id || body.live_mode !== true)
    throw new HttpError(400, 'Notificación incompatible con una compra real');
  const row = await env.LA_ORDERS_DB.prepare('SELECT * FROM la_mp_live_orders WHERE mp_order_id=?').bind(id).first();
  if (row) {
    const state=await refreshOrder(env, row); // Repeticiones y eventos fuera de orden consultan la fuente actual.
    if (state.paid) await env.LA_ORDERS_DB.prepare(
      'UPDATE la_mp_live_orders SET webhook_verified_at=COALESCE(webhook_verified_at,?) WHERE checkout_id=?'
    ).bind(now(), row.checkout_id).run();
  }
  return { ok: true };
}
async function diagnostics(request, env) {
  requireAdmin(request, env);
  const orders = await env.LA_ORDERS_DB.prepare(
    "SELECT checkout_id,mp_order_id,amount,currency,mode,mp_status,status_detail,payment_valid,before_payment_blocked_at,paid_verified_at,webhook_verified_at,download_verified_at,updated_at FROM la_mp_live_orders WHERE mode='validation' ORDER BY created_at DESC LIMIT 10"
  ).all();
  return { ok: true, ...(await paymentConfig(env)), verified_validation: await verifiedValidation(env),
    production_token_configured: Boolean(env.MP_ACCESS_TOKEN_PROD),
    production_webhook_configured: Boolean(env.MP_WEBHOOK_SECRET_PROD), orders: orders.results || [] };
}
async function validationSample(request, env) {
  requireAdmin(request, env);
  const pricing = await env.LA_ORDERS_DB.prepare('SELECT updated_at FROM la_mp_pricing WHERE id=1').first();
  if (!pricing) throw new HttpError(409, 'Primero sincronizá el catálogo');
  const rows = await env.LA_ORDERS_DB.prepare(
    'SELECT * FROM la_mp_catalog WHERE updated_at=? ORDER BY album_id LIMIT 1'
  ).bind(pricing.updated_at).all();
  const album = rows.results?.[0], photo = album && JSON.parse(album.photos_json)[0];
  if (!photo) throw new HttpError(409, 'No hay una fotografía válida en el catálogo');
  const selection = { kind: 'photos', items: [{ album_id: album.album_id, photo_id: photo.id }] };
  const quote = computePriceBasket(selection, [album], []);
  return { ok: true, selection, expected_total: quote.amount,
    name: photo.name, album_name: album.album_name, validation_amount: validationAmount(env) };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url), path = url.pathname, origin = request.headers.get('Origin') || '';
    if (path === '/validation' && request.method === 'GET') return new Response(validationPage, {
      headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
        'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        'X-Frame-Options': 'DENY' }
    });
    const livePath = path.startsWith('/api/live-') || path === '/api/admin-orders' || path === '/api/payment-config' || path === '/webhook/mp/live';
    if (!livePath && path !== '/health') return trial.fetch(request, env);
    if (request.method === 'OPTIONS') return json({}, 200, origin);
    try {
      if (origin && origin !== APP_ORIGIN && origin !== url.origin)
        throw new HttpError(403, 'Origen no autorizado');
      if (path === '/health') return json({ ok: true, trial: true, database: Boolean(env.LA_ORDERS_DB),
        live_configured: liveReady(env), public_payments: (await paymentConfig(env)).public_enabled });
      if (path === '/api/payment-config' && request.method === 'GET')
        return json(await paymentConfig(env), 200, origin);
      if (!env.LA_ORDERS_DB || !env.MP_ACCESS_TOKEN_PROD)
        throw new HttpError(503, 'La integración real todavía no está configurada');
      if (path === '/api/admin-orders' && request.method === 'POST')
        return json(await adminOrders(request,env),200,origin);
      if (path === '/api/live-checkout' && request.method === 'POST')
        return json(await createCheckout(request, env), 200, origin);
      if (path === '/api/live-status' && request.method === 'POST')
        return json(await checkoutStatus(request, env), 200, origin);
      if (path === '/api/live-recover' && request.method === 'POST')
        return json(await recoverValidation(request, env), 200, origin);
      if (path.startsWith('/api/live-download/') && request.method === 'GET') {
        const res = await download(request, env, url);
        if (origin === APP_ORIGIN) {
          res.headers.set('Access-Control-Allow-Origin', APP_ORIGIN);
          res.headers.set('Vary', 'Origin');
        }
        return res;
      }
      if (path === '/api/live-diagnostics' && request.method === 'POST')
        return json(await diagnostics(request, env), 200, origin);
      if (path === '/api/live-sample' && request.method === 'POST')
        return json(await validationSample(request, env), 200, origin);
      if (path === '/webhook/mp/live' && request.method === 'POST')
        return json(await webhook(request, env, url));
      throw new HttpError(404, 'Ruta inexistente');
    } catch (err) {
      // Nunca registrar cuerpos, URLs completas, headers, claves ni tokens de recibo.
      if (!(err instanceof HttpError)) console.error('LA_MP_LIVE_ERROR', { route: path });
      return json({ error: err instanceof HttpError ? err.message : 'Error interno. Tu compra sigue registrada' },
        err instanceof HttpError ? err.status : 500, origin);
    }
  }
};
