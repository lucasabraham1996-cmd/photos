from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1, got {n}')
    s=s.replace(old,new,1)

s=s.replace('v89-club-blue-login','v91-ranking-cart-recovery-ui',1)

# Cart recovery + ranking expansion state.
once('''    const [cart, setCart] = useState([]);''','''    const [cart, setCart] = useState([]);
    const [cartRecovery, setCartRecovery] = useState(() => { try { const v=JSON.parse(localStorage.getItem('LA_RECOVER_CART') || '[]'); return Array.isArray(v) ? v : []; } catch(e) { return []; } });
    const cartPersistenceReady = useRef(false);
    const [clubRankingAllOpen, setClubRankingAllOpen] = useState(false);''','cart recovery states')

# Persist non-empty cart after first mount, but do not wipe a previous recoverable cart on startup.
marker="""    useEffect(() => { try { localStorage.setItem('LA_ADMIN_RESOLVED_ORDERS', JSON.stringify(adminResolvedIds)); } catch(e) {} }, [adminResolvedIds]);"""
insert=marker+"""
    useEffect(() => {
        if (!cartPersistenceReady.current) { cartPersistenceReady.current = true; return; }
        try {
            if (cart.length) {
                localStorage.setItem('LA_RECOVER_CART', JSON.stringify(cart));
                setCartRecovery(cart);
            } else {
                localStorage.removeItem('LA_RECOVER_CART');
                setCartRecovery([]);
            }
        } catch(e) {}
    }, [cart]);
    const restoreSavedCart = () => {
        const valid = (cartRecovery || []).filter(id => allPhotos.some(p => p.id === id));
        if (!valid.length) {
            try { localStorage.removeItem('LA_RECOVER_CART'); } catch(e) {}
            setCartRecovery([]);
            return;
        }
        setCart(valid);
    };
    const cancelSavedCart = () => {
        try { localStorage.removeItem('LA_RECOVER_CART'); } catch(e) {}
        setCartRecovery([]);
        setCart([]);
    };"""
once(marker,insert,'cart recovery persistence')

# Ranking hides zero-point users and supports top 10 + expand.
needle='''    const ADMIN_HISTORY_RESET_AT = Date.parse('2026-08-16T02:03:00Z');'''
replacement='''    const clubRankingStats = useMemo(() => customerDniStats.filter(r => Number(r.points || 0) > 0), [customerDniStats]);
    const visibleClubRankingStats = clubRankingAllOpen ? clubRankingStats : clubRankingStats.slice(0, 10);
    const ADMIN_HISTORY_RESET_AT = Date.parse('2026-08-16T02:03:00Z');'''
once(needle,replacement,'ranking filtered stats')

old_rank='''                pointsAdminOpen && React.createElement("div", { className:"grid gap-2 mb-4" },
                    React.createElement("div", { className:"flex items-center justify-between px-1 mb-1" }, React.createElement("span", { className:"text-[10px] uppercase tracking-widest text-neutral-500 font-black" }, "Ranking por puntos disponibles"), React.createElement("span", { className:"text-[10px] text-neutral-500" }, `${customerDniStats.length} usuarios`)),
                    customerDniStats.length===0 && React.createElement("p", { className:"text-sm text-neutral-500" }, "Todavía no hay usuarios con teléfono registrado."),
                    customerDniStats.map((r,index)=>React.createElement("div", { key:r.phone, className:`club-ranking-card ${index<3?`top-${index+1}`:''}` },
                        React.createElement("div", { className:"club-ranking-pos" }, index===0?'🥇':index===1?'🥈':index===2?'🥉':`#${index+1}`),
                        React.createElement("div", { className:"min-w-0" }, React.createElement("b", { className:"block text-sm sm:text-base truncate text-white" }, r.name||'Sin nombre'), React.createElement("span", { className:"block text-xs text-neutral-400 mt-0.5" }, r.phone), React.createElement("span", { className:"block text-[10px] text-neutral-500 mt-1" }, `${r.purchases} compras · ${formatPrice(r.spent)} gastados · ${r.redeemedPoints} canjeados`)),
                        React.createElement("div", { className:"club-ranking-points" }, r.points, React.createElement("small", null,"puntos"))))),'''
