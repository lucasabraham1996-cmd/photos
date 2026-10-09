// Bundle sin dependencias para el editor de Cloudflare. No incluye secretos.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export function buildWorker() {
const legacy = readFileSync(resolve(root,'cloudflare/worker-mp-trial.js'),'utf8')
  .replace(/export\s*\{[^}]+\};?\s*$/,'').replace('export default {','const trial = {');
const page = readFileSync(resolve(root,'cloudflare/mp-validation-page.js'),'utf8')
  .replace('export default ','const validationPage = ');
const live = readFileSync(resolve(root,'cloudflare/worker-mp.js'),'utf8')
  .replace(/^import .*;\r?\n/gm,'');
return 'const legacy = (()=>{\n'+legacy+
  '\nreturn { trial, computePriceBasket, hash };\n})();\n'+
  'const {trial,computePriceBasket,hash} = legacy;\n'+page+'\n'+live;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = resolve(process.argv[2] || '/tmp/lucasabraham-mp-deploy.mjs');
  writeFileSync(output,buildWorker());
  console.log(output);
}
