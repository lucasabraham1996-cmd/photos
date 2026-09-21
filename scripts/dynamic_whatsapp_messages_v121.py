from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v121-whatsapp-dynamic-messages'
s = re.sub(r'<meta name="app-version" content="[^"]*"\s*/?>', f'<meta name="app-version" content="{VERSION}" />', s, count=1)

new_block = r'''    function cleanWhatsappPersonName(value) {
        return String(value || '').trim().replace(/\s+/g, ' ');
    }
    function whatsappFirstName(value) {
        const clean = cleanWhatsappPersonName(value);
        return clean ? clean.split(/\s+/)[0] : '';
    }
    function selectedOrderPlayerName(photos) {
        const names = [...new Set((Array.isArray(photos) ? photos : []).map(photo =>
            cleanWhatsappPersonName(
                photo && (photo.playerName || photo.nombreJugador || photo.player || photo.jugadorNombre || '')
            )
        ).filter(Boolean))];
        return names.length === 1 ? names[0] : '';
    }
    function buildOrderSelectionWhatsappMessage({ photos, total, playerName = '' }) {
        const currentPhotos = Array.isArray(photos) ? photos : [];
        const quantity = currentPhotos.length;
        const quantityLabel = quantity === 1 ? '1 foto' : `${quantity} fotos`;
        const cleanPlayer = cleanWhatsappPersonName(playerName);
        const intro = cleanPlayer
            ? `👋 ¡Buenas Lucas! Seleccioné estas fotos de ${cleanPlayer} 📸⚽`
            : '👋 ¡Buenas Lucas! Seleccioné estas fotos 📸⚽';
        const photoLines = currentPhotos.map((photo, index) => {
            const fileName = String((photo && (photo.name || photo.filename || photo.fileName)) || '').trim() || `Foto ${index + 1}`;
            return `📷 ${fileName}`;
        }).join('\n\n');
        return `${intro}

${photoLines}

📸 *${quantityLabel}*

💰 *Total: ${formatPrice(total)}*

━━━━━━━━━━━━━

💳 *DATOS PARA TRANSFERIR*

🔑 *ALIAS: ${MP_ALIAS}*

👤 *Lucas Abraham*

━━━━━━━━━━━━━

Cuando haga la transferencia te mando el comprobante por acá 🙌`;
    }
    function buildOrderConfirmationMessage(orderLike = {}) {
        const customerName = cleanWhatsappPersonName(orderLike.customerName || orderLike.nombreCliente || orderLike.nombreApellido || '');
        const firstName = whatsappFirstName(customerName);
        const greeting = firstName ? `👋 ¡Buenas, ${firstName}! ¿Cómo estás?` : '👋 ¡Buenas! ¿Cómo estás?';
        return `${greeting}

¡Listo! Ya recibí tu selección de fotos 📸⚽

En breve te las preparo y te las envío por acá 😊

¡Muchas gracias por elegirme y por bancar mi trabajo! 🙌

📸 *lucasabraham.ph*`;
    }
    function orderConfirmationWhatsappUrl(orderLike) {
        const phone = normalizeClubPhone(orderLike && (orderLike.phone || orderLike.celular || orderLike.customerPhone));
        if (!phone) return '';
        const message = String((orderLike && orderLike.confirmationMessage) || buildOrderConfirmationMessage(orderLike || {}));
        return `https://api.whatsapp.com/send?phone=549${phone}&text=${encodeURIComponent(message)}`;
    }

    const buildOrderPackage = (forcedOrder) => {
        const order = forcedOrder || checkoutOrderCode || ('LA-' + Math.floor(10000 + Math.random() * 90000));
        const cleanPhone = checkoutWantsPoints && customerDetailsSaved ? normalizeClubPhone(checkoutPhone) : '';
        const cleanCustomerName = cleanPhone ? cleanWhatsappPersonName(checkoutCustomerName) : '';
        const playerName = selectedOrderPlayerName(selectedPhotos);

        // Se genera en el momento de enviar usando exclusivamente la selección y el total actuales.
        // No se conserva un texto previo, por lo que cualquier cambio en el carrito se refleja al instante.
        const msg = buildOrderSelectionWhatsappMessage({
            photos: selectedPhotos,
            total: checkoutTotal,
            playerName
        });
        const confirmationMessage = buildOrderConfirmationMessage({ customerName: cleanCustomerName });

        const orderData = {
            id: order,
            date: new Date().toISOString(),
            subtotal: regular,
            discount: effectiveDiscountPercent,
            coupon: appliedCoupon ? { code: appliedCoupon.code, percent: appliedCoupon.percent } : null,
            total: checkoutTotal,
            digitalTotal: checkoutDigitalTotal,
            customerName: cleanCustomerName,
            dni: '',
            phone: cleanPhone,
            wantsPoints: Boolean(cleanPhone),
            confirmationMessage,
            messageVersion: 2,
            printRequested: printSelectedPhotos.length > 0,
            printFormat: '10x15 cm',
            printCount: printSelectedPhotos.length,
            printedPhotoIds: printSelectedPhotos.map(p => p.id),
            printedItems: printSelectedPhotos.map(p => ({ id:p.id, albumName:p.albumName, name:p.name, code:p.code })),
            printSurchargePerPhoto: PRINT_SURCHARGE_PER_PHOTO,
            printSurcharge,
            items: selectedPhotos.map(p => ({ id: p.id, albumName: p.albumName, subAlbumName: p.subAlbumName || '', name: p.name, code: p.code, url: p.url, driveLink: p.rawUrl || p.fullUrl || p.url, price: p.price, printRequested: printedPhotoIds.includes(p.id) })),
            delivered: false,
            status: 'pendiente'
        };
        const whatsappUrl = `https://api.whatsapp.com/send?phone=${SELLER_PHONE}&text=${encodeURIComponent(msg)}`;
        return { order, msg, confirmationMessage, orderData, whatsappUrl };
    };
    const currentWhatsappHref = () => {'''

