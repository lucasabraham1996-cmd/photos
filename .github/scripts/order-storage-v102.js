const LAOrderStorage = (() => {
  const MAX_INLINE = 180000;
  const PART_LENGTH = 60000;
  const mutable = new Set(['delivered','rejected','status','paid','updatedAt','deliveredAt','rejectedAt','resolvedAt','cancelledAt']);
  const internal = new Set(['storageVersion','payloadMode','payloadHash','payloadLength','payloadChunkCount','itemCount','storageIncomplete','_firebasePath','appVersion']);
  const bytes = s => new TextEncoder().encode(s).length;
  function hash(s) { let h=2166136261; for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)} return (h>>>0).toString(16).padStart(8,'0') + '-' + s.length; }
  function payload(order) { const p={...order}; [...mutable,...internal].forEach(k=>delete p[k]);p.items=Array.isArray(p.items)?p.items:[];p.printedItems=Array.isArray(p.printedItems)?p.printedItems:[];p.printedPhotoIds=Array.isArray(p.printedPhotoIds)?p.printedPhotoIds:[];return p; }
  function split(s) { const parts=[]; for(let i=0;i<s.length;){let end=Math.min(i+PART_LENGTH,s.length);if(end<s.length&&s.charCodeAt(end-1)>=0xD800&&s.charCodeAt(end-1)<=0xDBFF)end++;parts.push(s.slice(i,end));i=end}return parts; }
  function prepare(order) {
    const raw=JSON.stringify(payload(order));
    const info={storageVersion:2,payloadHash:hash(raw),payloadLength:raw.length,itemCount:Array.isArray(order.items)?order.items.length:0};
    if(bytes(raw)<=MAX_INLINE)return {manifest:{...order,...info,payloadMode:'inline',payloadChunkCount:0},parts:[]};
    const parts=split(raw);
    const manifest={...order};
    delete manifest.items;delete manifest.printedItems;delete manifest.printedPhotoIds;
    Object.assign(manifest,info,{payloadMode:'chunks',payloadChunkCount:parts.length,items:[],printedItems:[],printedPhotoIds:[]});
    return {manifest,parts};
  }
  async function read(db,path,id,key) {
    const ref=db.collection(path).doc(key(id));
    const snap=await ref.get({source:'server'});
    if(!snap.exists)return null;
    return hydrate(ref,snap.data());
  }
  async function hydrate(ref,data) {
    if(data.storageVersion!==2||data.payloadMode!=='chunks')return data;
    const count=Number(data.payloadChunkCount);
    if(!Number.isInteger(count)||count<1||count>100000)throw new Error('Cantidad de partes inválida');
    const parts=[];
    for(let i=0;i<count;i+=8){
      const group=await Promise.all(Array.from({length:Math.min(8,count-i)},(_,n)=>ref.collection('payload').doc(String(i+n).padStart(6,'0')).get({source:'server'})));
      for(const snap of group){if(!snap.exists||typeof snap.data().part!=='string')throw new Error('Falta una parte del pedido');parts.push(snap.data().part)}
    }
    const raw=parts.join('');
    if(raw.length!==data.payloadLength||hash(raw)!==data.payloadHash)throw new Error('El detalle del pedido no coincide con el guardado');
    const p=JSON.parse(raw);
    if(!Array.isArray(p.items)||p.items.length!==data.itemCount)throw new Error('Faltan fotos en el pedido');
    return {...p,...data,items:p.items,printedItems:p.printedItems||[],printedPhotoIds:p.printedPhotoIds||[]};
  }
  async function persist(db,path,order,key) {
    const ref=db.collection(path).doc(key(order.id));
    const prepared=prepare(order);
    const before=await ref.get({source:'server'});
    if(before.exists){
      const old=before.data();
      if(old.storageVersion===2&&old.payloadHash===prepared.manifest.payloadHash){
        try { const found=await hydrate(ref,old);
          if(JSON.stringify(payload(found))===JSON.stringify(payload(order)))return true;
        } catch(e) { /* An interrupted upload is repaired with the same order ID. */ }
      }
      if(old.storageVersion===2&&old.payloadHash!==prepared.manifest.payloadHash)throw new Error('El código ya pertenece a otro pedido');
      if(old.date&&old.date!==order.date)throw new Error('El código ya pertenece a otro pedido');
    }
    for(let i=0;i<prepared.parts.length;i+=8){
      await Promise.all(prepared.parts.slice(i,i+8).map((part,n)=>ref.collection('payload').doc(String(i+n).padStart(6,'0')).set({part,index:i+n})));
    }
    const manifest={...prepared.manifest};
    if(before.exists){for(const field of mutable)delete manifest[field];}
    await ref.set(manifest,{merge:true});
    const found=await read(db,path,order.id,key);
    if(!found||found.payloadHash!==prepared.manifest.payloadHash||JSON.stringify(payload(found))!==JSON.stringify(payload(order)))throw new Error('No se pudo verificar el pedido completo');
    return true;
  }
  function verifiedAck(r,id,normalize) {
    if(!r||typeof r!=='object'||r.ok===false||r.success===false||r.error)return false;
    const returned=r.order?.id||r.order?.orderId||r.orderId||r.id||r.code;
    if(returned&&normalize(returned)!==normalize(id))return false;
    return r.ok===true||r.success===true||r.saved===true||r.created===true||['ok','success','saved'].includes(String(r.status||'').toLowerCase())||Boolean(r.order&&returned);
  }
  function createOutbox() {
    const name='LA_ORDER_OUTBOX_V2', fallback='LA_ORDER_OUTBOX_V2';
    let opening;
    function database(){
      if(!('indexedDB' in globalThis))return Promise.reject(new Error('IndexedDB no disponible'));
      if(!opening)opening=new Promise((resolve,reject)=>{const r=indexedDB.open(name,1);r.onupgradeneeded=()=>r.result.createObjectStore('orders',{keyPath:'id'});r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)}).catch(e=>{opening=null;throw e});
      return opening;
    }
    async function transaction(mode,action){const db=await database();return new Promise((resolve,reject)=>{const tx=db.transaction('orders',mode);const req=action(tx.objectStore('orders'));tx.oncomplete=()=>resolve(req.result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error)})}
    function localRead(){try{return JSON.parse(localStorage.getItem(fallback)||'[]')}catch(e){return []}}
    function localWrite(list){localStorage.setItem(fallback,JSON.stringify(list));}
    async function put(order){try{await transaction('readwrite',s=>s.put(order));return}catch(e){const list=localRead().filter(x=>x.id!==order.id);list.push(order);localWrite(list);if(!localRead().some(x=>x.id===order.id))throw new Error('No se pudo conservar el pedido en este dispositivo')}}
    async function all(){let rows=[];try{rows=await transaction('readonly',s=>s.getAll())}catch(e){}const map=new Map();[...localRead(),...rows].forEach(o=>{if(o&&o.id)map.set(o.id,o)});return [...map.values()]}
    async function remove(id){try{await transaction('readwrite',s=>s.delete(id))}catch(e){}try{localWrite(localRead().filter(o=>o.id!==id))}catch(e){}}
    return {put,all,remove};
  }
  return {prepare,persist,hydrate,read,verifiedAck,createOutbox,payload,hash};
})();