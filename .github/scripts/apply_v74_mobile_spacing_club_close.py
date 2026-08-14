from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')
if 'v74-mobile-spacing-club-close' in s:
    print('already applied'); raise SystemExit(0)
s,n=re.subn(r'<meta name="app-version" content="[^"]+"\s*/>','<meta name="app-version" content="v74-mobile-spacing-club-close" />',s,count=1)
if n!=1: raise SystemExit('version anchor missing')
css='''\n<style id="v74-mobile-spacing-club-close">\n@media(max-width:768px){\n  .la-insta-topbar + header{margin-top:0!important;padding-top:76px!important}\n  .la-insta-topbar{top:0!important}\n}\n.club-modal-close{position:absolute;top:12px;right:12px;z-index:50;width:40px;height:40px;border-radius:999px;border:1px solid rgba(255,255,255,.14);background:rgba(15,15,18,.88);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,0,0,.35);backdrop-filter:blur(12px)}\n.club-modal-close:active{transform:scale(.96)}\n</style>\n'''
s=s.replace('</head>',css+'</head>',1)
old='React.createElement("div", { className: "max-w-6xl mx-auto px-4 py-8" },'
new='React.createElement("div", { className: "max-w-6xl mx-auto px-4 pt-0 pb-8" },'
if old not in s: raise SystemExit('main container anchor missing')
s=s.replace(old,new,1)
old='React.createElement("header", { className: "max-w-5xl mx-auto pt-2 sm:pt-4 pb-4 px-0" },'
new='React.createElement("header", { className: "max-w-5xl mx-auto pt-0 sm:pt-4 pb-4 px-0" },'
if old not in s: raise SystemExit('header anchor missing')
s=s.replace(old,new,1)
old='''        clubModalOpen && React.createElement(Modal, { onClose:closeClub, max:"max-w-2xl" },\n            React.createElement("div", { className:"club-modal-shell" },'''
new='''        clubModalOpen && React.createElement(Modal, { onClose:closeClub, max:"max-w-2xl" },\n            React.createElement("div", { className:"club-modal-shell relative" },\n                React.createElement("button", { type:"button", onClick:closeClub, className:"club-modal-close", "aria-label":"Cerrar Club de beneficios", title:"Cerrar" }, React.createElement("i", { className:"fas fa-xmark" })),'''
if old not in s: raise SystemExit('club modal anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('v74 applied')