pattern = re.compile(r'    const buildOrderPackage = \(forcedOrder\) => \{.*?\n    \};\n    const currentWhatsappHref = \(\) => \{', re.S)
s, count = pattern.subn(new_block, s, count=1)
if count != 1:
    raise SystemExit(f'buildOrderPackage replacement count: {count}')

old_button = '''                            React.createElement("button", { onClick: () => { navigator.clipboard.writeText(buildDeliveryLinksMessage(matchedOrder)); setAdminMessage('Mensaje con links copiado.'); }, className: "bg-white text-black px-4 py-3 rounded-xl font-black text-sm" },
                                React.createElement("i", { className: "fas fa-copy mr-2" }),
                                "Copiar mensaje con links"))),'''

new_buttons = '''                            React.createElement("button", { onClick: () => { navigator.clipboard.writeText(buildDeliveryLinksMessage(matchedOrder)); setAdminMessage('Mensaje con links copiado.'); }, className: "bg-white text-black px-4 py-3 rounded-xl font-black text-sm" },
                                React.createElement("i", { className: "fas fa-copy mr-2" }),
                                "Copiar mensaje con links"),
                            React.createElement("button", { onClick: () => { const confirmation = String(matchedOrder.confirmationMessage || buildOrderConfirmationMessage(matchedOrder)); navigator.clipboard.writeText(confirmation).then(() => setAdminMessage('Confirmación copiada.')).catch(() => setAdminMessage('No se pudo copiar la confirmación.')); }, className: "bg-sky-500 text-black px-4 py-3 rounded-xl font-black text-sm" },
                                React.createElement("i", { className: "fas fa-message mr-2" }),
                                "Copiar confirmación"),
                            orderConfirmationWhatsappUrl(matchedOrder) && React.createElement("button", { onClick: () => window.open(orderConfirmationWhatsappUrl(matchedOrder), '_blank'), className: "bg-[#25D366] text-black px-4 py-3 rounded-xl font-black text-sm" },
                                React.createElement("i", { className: "fab fa-whatsapp mr-2" }),
                                "Enviar confirmación"))),'''

if old_button not in s:
    raise SystemExit('admin delivery button anchor not found')
s = s.replace(old_button, new_buttons, 1)

p.write_text(s, encoding='utf-8')