new_rank='''                pointsAdminOpen && React.createElement("div", { className:"club-ranking-shell mb-4" },
                    React.createElement("div", { className:"club-ranking-titlebar" }, React.createElement("div", null, React.createElement("b", null, "Ranking por puntos disponibles"), React.createElement("span", null, "Sólo aparecen usuarios con saldo mayor a 0")), React.createElement("span", { className:"club-ranking-count" }, `${clubRankingStats.length} usuarios`)),
                    clubRankingStats.length===0 && React.createElement("p", { className:"text-sm text-neutral-500 p-4" }, "Todavía no hay usuarios con puntos disponibles."),
                    clubRankingStats.length>0 && React.createElement("div", { className:"club-ranking-table" },
                        React.createElement("div", { className:"club-ranking-head" }, React.createElement("span", null,"#"),React.createElement("span", null,"Usuario"),React.createElement("span", null,"Actividad"),React.createElement("span", null,"Puntos")),
                        visibleClubRankingStats.map((r,index)=>React.createElement("div", { key:r.phone, className:`club-ranking-card ${index<3?`top-${index+1}`:''}` },
                            React.createElement("div", { className:"club-ranking-pos" }, index===0?'🥇':index===1?'🥈':index===2?'🥉':`#${index+1}`),
                            React.createElement("div", { className:"club-ranking-user min-w-0" }, React.createElement("b", null, r.name||'Sin nombre'), React.createElement("span", null, r.phone)),
                            React.createElement("div", { className:"club-ranking-activity" }, React.createElement("b", null, `${r.purchases} compra${r.purchases===1?'':'s'}`), React.createElement("span", null, `${formatPrice(r.spent)} · ${r.redeemedPoints} canjeados`)),
                            React.createElement("div", { className:"club-ranking-points" }, r.points, React.createElement("small", null,"pts"))))),
                    clubRankingStats.length>10 && React.createElement("button", { type:"button", onClick:()=>setClubRankingAllOpen(v=>!v), className:"club-ranking-more" }, clubRankingAllOpen ? React.createElement(React.Fragment,null,"Ver sólo top 10 ",React.createElement("i",{className:"fas fa-chevron-up"})) : React.createElement(React.Fragment,null,`Ver ${clubRankingStats.length-10} más `,React.createElement("i",{className:"fas fa-chevron-down"})))),'''
once(old_rank,new_rank,'ranking render')

# Preview can always be closed without resolving the order.
once('''                matchedOrder && React.createElement("div", { className: "mt-5 bg-black/35 border border-neutral-800 rounded-2xl p-4" },''','''                matchedOrder && React.createElement("div", { className: "mt-5 bg-black/35 border border-neutral-800 rounded-2xl p-4 relative" },
                    React.createElement("button", { type:"button", onClick:clearOrderBox, className:"order-preview-close", title:"Cerrar vista previa", "aria-label":"Cerrar vista previa" }, React.createElement("i", { className:"fas fa-xmark" })),''','order preview close')

# Recovery controls appear only after a restart / lost session when there is a saved cart but current cart is empty.
anchor='''        cart.length > 0 && !checkoutOpen && React.createElement("button", { onClick: openCheckout, className: "mobile-buy-shortcut" },'''
recovery='''        cart.length === 0 && cartRecovery.length > 0 && React.createElement("div", { className:"cart-recovery-bar up" },
            React.createElement("button", { type:"button", onClick:restoreSavedCart, className:"cart-restore-btn" }, React.createElement("i", { className:"fas fa-rotate-left" }), " Restaurar carrito"),
            React.createElement("button", { type:"button", onClick:cancelSavedCart, className:"cart-cancel-btn" }, React.createElement("i", { className:"fas fa-xmark" }), " Cancelar carrito")),
'''+anchor
once(anchor,recovery,'cart recovery bar')

# Explicit marker/documentation: selection is deliberately unlimited. No slice/cap is applied to cart.
once('''    const toggle = (id) => {
        const removing = cart.includes(id);''','''    // CARRITO_SIN_LIMITE: la selección de fotos no tiene máximo de unidades.
    const toggle = (id) => {
        const removing = cart.includes(id);''','unlimited cart marker')

