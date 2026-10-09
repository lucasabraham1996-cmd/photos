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
async function multiRead(request) {
  const raw=await request.text();
  if(raw.length>1500000)throw Error("Solicitud demasiado grande");
  return JSON.parse(raw);
}
async function syncCatalogue(request,env,origin) {
  if(!env.MP_SETUP_KEY||request.headers.get("X-Setup-Key")!==env.MP_SETUP_KEY)return result({error:"No autorizado"},401,origin);
  let data;
  try{data=await multiRead(request);}catch(e){return result({error:String(e.message||e)},400,origin);}
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
  const requestId=crypto.randomUUID();
  const orderData={
    type:"online",processing_mode:"manual",total_amount:quote.amount.toFixed(2),
    external_reference:"LA-CART-TEST-"+requestId,
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
      if(path==="/webhook/mp"&&request.method==="POST")return await multiWebhook(request,env,url);
      return result({error:"Ruta inexistente"},404,origin);
    }catch(err){
      console.error("MP_TRIAL_ERROR",{route:path,error:String(err?.message||err).slice(0,150)});
      return result({error:"Error interno; reintentá"},500,origin);
    }
  }
};