from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
if 'v70-mobile-checkout' in s:
    print('already applied')
    raise SystemExit(0)

s=re.sub(r'<meta name="app-version" content="[^"]+"\s*/>', '<meta name="app-version" content="v70-mobile-checkout" />', s, count=1)

old='''@media(max-width:768px),(hover:none),(pointer:coarse){
 .la-insta-topbar{position:-webkit-sticky!important;position:sticky!important;top:max(0px,env(safe-area-inset-top))!important;z-index:999!important;transform:translateZ(0)!important}
 .subalbum-panel{overflow:visible!important;padding:12px!important;border-radius:22px!important}'''
new='''@media(max-width:768px),(hover:none),(pointer:coarse){
 .la-insta-topbar{position:fixed!important;left:10px!important;right:10px!important;top:max(6px,env(safe-area-inset-top))!important;width:auto!important;z-index:9999!important;transform:translateZ(0)!important;-webkit-transform:translateZ(0)!important;margin:0!important}
 .la-insta-topbar + header{padding-top:76px!important}
 .subalbum-panel{overflow:visible!important;padding:12px!important;border-radius:22px!important}'''
if old not in s: raise SystemExit('header css anchor missing')
s=s.replace(old,new,1)

anchor='.print-order-btn.active{box-shadow:inset 0 1px 0 #fff,0 0 0 3px rgba(59,130,246,.25),0 12px 28px rgba(37,99,235,.2)}\n</style>'
css='''.print-order-btn.active{box-shadow:inset 0 1px 0 #fff,0 0 0 3px rgba(59,130,246,.25),0 12px 28px rgba(37,99,235,.2)}
@media(max-width:640px),(hover:none),(pointer:coarse){
 .checkout-simple-shell{width:100%!important;max-height:calc(100dvh - 18px)!important;overflow-y:auto!important;overscroll-behavior:contain!important;border-radius:20px!important;padding:10px!important;margin:0!important;scrollbar-width:none!important}
 .checkout-simple-shell::-webkit-scrollbar{display:none!important}
 .checkout-simple-shell>div:first-child{margin-bottom:8px!important}
 .checkout-simple-shell>div:first-child>p:first-child{margin-bottom:6px!important;padding:4px 9px!important;font-size:9px!important}
 .checkout-simple-shell>div:first-child h2{font-size:20px!important;line-height:1.05!important;margin-bottom:3px!important}
 .checkout-simple-shell>div:first-child p:last-child{font-size:11px!important;line-height:1.25!important}
 .checkout-simple-card{padding:10px!important;border-radius:15px!important;margin-bottom:8px!important}
 .checkout-simple-total{padding:10px 12px!important;border-radius:15px!important;margin-bottom:8px!important}
 .checkout-simple-total b{font-size:26px!important}
 .checkout-simple-row{padding:3px 0!important;font-size:12px!important}
 .checkout-simple-alias{padding:9px 10px!important;min-height:42px!important}
 .checkout-pay-logo{max-height:24px!important;width:auto!important}
 .benefits-glass-btn,.print-order-btn{padding:10px 11px!important;border-radius:14px!important;gap:9px!important;font-size:12px!important}
 .benefits-glass-btn small,.print-order-btn small{font-size:9px!important;line-height:1.2!important}
 .customer-compact-input{padding:9px 10px!important;font-size:13px!important;border-radius:11px!important}
 .save-customer-btn{padding:9px 11px!important}
 .checkout-simple-coupon summary{font-size:12px!important}
 .checkout-simple-cta{position:sticky!important;bottom:0!important;z-index:3!important;padding:12px!important;border-radius:14px!important;box-shadow:0 -8px 24px rgba(0,0,0,.45)!important}
 .checkout-simple-shell>p:last-child{font-size:9px!important;margin-top:6px!important}
}
</style>'''
if anchor not in s: raise SystemExit('checkout css anchor missing')
s=s.replace(anchor,css,1)

old='''        setCheckoutPrint(false);
        setCustomerDetailsOpen(true);
        setCustomerDetailsSaved(false);'''
new='''        setCheckoutPrint(false);
        setCustomerDetailsOpen(false);
        setCustomerDetailsSaved(false);'''
if old not in s: raise SystemExit('open checkout anchor missing')
s=s.replace(old,new,1)

old='''        setCheckoutCustomerName(name);
        setCheckoutPhone(phone);
        setCheckoutDni(dni);
        setCustomerDetailsSaved(true);'''
new='''        setCheckoutCustomerName(name);
        setCheckoutPhone(phone);
        setCheckoutDni(dni);
        setCheckoutWantsPoints(Boolean(dni));
        setCustomerDetailsSaved(true);'''
if old not in s: raise SystemExit('save customer anchor missing')
s=s.replace(old,new,1)

pattern=r'''                React\.createElement\("div", \{ className: "checkout-simple-card customer-data-card mb-3" \},.*?                React\.createElement\("div", \{ className: "checkout-simple-total mb-3" \},'''
replacement='''                React.createElement("div", { className: "mb-3" },
                    React.createElement("button", { type:"button", onClick:() => setCustomerDetailsOpen(v => !v), className:`benefits-glass-btn ${customerDetailsOpen || customerDetailsSaved ? 'active' : ''}` },
                        React.createElement("i", { className:"fas fa-gift" }),
                        React.createElement("span", null,
                            React.createElement("b", null, customerDetailsSaved ? "Datos guardados para beneficios" : "Quiero sumar puntos para beneficios"),
                            React.createElement("small", null, customerDetailsSaved ? `${checkoutCustomerName} · ${checkoutPhone}${checkoutDni ? ` · DNI ${normalizeDni(checkoutDni)}` : ''}` : "Nombre y apellido · celular · DNI opcional")),
                        React.createElement("i", { className:`fas ${customerDetailsOpen ? 'fa-chevron-up' : customerDetailsSaved ? 'fa-circle-check' : 'fa-chevron-down'}` })),
                    customerDetailsOpen && React.createElement("div", { className:"checkout-simple-card customer-data-card mt-2 mb-0" },
                        React.createElement("div", { className:"grid gap-2" },
                            React.createElement("input", { value:checkoutCustomerName, onChange:e => { setCheckoutCustomerName(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"Nombre y apellido", className:"customer-compact-input" }),
                            React.createElement("input", { value:checkoutPhone, inputMode:"tel", onChange:e => { setCheckoutPhone(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"Celular", className:"customer-compact-input" }),
                            React.createElement("div", null,
                                React.createElement("input", { value:checkoutDni, inputMode:"numeric", onChange:e => { setCheckoutDni(e.target.value); setCustomerDetailsSaved(false); }, placeholder:"DNI (opcional)", className:"customer-compact-input" }),
                                React.createElement("p", { className:"text-[10px] text-amber-200/80 mt-1 px-1 leading-tight" }, "Ingresalo sin puntos. Si escribís puntos, espacios o guiones, se unifica automáticamente.")),
                            React.createElement("button", { type:"button", onClick:saveCheckoutCustomer, className:"save-customer-btn" }, React.createElement("i", { className:"fas fa-floppy-disk mr-2" }), "Guardar datos"),
                            customerSavedMessage && React.createElement("p", { className:"customer-saved-msg" }, customerSavedMessage)))),
                React.createElement("div", { className: "checkout-simple-total mb-3" },'''
s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n != 1: raise SystemExit(f'customer card replacement count {n}')

p.write_text(s,encoding='utf-8')
