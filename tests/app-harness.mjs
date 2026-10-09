import { readFileSync } from 'node:fs';

// Ejecuta el código de la app con hooks y DOM mínimos, sin servicios externos.
export function appHarness(overrides = {}) {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  const start = html.indexOf('if (!window.React || !window.ReactDOM)');
  const end = html.indexOf('</script>', start);
  let script = html.slice(start, end);
  const appStart = script.indexOf('function App() {');
  const renderStart = script.indexOf('\n    return React.createElement(', appStart);
  if (renderStart < 0) throw Error('No se encontró el render de App');
  const names = [...script.slice(appStart, renderStart).matchAll(/const\s+\[(\w+),\s*\w+\]\s*=\s*useState\(/g)].map(m => m[1]);
  script = script.slice(0, renderStart) + `
    ctx.actions={buildOrderPackage,buildOrderConfirmationMessage,orderConfirmationWhatsappUrl,
      openClub,saveCheckoutCustomer,addClubProduct,addManualClubPoints,transferClubPoints,
      registerClubUser,redeemClubProduct,lookupClubPoints,clubAccountFromOrders,
      syncMpCatalogue,syncMpCatalogueAndRetry,submitMpTrial,beginMpTrial,setOrderDecisionAndClose};
` + script.slice(renderStart);
  const state = { ...overrides }, effects = [], storage = new Map(), requests = [];
  let cursor = 0, refCursor = 0;
  const refs = [];
  const React = {
    Component: class {}, Fragment: 'fragment', memo: fn => fn,
    createElement: (type, props, ...children) => ({ type, props: props || {}, children: children.flat().filter(v => v !== false && v != null) }),
    useState(initial) {
      const name = names[cursor++];
      if (!name) throw Error('Hook desconocido');
      if (!(name in state)) state[name] = typeof initial === 'function' ? initial() : initial;
      return [state[name], value => { state[name] = typeof value === 'function' ? value(state[name]) : value; }];
    },
    useMemo: fn => fn(), useEffect: fn => effects.push(fn),
    useRef(value) { const index = refCursor++; return refs[index] || (refs[index] = { current: value }); }
  };
  const document = {
    head: { appendChild() {} }, body: { appendChild() {} }, hidden: false,
    getElementById() { return null; }, querySelector() { return null; },
    querySelectorAll() { return []; }, addEventListener() {}, removeEventListener() {},
    createElement() { return { style: {}, getContext() { return null; }, setAttribute() {}, appendChild() {} }; }
  };
  const ctx = {
    React, ReactDOM: {}, document, state, effects, requests, actions: {},
    window: { React, ReactDOM: {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() {}, scrollTo() {} },
    location: { origin: 'https://lucasabraham1996-cmd.github.io', pathname: '/photos/', hash: '#/galeria', search: '', href: 'https://lucasabraham1996-cmd.github.io/photos/' },
    navigator: {}, history: { replaceState() {} }, indexedDB: undefined,
    localStorage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) },
    sessionStorage: { getItem() { return null; }, setItem() {} },
    setTimeout() {}, setInterval() {}, clearTimeout() {}, clearInterval() {}, addEventListener() {}, removeEventListener() {}, alert() {},
    fetch: async (...args) => { requests.push(args); throw Error('No hay red en este harness'); }
  };
  ctx.window.location = ctx.location;
  const code = new Function('ctx', 'with(ctx){' + script + ';return {App,normalizeAlbums,saveOrderRemote};}')(ctx);
  const render = () => { cursor = 0; refCursor = 0; effects.length = 0; return code.App(); };
  return { ...code, ctx, state, effects, storage, render, actions: () => ctx.actions };
}
export function nodes(node) {
  return typeof node === 'object' && node !== null ? [node, ...node.children.flatMap(nodes)] : [];
}
export function textContent(node) {
  return typeof node === 'object' && node !== null ? node.children.map(textContent).join(' ') : String(node);
}
