from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

VERSION = 'v119-silent-order-sync'
s = re.sub(r'<meta name="app-version" content="[^"]*"\s*/?>', f'<meta name="app-version" content="{VERSION}" />', s, count=1)

old1 = "setCheckoutSaveError(`El pedido ${fixedCode} quedó guardado en este dispositivo y se sincronizará automáticamente cuando haya conexión disponible.`);"
old2 = "setCheckoutSaveError(`El pedido ${fixedCode} quedó guardado en este dispositivo y pendiente de sincronización.`);"

if old1 not in s:
    raise SystemExit('deferred-sync banner text 1 not found')
if old2 not in s:
    raise SystemExit('deferred-sync banner text 2 not found')

s = s.replace(old1, "setCheckoutSaveError('');", 1)
s = s.replace(old2, "setCheckoutSaveError('');", 1)

p.write_text(s, encoding='utf-8')
