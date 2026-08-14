from pathlib import Path
import re
p=Path('index.html')
s=p.read_text(encoding='utf-8')
if 'v75-mobile-tight-club-close' in s:
    print('already applied'); raise SystemExit(0)
s,n=re.subn(r'<meta name="app-version" content="[^"]+"\s*/>','<meta name="app-version" content="v75-mobile-tight-club-close" />',s,count=1)
if n!=1: raise SystemExit('version anchor missing')
css='''\n<style id="v75-mobile-tight-club-close">\n@media(max-width:768px){\n  .la-insta-topbar{position:fixed!important;top:0!important;left:0!important;right:0!important;margin:0!important;z-index:9999!important}\n  .la-profile-header{margin:0!important;padding-top:calc(94px + env(safe-area-inset-top,0px))!important;padding-bottom:16px!important;min-height:0!important}\n  .la-profile-card{margin-top:0!important;transform:none!important}\n}\n.club-global-close{position:fixed!important;top:calc(env(safe-area-inset-top,0px) + 12px)!important;right:12px!important;z-index:2147483647!important;width:44px!important;height:44px!important;border-radius:999px!important;border:1px solid rgba(255,255,255,.28)!important;background:rgba(8,8,10,.96)!important;color:#fff!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:20px!important;box-shadow:0 10px 30px rgba(0,0,0,.55)!important;backdrop-filter:blur(14px)!important;-webkit-backdrop-filter:blur(14px)!important}\n.club-global-close:active{transform:scale(.94)!important}\n</style>\n'''
s=s.replace('</head>',css+'</head>',1)
old='React.createElement("header", { className: "max-w-5xl mx-auto pt-0 sm:pt-4 pb-4 px-0" },'
new='React.createElement("header", { className: "la-profile-header max-w-5xl mx-auto pt-0 sm:pt-4 pb-4 px-0" },'
if old not in s: raise SystemExit('profile header anchor missing')
s=s.replace(old,new,1)
# Remove old close button inside the Club to avoid duplicates/being clipped.
old='''                React.createElement("button", { type:"button", onClick:closeClub, className:"club-modal-close", "aria-label":"Cerrar Club de beneficios", title:"Cerrar" }, React.createElement("i", { className:"fas fa-xmark" })),'''
if old in s:
    s=s.replace(old,'',1)
# Add a close button outside the Modal so no overflow/stacking context can hide it.
anchor='''        clubModalOpen && React.createElement(Modal, { onClose:closeClub, max:"max-w-2xl" },'''
if anchor not in s: raise SystemExit('club modal anchor missing')
replacement='''        clubModalOpen && React.createElement("button", { type:"button", onClick:closeClub, className:"club-global-close", "aria-label":"Cerrar Club de beneficios", title:"Cerrar Club" }, React.createElement("i", { className:"fas fa-xmark" })),\n        clubModalOpen && React.createElement(Modal, { onClose:closeClub, max:"max-w-2xl" },'''
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding='utf-8')
print('v75 applied')
