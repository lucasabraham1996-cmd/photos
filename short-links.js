/* Short, shareable addresses for lucasabrahamph.com.
   Legacy #/album/... links stay readable. No admin/payment secrets in path. */
(function (root) {
  'use strict';
  const sections = Object.freeze({inicio:'#/galeria',galeria:'#/galeria',admin:'#/admin',club:'#/club'});
  const reserved = new Set(['inicio','galeria','admin','club','album','assets','docs','tests','scripts','cloudflare','contrataciones','como-comprar','como-pedir','index','404','checkout','compras']);
  let reg = {bySlug:new Map(),byAlbum:new Map(),bySub:new Map()};
  const ascii = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const token = value => ascii(value).replace(/[^a-z0-9]/g,'');
  // Tres letras por equipo; All Boys siempre ALB.
  // Los nombres alternativos apuntan al mismo código en cualquier partido.
  const teamCodes=Object.freeze({
    allboys:'ALB', unionmalvinas:'MAL', malvinas:'MAL',
    unionflorida:'UFL', unionsanvicente:'USV', usv:'USV',
    caleracentral:'CAL', defensorescentralcordoba:'DCC',
    defensoresjuveniles:'DJU', centralcordoba:'CCO',
    atleticocarlospaz:'ACP', elcarmen:'CAR',
    dief:'DIE', medea:'MED', cibi:'CIB',
    deportivoalberdi:'DAL', vill asiburu:'VSI',
    villasiburu:'VSI', barrioparque:'BPA',
    parquevelez:'PVE', lasallano:'LAS',
    racing:'RAC', talleres:'TAL', sanlorenzo:'SLO',
    comercial:'COM', universitario:'UNI'
  });
  function codeForTeam(value) {
    const plain=ascii(value).trim();
    const key=token(plain);
    if(teamCodes[key]) return teamCodes[key];
    const words=plain.replace(/[^a-z0-9]+/g,' ').trim().split(/\s+/)
      .filter(w=>w && !['club','de','del','la','las','los','el','fc','ca'].includes(w));
    if(!words.length) return 'EQP';
    let code=words.length===1 ? words[0].slice(0,3)
      : words.length===2 ? words[0].slice(0,2)+words[1].slice(0,1)
      : words.slice(0,3).map(w=>w.charAt(0)).join('');
    return code.toUpperCase().padEnd(3,'X').slice(0,3);
  }
  function matchCode(name, album) {
    let title=String(name||'').split(':')[0].trim();
    const parts=title.split(/\s+(?:vs\.?|versus|contra)\s+|\s+[-–—]\s+/i)
      .map(s=>s.trim()).filter(Boolean);
    while(parts.length>2 && /^(primera|reserva|cebollitas|festejos|escuelita|galeria|participando|cuarta|quinta|sexta|septima|octava|inferiores)$/i.test(ascii(parts[parts.length-1]))) parts.pop();
    const teams=parts.length===2 ? parts
      : Array.isArray(album&&album.teamNames)&&album.teamNames.length>=2 ? album.teamNames.slice(0,2) : [];
    return teams.length===2 ? codeForTeam(teams[0])+codeForTeam(teams[1])
      : codeForTeam(title || (album&&album.id) || 'album');
  }
  function categorySegment(value) {
    const t=ascii(value).replace(/[^a-z0-9]+/g,' ').trim();
    if(!t) return 'Galeria';
    const labels={
      primera:'Primera', reserva:'Reserva', cebollitas:'Cebollitas',
      escuelita:'Escuelita', festejos:'Festejos',
      cuarta:'Cuarta', '4ta':'Cuarta', '4to':'Cuarta',
      quinta:'Quinta', '5ta':'Quinta', '5to':'Quinta',
      sexta:'Sexta', '6ta':'Sexta', '6to':'Sexta',
      septima:'Septima', '7ma':'Septima', octava:'Octava', '8va':'Octava',
      inferiores:'Inferiores', participando:'Participando', galeria:'Galeria'
    };
    return t.split(/\s+/).map(w=>labels[w]||w[0].toUpperCase()+w.slice(1)).join('-');
  }
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
    const items=[...(albums||[])].sort((a,b)=>(Number(a.publishedTs||a.dateTs)||0)-(Number(b.publishedTs||b.dateTs)||0)||String(a.id||'').localeCompare(String(b.id||'')));
    // Canonical URLs are short uppercase match codes, with a category directory.
    const allocCode=raw=>{
      const seed=raw||'ALBUM',key=()=>candidate.toLowerCase();
      let candidate=seed,n=2;
      while(reserved.has(key())||bySlug.has(key())) candidate=seed+(n++);
      return candidate;
    };
    const legacyAlloc=raw=>{
      const seed=raw||'album';
      let candidate=seed,n=2;
      while(reserved.has(candidate)||bySlug.has(candidate.toLowerCase())) candidate=seed+'-'+(n++);
      return candidate;
    };
    for(const a of items) {
      if(!a||!a.id)continue;
      const id=String(a.id);
      const base=allocCode(matchCode(a.name||id,a));
      const subs=[...(a.subalbums||[])].filter(sa=>sa&&sa.id)
        .sort((x,y)=>subWeight(x.name)-subWeight(y.name)||String(x.name||'').localeCompare(String(y.name||''),'es',{numeric:true,sensitivity:'base'}));
      const primary=subs.length?String(subs[0].id):'';
      byAlbum.set(id,'/'+base);
      bySlug.set(base.toLowerCase(),{albumId:id,subAlbumId:primary});
      for(const sub of subs) {
        const subid=String(sub.id),categoryBase=categorySegment(sub.name||subid);
        let path=base+'/'+categoryBase,n=2;
        while(bySlug.has(path.toLowerCase()))path=base+'/'+categoryBase+(n++);
        bySub.set(id+'\u0000'+subid,'/'+path);
        bySlug.set(path.toLowerCase(),{albumId:id,subAlbumId:subid});
      }
      // Keep all pre-existing links valid, including old /team_team-reserva paths.
      const legacyBase=legacyAlloc(albumBase(a.name||id));
      bySlug.set(legacyBase,{albumId:id,subAlbumId:primary});
      subs.forEach((sub,i)=>{
        if(i===0)return;
        const alias=legacyAlloc(legacyBase+'-'+category(sub.name||sub.id));
        bySlug.set(alias,{albumId:id,subAlbumId:String(sub.id)});
      });
    }
    reg={bySlug,byAlbum,bySub};
    return reg;
  }
  function pathForAlbum(albumId,subAlbumId) {
    const id=String(albumId||'');
    const slug=subAlbumId?reg.bySub.get(id+'\u0000'+String(subAlbumId)):reg.byAlbum.get(id);
    return slug || '';
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
      return /^[a-z0-9_-]+(?:\/[a-z0-9_-]+)?$/.test(v)?v:'';
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