# Final CSS overrides for ranking, desktop categories, recovery bar, close preview.
style='''
<style id="v91-ranking-cart-recovery-ui">
.club-ranking-shell{border:1px solid rgba(56,189,248,.16);border-radius:20px;overflow:hidden;background:linear-gradient(145deg,rgba(3,7,18,.78),rgba(10,10,12,.94));box-shadow:0 16px 38px rgba(0,0,0,.22)}
.club-ranking-titlebar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 14px;border-bottom:1px solid rgba(255,255,255,.07);background:rgba(56,189,248,.045)}
.club-ranking-titlebar b{display:block;font-size:12px;color:#e0f2fe}.club-ranking-titlebar span{display:block;font-size:9px;color:#64748b;margin-top:2px}.club-ranking-count{margin:0!important;padding:6px 9px;border-radius:999px;background:rgba(56,189,248,.10);border:1px solid rgba(125,211,252,.14);color:#bae6fd!important;font-weight:900;white-space:nowrap}
.club-ranking-table{display:grid}.club-ranking-head,.club-ranking-card{display:grid;grid-template-columns:52px minmax(150px,1.2fr) minmax(170px,1fr) 84px;align-items:center;gap:12px}.club-ranking-head{padding:8px 13px;color:#64748b;font-size:8px;text-transform:uppercase;letter-spacing:.12em;font-weight:900;border-bottom:1px solid rgba(255,255,255,.055)}
.club-ranking-card{margin:0!important;padding:11px 13px!important;border:0!important;border-bottom:1px solid rgba(255,255,255,.055)!important;border-radius:0!important;background:transparent!important;box-shadow:none!important}.club-ranking-card:last-child{border-bottom:0!important}.club-ranking-card.top-1{background:linear-gradient(90deg,rgba(250,204,21,.09),transparent 42%)!important}.club-ranking-card.top-2{background:linear-gradient(90deg,rgba(203,213,225,.07),transparent 42%)!important}.club-ranking-card.top-3{background:linear-gradient(90deg,rgba(251,146,60,.07),transparent 42%)!important}
.club-ranking-pos{width:38px!important;height:38px!important;border-radius:12px!important;display:flex!important;align-items:center!important;justify-content:center!important;background:rgba(255,255,255,.045)!important;border:1px solid rgba(255,255,255,.07)!important;font-size:14px!important}.club-ranking-user b,.club-ranking-activity b{display:block;color:#fff;font-size:11px}.club-ranking-user span,.club-ranking-activity span{display:block;color:#737373;font-size:9px;margin-top:2px}.club-ranking-points{justify-self:end!important;min-width:62px!important;padding:7px 8px!important;border-radius:13px!important;background:rgba(14,165,233,.10)!important;border:1px solid rgba(125,211,252,.16)!important;color:#7dd3fc!important;font-size:19px!important;line-height:.9!important;text-align:center!important}.club-ranking-points small{display:block!important;font-size:7px!important;text-transform:uppercase!important;letter-spacing:.1em!important;margin-top:4px!important;color:#94a3b8!important}.club-ranking-more{width:100%;border:0;border-top:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.025);color:#bae6fd;padding:11px;font-size:10px;font-weight:900}.club-ranking-more:hover{background:rgba(56,189,248,.07)}
.order-preview-close{position:absolute;right:11px;top:11px;width:34px;height:34px;border-radius:50%;border:1px solid rgba(255,255,255,.10);background:#171717;color:#a3a3a3;display:flex;align-items:center;justify-content:center;z-index:4}.order-preview-close:hover{color:#fff;background:#262626}
.cart-recovery-bar{position:fixed;left:50%;bottom:max(14px,env(safe-area-inset-bottom));transform:translateX(-50%);z-index:75;width:min(94vw,520px);display:grid;grid-template-columns:1.15fr .85fr;gap:8px;padding:8px;border-radius:20px;background:rgba(8,8,10,.96);border:1px solid rgba(255,255,255,.10);box-shadow:0 18px 50px rgba(0,0,0,.48)}.cart-recovery-bar button{min-height:46px;border-radius:14px;font-weight:900;font-size:11px}.cart-restore-btn{border:1px solid rgba(248,113,113,.34);background:linear-gradient(135deg,#7f1d1d,#dc2626 58%,#ef4444);color:#fff;box-shadow:0 9px 22px rgba(220,38,38,.22)}.cart-cancel-btn{border:1px solid rgba(255,255,255,.09);background:#171717;color:#a3a3a3}
@media(min-width:769px){.subalbum-panel{padding:16px 18px!important}.subalbum-showcase{justify-content:center!important;gap:14px!important;overflow-x:visible!important;padding:4px 0 6px!important}.subalbum-visual-card{min-width:190px!important;height:68px!important;padding:0 24px!important;border-radius:20px!important}.subalbum-visual-card::before{display:none!important}.subalbum-copy-wrap{width:100%!important;justify-content:center!important}.subalbum-copy-title{width:100%!important;text-align:center!important;font-size:14px!important;letter-spacing:.055em!important;padding:0!important}.subalbum-visual-card::after{content:""!important;display:block!important;position:absolute!important;left:50%!important;right:auto!important;top:auto!important;bottom:11px!important;width:24px!important;height:2px!important;transform:translateX(-50%)!important;border-radius:99px!important;background:rgba(148,163,184,.38)!important;box-shadow:none!important;opacity:1!important;font-size:0!important}.subalbum-visual-card.active::after{width:44px!important;background:#7dd3fc!important;box-shadow:0 0 12px rgba(125,211,252,.55)!important}}
@media(max-width:640px){.club-ranking-head{display:none}.club-ranking-card{grid-template-columns:40px minmax(0,1fr) 62px!important;gap:9px!important;padding:10px!important}.club-ranking-activity{grid-column:2/4;margin-top:-3px}.club-ranking-points{grid-column:3;grid-row:1}.club-ranking-titlebar{align-items:flex-start}.cart-recovery-bar{grid-template-columns:1fr 1fr;width:calc(100vw - 18px);bottom:max(8px,env(safe-area-inset-bottom))}.cart-recovery-bar button{font-size:10px;padding:0 7px}}
</style>
'''
if '</head>' not in s: raise SystemExit('missing </head>')
s=s.replace('</head>',style+'</head>',1)

p.write_text(s,encoding='utf-8')
print('v91 patched')
