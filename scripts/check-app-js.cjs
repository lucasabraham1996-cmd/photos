const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
let count=0;
for(const script of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){
  if(/\bsrc\s*=|\btype\s*=\s*["'](?:application\/ld\+json|application\/json)/i.test(script[1]))continue;
  new vm.Script(script[2],{filename:'index-inline-'+(++count)+'.js'});
}
console.log(count+' scripts de la aplicación: sintaxis correcta');
