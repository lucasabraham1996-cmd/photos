/* Short, shareable addresses for lucasabrahamph.com.
   Legacy #/album/... links stay readable. No admin/payment secrets in path. */
(function (root) {
  'use strict';
  const sections = Object.freeze({inicio:'#/galeria',galeria:'#/galeria',admin:'#/admin',club:'#/club'});
  const reserved = new Set(['inicio','galeria','admin','club','album','assets','docs','tests','scripts','cloudflare','contrataciones','como-comprar','como-pedir','index','404','checkout','compras']);
  let reg = {bySlug:new Map(),byAlbum:new Map(),bySub:new Map()};
  const ascii = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const token = value => ascii(value).replace(/[^a-z0-9]/g,'');
  function albumBase(value) {
    const source=ascii(value).trim();
    const teams=source.split(/\s+(?:vs\.?|versus|contra)\s+|\s+[-–—]\s+/).map(token).filter(Boolean);
    return (teams.length>1 ? teams.join('_') : token(source)) || 'album';
  }
  function category(value) {
    const t=token(value);
    if(t.includes('primera')) return 'primera';
    if(t.includes('reserva')) return 'reserva';
    if(t.includes('cebollitas')) return 'cebollitas';
    return t || 'categoria';
  }
  function subWeight(value) {
    const t=category(value);
    return t==='primera'?1:t==='reserva'?2:t==='cebollitas'?3:99;
  }
  function setAlbums(albums) {
    const bySlug=new Map(),byAlbum=new Map(),bySub=new Map();
    const items=[...(albums || [])].sort((a,b) => (Number(a.publishedTs||a.dateTs)||0)-(Number(b.publishedTs||b.dateTs)||0) || String(a.id||'').localeCompare(String(b.id||'')));
    const alloc = raw => {
      const base=raw || 'album';
      let slug=base, n=2;
      while(reserved.has(slug)||bySlug.has(slug)) slug=base+'-'+(n++);
      return slug;
    };
    for(const a of items) {
      if(!a || !a.id) continue;
      const id=String(a.id);
      const base=alloc(albumBase(a.name || id));
      const subs=[...(a.subalbums || [])].filter(sa=>sa&&sa.id).sort((a,b)=>subWeight(a.name)-subWeight(b.name)||String(a.name||'').localeCompare(String(b.name||''),'es',{numeric:true,sensitivity:'base'}));
      const primary=subs.length ? String(subs[0].id) : '';
      byAlbum.set(id,base);
      bySlug.set(base,{albumId:id,subAlbumId:primary});
      for(let i=0;i<subs.length;i++) {
        const subid=String(subs[i].id);
        const suffix=i===0?base:alloc(base+'-'+category(subs[i].name || subid));
        if(i>0) bySlug.set(suffix,{albumId:id,subAlbumId:subid});
        bySub.set(id+'\u0000'+subid,suffix);
      }
    }
    reg={bySlug,byAlbum,bySub};
    return reg;
  }
  function pathForAlbum(albumId,subAlbumId) {
    const id=String(albumId||'');
    const slug=subAlbumId?reg.bySub.get(id+'\u0000'+String(subAlbumId)):reg.byAlbum.get(id);
    return slug ? '/'+slug : '';
  }
  function pathForHash(hash) {
    const h=String(hash||'');
    const m=h.match(/^#\/album\/([^/]+)(?:\/sub\/(.+))?$/);
    if(m) {
      try { return pathForAlbum(decodeURIComponent(m[1]),m[2]?decodeURIComponent(m[2]):''); } catch(e) { return ''; }
    }
    if(h==='#/galeria') return '/';
    if(h==='#/admin') return '/admin';
    if(h==='#/club') return '/club';
    return '';
  }
  function segment() {
    try {
      const v=decodeURIComponent(location.pathname||'/').replace(/^\/+|\/+$/g,'').toLowerCase();
      return /^[a-z0-9_-]+$/.test(v)?v:'';
    } catch(e) { return ''; }
  }
  function resolve() {
    const key=segment();
    if(sections[key])return sections[key];
    const route=reg.bySlug.get(key);
    if(!route)return '';
    return '#/album/'+encodeURIComponent(route.albumId)+(route.subAlbumId?'/sub/'+encodeURIComponent(route.subAlbumId):'');
  }
  function sync(hash) {
    const path=pathForHash(hash);
    if(!path)return;
    if (location.search && !/[?&](?:mp_return|mp_live|order_id|checkout_id)=/.test(location.search)) {
      // Keep unrelated login/configuration query parameters on legacy links.
      if (hash==='#/admin') return;
    }
    const search=/[?&](?:mp_return|mp_live|order_id|checkout_id)=/.test(location.search)?location.search:'';
    if(location.pathname+location.search+location.hash !== path+search) {
      try { history.replaceState(history.state,'',path+search); } catch(e) {}
    }
  }
  const albumUrl=(albumId,subId) => location.origin+(pathForAlbum(albumId,subId)||('/#/album/'+encodeURIComponent(albumId)+(subId?'/sub/'+encodeURIComponent(subId):'')));
  root.LAShortLinks={setAlbums,pathForAlbum,pathForHash,resolve,segment,sync,albumUrl,slugs:()=>[...reg.bySlug.keys()]};
})(window);
