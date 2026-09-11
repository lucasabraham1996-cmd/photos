from pathlib import Path


def patch_index():
    p = Path('index.html')
    s = p.read_text(encoding='utf-8')

    if '<meta name="color-scheme" content="dark" />' not in s:
        s = s.replace(
            '<meta name="theme-color" content="#000000" />',
            '<meta name="theme-color" content="#000000" />\n  <meta name="color-scheme" content="dark" />',
            1,
        )

    s = s.replace('content="v109-mobile-swipe-reveal"', 'content="v110-blank-screen-fix"', 1)
    s = s.replace('const APP_VERSION = "v109-mobile-swipe-reveal";', 'const APP_VERSION = "v110-blank-screen-fix";', 1)

    if '<style>html{color-scheme:dark}' not in s:
        s = s.replace(
            '<style>html,body{margin:0;min-height:100%;background:#050505;color:#fff}',
            '<style>html{color-scheme:dark}html,body{margin:0;min-height:100%;background:#050505;color:#fff}',
            1,
        )

    if 'window.LA_REACT_BOOT_STARTED=false;' not in s:
        s = s.replace(
            'window.LA_APP_RENDERED=false;',
            'window.LA_APP_RENDERED=false;\n  window.LA_REACT_BOOT_STARTED=false;',
            1,
        )

    s = s.replace(
        'if(root && !window.LA_APP_RENDERED){',
        'if(root && !window.LA_APP_RENDERED && !window.LA_REACT_BOOT_STARTED){',
    )
    s = s.replace(
        'if(root && !window.LA_APP_RENDERED && !root.textContent.trim()){',
        'if(root && !window.LA_APP_RENDERED && !window.LA_REACT_BOOT_STARTED && !root.textContent.trim()){',
    )
    s = s.replace(
        "if(!window.LA_APP_RENDERED && (!root || !root.textContent.trim())) {",
        "if(!window.LA_APP_RENDERED && !window.LA_REACT_BOOT_STARTED && (!root || !root.textContent.trim())) {",
    )

    old = """    try {\n        rootEl.innerHTML = '';\n        ReactDOM.createRoot(rootEl).render(React.createElement(AppErrorBoundary, null, React.createElement(App, null)));"""
    new = """    try {\n        window.LA_REACT_BOOT_STARTED = true;\n        rootEl.innerHTML = '';\n        ReactDOM.createRoot(rootEl).render(React.createElement(AppErrorBoundary, null, React.createElement(App, null)));"""
    if old in s:
        s = s.replace(old, new, 1)
    elif 'window.LA_REACT_BOOT_STARTED = true;' not in s:
        raise RuntimeError('No se encontró el arranque React esperado')

    p.write_text(s, encoding='utf-8')


def patch_bookings():
    p = Path('contrataciones.html')
    s = p.read_text(encoding='utf-8')

    if '<meta name="color-scheme" content="dark" />' not in s:
        s = s.replace(
            '<meta name="theme-color" content="#050505" />',
            '<meta name="theme-color" content="#050505" />\n  <meta name="color-scheme" content="dark" />',
            1,
        )

    if 'html{color-scheme:dark;background:#050505}' not in s:
        s = s.replace(
            ':root{--bg:#050505;',
            'html{color-scheme:dark;background:#050505}:root{--bg:#050505;',
            1,
        )

    boot_css = '''
    .booking-boot{min-height:100vh;display:grid;place-items:center;padding:24px;background:radial-gradient(circle at 50% 12%,rgba(37,99,235,.20),transparent 32%),#050505;color:#fff}
    .booking-boot-card{width:min(430px,100%);padding:24px;border-radius:24px;border:1px solid rgba(255,255,255,.10);background:linear-gradient(145deg,rgba(17,24,39,.94),rgba(5,7,11,.98));box-shadow:0 24px 70px rgba(0,0,0,.38);text-align:center}
    .booking-boot-card img{width:64px;height:64px;object-fit:contain;margin-bottom:13px}.booking-boot-card b{display:block;font-size:18px}.booking-boot-card p{margin:7px 0 0;color:#9ca3af;font-size:12px;line-height:1.5}
    .booking-boot-dot{width:9px;height:9px;border-radius:999px;background:#38bdf8;margin:16px auto 0;box-shadow:0 0 0 6px rgba(56,189,248,.12);animation:bookingBootPulse 1.1s ease-in-out infinite}@keyframes bookingBootPulse{50%{transform:scale(1.35);opacity:.7}}
'''
    if '.booking-boot{' not in s:
        s = s.replace('</style>', boot_css + '\n  </style>', 1)

    shell = '<div id="app"><div class="booking-boot"><div class="booking-boot-card"><img src="./brand-logo.png?v=105" alt="lucasabraham.ph"><b>Cargando contrataciones</b><p>Preparando agenda, equipos y categorías…</p><div class="booking-boot-dot"></div></div></div></div>'
    s = s.replace('<div id="app"></div>', shell, 1)

    old_init = "async function initFirebase(){try{firebase.initializeApp(FIREBASE_CONFIG);if(firebase.auth&&!firebase.auth().currentUser)await firebase.auth().signInAnonymously().catch(()=>null);db=firebase.firestore();try{db.settings({ignoreUndefinedProperties:true})}catch(e){}return true}catch(e){console.error(e);return false}}"
    new_init = "async function initFirebase(){try{if(typeof firebase==='undefined')return false;firebase.initializeApp(FIREBASE_CONFIG);if(firebase.auth&&!firebase.auth().currentUser){await Promise.race([firebase.auth().signInAnonymously().catch(()=>null),new Promise(resolve=>setTimeout(resolve,4500))])}db=firebase.firestore();try{db.settings({ignoreUndefinedProperties:true})}catch(e){}return true}catch(e){console.error(e);return false}}"
    if old_init in s:
        s = s.replace(old_init, new_init, 1)
    elif 'Promise.race([firebase.auth().signInAnonymously()' not in s:
        raise RuntimeError('No se encontró initFirebase esperado')

    old_end = "location.hash='#/admin';adminPage()}\nboot();"
    new_end = """location.hash='#/admin';adminPage()}
setTimeout(()=>{const app=$('#app');if(app&&app.querySelector('.booking-boot')){app.innerHTML=appShell('<div class=\"card success\"><h2 style=\"margin-top:0\">La carga está demorando</h2><p class=\"copy\">No vamos a dejarte una pantalla vacía. Podés reintentar ahora.</p><button class=\"btn primary\" onclick=\"location.reload()\" style=\"margin-top:14px\">Reintentar</button></div>')}},9000);
boot().catch(err=>{console.error(err);const app=$('#app');if(app)app.innerHTML=appShell('<div class=\"card success\"><h2 style=\"margin-top:0\">No se pudo iniciar</h2><p class=\"copy\">Hubo un problema de carga. Reintentá para volver a conectar.</p><button class=\"btn primary\" onclick=\"location.reload()\" style=\"margin-top:14px\">Reintentar</button></div>')});"""
    if old_end in s:
        s = s.replace(old_end, new_end, 1)
    elif 'No vamos a dejarte una pantalla vacía' not in s:
        raise RuntimeError('No se encontró boot() final esperado')

    p.write_text(s, encoding='utf-8')


patch_index()
patch_bookings()
print('v110 startup hardening applied')
