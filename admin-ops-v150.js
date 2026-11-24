/* lucasabraham.ph | Admin operations v150: read-only analytics and publishing checks */
(function(){
"use strict";
const h=(tag,props,...children)=>React.createElement(tag,props,...children);
const money=v=>'$'+new Intl.NumberFormat('es-AR').format(Number(v)||0);
function exportCsv(filename,columns,records){
  // BOM facilita Excel en español. Evitar fórmulas que podrían ejecutarse al abrirlo.
  const csvValue=input=>{
    let value=String(input??'').replace(/[\r\n\u0000-\u001f]+/g,' ').trim();
    if(/^[=+\-@]/.test(value))value="'"+value;
    return '"'+value.replace(/"/g,'""')+'"';
  };
  const rows=[columns,...records].map(row=>row.map(csvValue).join(';')).join('\r\n');
  const blob=new Blob(['\ufeff'+rows],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);
}
function Sales({orders=[],allPhotos=[],views={},mpOrders=[],mpConnected=false,orderState}){
  const [period,setPeriod]=React.useState('30');
  const cutoff=period==='all'?0:Date.now()-Number(period)*86400000;
  const scope=orders.filter(o=>o&&o.type!=='benefit_redemption'&&(!cutoff||Date.parse(o.date||o.createdAt||'')>=cutoff));
  const paid=scope.filter(o=>['paid','manual_paid'].includes(orderState(o)));
  const amount=paid.reduce((total,o)=>total+(Number(orderState(o)==='manual_paid'?(o.manualPaymentAmount??o.total):o.total)||0),0);
  const byAlbum=new Map(),byCategory=new Map(),byPhoto=new Map(),byPhotoInfo=new Map();
  for(const o of paid)for(const p of o.items||[]){
    if(!p)continue;
    const album=String(p.albumName||o.albumName||'Sin identificar');
    const category=String(p.subAlbumName||p.category||'Sin categoría');
    byAlbum.set(album,(byAlbum.get(album)||0)+1);
    byCategory.set(category,(byCategory.get(category)||0)+1);
    const key=album+'|'+String(p.id||p.code||p.name||'');
    if(!key.endsWith('|')){
      byPhoto.set(key,(byPhoto.get(key)||0)+1);
      if(!byPhotoInfo.has(key))byPhotoInfo.set(key,{album,category,
        name:String(p.name||p.code||'Foto'),code:String(p.code||'')});
    }
  }
  const best=map=>[...map.entries()].sort((a,b)=>b[1]-a[1]).slice(0,5);
  const metric=(label,value)=>h('div',{className:'la-ops-stat',key:label},h('span',null,label),h('strong',null,value));
  const rank=(label,values)=>h('div',{className:'la-ops-rank',key:label},h('h4',null,label),
    ...(values.length?values.map(([name,count],i)=>h('div',{className:'la-ops-rank-row',key:i},h('span',null,(i+1)+'. '+name),h('b',null,count))):
      [h('p',{className:'la-ops-muted',key:'empty'},'Sin ventas identificadas en el período.')]));
  const local=Object.entries(views).map(([id,count])=>{
    const p=allPhotos.find(x=>x.id===id);
    return p?[p.name||p.code||id,Number(count)||0]:null;
  }).filter(Boolean).sort((a,b)=>b[1]-a[1]).slice(0,5);
  const missingDownloads=mpConnected?mpOrders.filter(o=>o&&o.paid===true&&(o.photos||[]).some(p=>!p||!p.download_url)).length:0;
  // Señalar coincidencias sospechosas, nunca cancelar, fusionar ni cobrar de nuevo automáticamente.
  const suspectOrders=[];
  const sorted=scope.filter(o=>o&&o.id&&Date.parse(o.date||o.createdAt||'')).slice()
      .sort((a,b)=>Date.parse(a.date||a.createdAt)-Date.parse(b.date||b.createdAt));
  for(let i=1;i<sorted.length;i++){
    const a=sorted[i-1],b=sorted[i];
    const phoneA=String(a.phone||a.customerPhone||'').replace(/\D/g,'');
    const phoneB=String(b.phone||b.customerPhone||'').replace(/\D/g,'');
    const interval=Math.abs(Date.parse(b.date||b.createdAt)-Date.parse(a.date||a.createdAt));
    if(phoneA.length>=9&&phoneA===phoneB&&a.id!==b.id&&
        Number(a.total||0)>0&&Number(a.total)===Number(b.total)&&interval<=8*60000)
      suspectOrders.push([a.id,b.id]);
    if(suspectOrders.length>=5)break;
  }
  const children=[];
  children.push(h('div',{className:'la-ops-head'},h('h3',null,'Rendimiento comercial'),h('p',null,'Ventas y fotos de pedidos acreditados disponibles.')));
  children.push(h('label',{className:'la-ops-period'},'Período ',
    h('select',{value:period,onChange:e=>setPeriod(e.target.value)},
       ...[['7','7 días'],['30','30 días'],['all','Todo']].map(([value,title])=>h('option',{value,key:value},title)))));
  children.push(h('div',{className:'la-ops-kpis'},
    metric('Ventas acreditadas',paid.length),metric('Facturación',money(amount)),
    metric('Ticket promedio',money(paid.length?amount/paid.length:0)),
    metric('Fotos identificadas',[...byPhoto.values()].reduce((a,b)=>a+b,0))));
  children.push(h('div',{className:'la-ops-ranks'},
    rank('Álbumes con más ventas',best(byAlbum)),rank('Categorías vendidas',best(byCategory)),
    rank('Fotos más vendidas',best(byPhoto))));
  children.push(h('div',{className:'la-ops-export'},
    h('button',{type:'button',onClick:()=>{
      const rows=paid.map(o=>[String(o.id||''),String(o.date||o.createdAt||''),
        String(orderState(o)),String(o.paymentProvider||o.channel||''),
        Number(orderState(o)==='manual_paid'?(o.manualPaymentAmount??o.total):o.total)||0,
        (o.items||[]).length]);
      exportCsv('lucasabraham-ventas-'+period+'-dias.csv',
        ['Pedido','Fecha','Estado','Canal','Total ARS','Fotos'],rows);
    }},'Exportar ventas CSV'),
    h('button',{type:'button',onClick:()=>{
      const rows=[...byPhoto.entries()].sort((a,b)=>b[1]-a[1]).map(([key,count])=>{
        const p=byPhotoInfo.get(key)||{};
        return [p.album||'',p.category||'',p.name||'',p.code||'',count];
      });
      exportCsv('lucasabraham-fotos-vendidas-'+period+'-dias.csv',
        ['Album','Categoria','Foto','Codigo','Veces vendida'],rows);
    }},'Exportar fotos vendidas CSV'),
    h('small',null,'Archivos generados con los pedidos acreditados consultados. No incluyen claves de acceso ni enlaces privados.')));
  children.push(h('details',{className:'la-ops-details'},h('summary',null,'Aperturas de fotos en este dispositivo (no globales)'),
    ...local.map(([name,count],i)=>h('p',{className:'la-ops-muted',key:i},name+': '+count+' aperturas'))));
  if(missingDownloads)children.push(h('p',{className:'la-ops-warning'},'Revisar '+missingDownloads+' compras pagadas de Mercado Pago: la fuente no informa algún enlace de descarga.'));
  if(suspectOrders.length)children.push(h('div',{className:'la-ops-warning'},
    'Posibles pedidos repetidos (mismo teléfono, importe y menos de 8 minutos): '+
      suspectOrders.map(pair=>pair.join(' / ')).join(' · ')+'. Revisar manualmente; no se modificó ningún cobro.'));
  children.push(h('p',{className:'la-ops-muted'},mpConnected?'MP conectado: según registros recuperados.':'MP sin conectar: puede faltar facturación.'));
  return h('section',{className:'la-ops-panel'},...children);
}
function albumIssues(album,sides){
  const warnings=[];
  if(!album)return warnings;
  const teams=sides(album);
  const photos=Array.isArray(album.photos)?album.photos:[];
  if(!album.cover)warnings.push('Falta foto de portada.');
  for(const t of [teams.home,teams.away]){
    if(!t.name)warnings.push('Un equipo no tiene nombre.');
    if(!(t.appLogo||t.logo))warnings.push('Falta escudo de '+(t.name||'un equipo')+'.');
  }
  if(!photos.length)warnings.push('No hay fotos publicadas.');
  if(!(album.subalbums||[]).length)warnings.push('No hay categorías separadas.');
  const noLink=photos.filter(p=>!(p.url||p.rawUrl||p.fullUrl)).length;
  if(noLink)warnings.push(noLink+' fotos sin enlace.');
  const invalid=photos.filter(p=>!p.free&&!(Number(p.price)>0)).length;
  if(invalid)warnings.push(invalid+' fotos sin precio de venta válido.');
  const codes=photos.map(p=>String(p.id||'')).filter(Boolean);
  if(new Set(codes).size!==codes.length)warnings.push('Identificadores de foto duplicados.');
  if(album.archived)warnings.push('El álbum está archivado.');
  return warnings;
}
function Publisher({albums=[],sides,toThumb,albumLink,onCopy}){
  const [albumId,setAlbumId]=React.useState('');
  const [from,setFrom]=React.useState('');
  const [to,setTo]=React.useState('');
  const [check,setCheck]=React.useState(null);
  const [busy,setBusy]=React.useState(false);
  const [status,setStatus]=React.useState('');
  const album=albums.find(a=>a.id===albumId)||albums[0]||null;
  const warnings=albumIssues(album,sides);
  const opts=(value,change,prompt)=>h('select',{value,onChange:e=>change(e.target.value)},
    h('option',{value:''},prompt),...albums.map(a=>h('option',{value:a.id,key:a.id},a.name)));
  async function probe(){
    if(!album||busy)return;
    setBusy(true);setCheck(null);
    const ss=sides(album);
    const sources=[album.cover,ss.home.appLogo||ss.home.logo,ss.away.appLogo||ss.away.logo,
      ...(album.photos||[]).slice(0,17).map(p=>p.url||p.rawUrl||p.fullUrl)].filter(Boolean).slice(0,20);
    const failed=[];
    await Promise.all(sources.map((url,i)=>new Promise(done=>{
      const img=new Image();let settled=false;
      const finish=success=>{if(settled)return;settled=true;clearTimeout(timer);if(!success)failed.push(i+1);done();};
      const timer=setTimeout(()=>finish(false),8000);
      img.onload=()=>finish(true);img.onerror=()=>finish(false);
      img.src=toThumb(url);
    })));
    setCheck({total:sources.length,failed});setBusy(false);
  }
  const report=[album&&album.name||'Sin álbum',...(warnings.length?warnings:['Datos básicos completos']),
      check?'Imágenes comprobadas: '+check.total+' · errores: '+check.failed.join(', '):''].join('\n');
  const content=[];
  content.push(h('div',{className:'la-ops-head'},h('h3',null,'Asistente para publicar álbumes'),h('p',null,'Portadas, escudos, categorías y precios antes de compartir.')));
  if(album)content.push(h('label',{className:'la-ops-field'},'Revisar álbum',
    h('select',{value:album.id,onChange:e=>{setAlbumId(e.target.value);setCheck(null);}},
      ...albums.map(a=>h('option',{value:a.id,key:a.id},a.name)))));
  content.push(h('div',{className:'la-ops-audit'},h('strong',{className:warnings.length?'la-ops-yellow':'la-ops-green'},
    warnings.length?warnings.length+' observaciones':'✓ Sin advertencias de metadatos'),
    ...warnings.map((x,i)=>h('p',{className:'la-ops-issue',key:i},'• '+x))));
  content.push(h('div',{className:'la-ops-buttons'},
    h('button',{disabled:!album||busy,onClick:probe},busy?'Comprobando…':'Comprobar hasta 20 imágenes'),
    h('button',{onClick:()=>navigator.clipboard.writeText(report).then(()=>setStatus('Informe copiado.')).catch(()=>setStatus('No se pudo copiar.'))},'Copiar informe'),
    album&&h('button',{onClick:()=>window.open(albumLink(album),'_blank','noopener')},'Abrir álbum')));
  if(check)content.push(h('p',{className:check.failed.length?'la-ops-warning':'la-ops-green'},
    check.total+' imágenes comprobadas. '+(check.failed.length?'Posibles fallos: muestras '+check.failed.join(', '):'Todas cargaron.')));
  content.push(h('div',{className:'la-ops-transfer'},h('h4',null,'Copiar configuración a otro álbum'),
    h('p',{className:'la-ops-muted'},'Copia elección de escudos, marca de agua y excepción del descuento general. No duplica imágenes, categorías ni precios de la planilla.'),
    h('div',{className:'la-ops-copy'},
      h('label',{className:'la-ops-field'},'Origen',opts(from,setFrom,'Elegí origen')),
      h('label',{className:'la-ops-field'},'Destino',opts(to,setTo,'Elegí destino'))),
    h('button',{disabled:!from||!to||from===to,onClick:()=>{onCopy(from,to);setStatus('Ajustes copiados.');}},'Copiar ajustes')));
  if(status)content.push(h('p',{className:'la-ops-green',role:'status'},status));
  content.push(h('p',{className:'la-ops-muted'},'Verificar imágenes no prueba el cobro ni el permiso de descarga del servidor.'));
  return h('section',{className:'la-ops-panel'},...content);
}
window.LAPhotoOps={Sales,Publisher,albumIssues};
})();