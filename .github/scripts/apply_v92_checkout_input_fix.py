from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
s=s.replace('v91-ranking-cart-recovery-ui','v92-checkout-mobile-inputs',1)
old='''                            React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "Usamos tu celular para tu cuenta y tus puntos. 351, 0351, 15, +54 9 y formatos equivalentes se unifican automáticamente."),\n'''
if old not in s: raise SystemExit('checkout technical phone helper not found')
s=s.replace(old,'',1)
style='''\n<style id="v92-checkout-mobile-inputs">\n/* iOS: mantener texto y placeholder perfectamente centrados dentro de los campos del checkout */\n.customer-data-card .customer-compact-input{box-sizing:border-box!important;display:block!important;width:100%!important;height:52px!important;min-height:52px!important;padding:0 14px!important;line-height:52px!important;font-size:16px!important;vertical-align:middle!important;-webkit-appearance:none!important;appearance:none!important}\n.customer-data-card .customer-compact-input::placeholder{line-height:normal!important;opacity:.72}\n.customer-data-card .customer-compact-input:focus{padding-top:0!important;padding-bottom:0!important}\n@media(max-width:640px),(hover:none),(pointer:coarse){\n .customer-data-card .customer-compact-input{height:54px!important;min-height:54px!important;padding:0 14px!important;line-height:54px!important;font-size:16px!important;border-radius:14px!important}\n}\n</style>\n'''
if '</head>' not in s: raise SystemExit('missing head')
s=s.replace('</head>',style+'</head>',1)
p.write_text(s,encoding='utf-8')
print('v92 patched')
