from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s = s.replace('content="v106-team-logo-source"', 'content="v109-mobile-swipe-reveal"')
s = s.replace('const APP_VERSION = "v106-team-logo-source";', 'const APP_VERSION = "v109-mobile-swipe-reveal";')

old = """    const handleAlbumCardTap = (event, album) => {
        if (!album)
            return;
        if (isMobileLike() && mobileRevealedAlbumId !== album.id) {
            event && event.preventDefault && event.preventDefault();
            event && event.stopPropagation && event.stopPropagation();
            setMobileRevealedAlbumId(album.id);
            return;
        }
        const firstSubAlbumId = (((album.subalbums || [])[0] || {}).id) || '';
        setMobileRevealedAlbumId('');
        location.hash = albumHash(album.id, firstSubAlbumId);
        window.scrollTo(0, 0);
    };"""
new = """    useEffect(() => {
        if (!isMobileLike()) return;
        let lastId = '';
        const revealAtTouch = (touch) => {
            if (!touch) return;
            const target = document.elementFromPoint(touch.clientX, touch.clientY);
            const albumButton = target && target.closest ? target.closest('[data-album-card-id]') : null;
            if (!albumButton) return;
            const albumId = albumButton.getAttribute('data-album-card-id') || '';
            if (!albumId || albumId === lastId) return;
            lastId = albumId;
            setMobileRevealedAlbumId(albumId);
        };
        const onTouchStart = (event) => revealAtTouch(event.touches && event.touches[0]);
        const onTouchMove = (event) => revealAtTouch(event.touches && event.touches[0]);
        document.addEventListener('touchstart', onTouchStart, { passive: true });
        document.addEventListener('touchmove', onTouchMove, { passive: true });
        return () => {
            document.removeEventListener('touchstart', onTouchStart);
            document.removeEventListener('touchmove', onTouchMove);
        };
    }, []);
    const handleAlbumCardTap = (event, album) => {
        if (!album)
            return;
        // La carátula ya se revela al rozar/deslizar el dedo; el toque queda para entrar al álbum.
        const firstSubAlbumId = (((album.subalbums || [])[0] || {}).id) || '';
        setMobileRevealedAlbumId('');
        location.hash = albumHash(album.id, firstSubAlbumId);
        window.scrollTo(0, 0);
    };"""
if old not in s:
    if 'v109-mobile-swipe-reveal' not in s:
        raise SystemExit('No se encontró el bloque handleAlbumCardTap esperado')
else:
    s = s.replace(old, new, 1)

needle = 'React.createElement("button", { key: a.id, onClick: e => handleAlbumCardTap(e, a), className: "group text-left active:scale-[0.98] focus:outline-none", "aria-pressed": mobileRevealedAlbumId === a.id }'
repl = 'React.createElement("button", { key: a.id, "data-album-card-id": a.id, onClick: e => handleAlbumCardTap(e, a), className: "group text-left active:scale-[0.98] focus:outline-none", "aria-pressed": mobileRevealedAlbumId === a.id }'
count = s.count(needle)
if count:
    if count != 2:
        raise SystemExit(f'Se esperaban 2 tarjetas de álbum y se encontraron {count}')
    s = s.replace(needle, repl)
elif s.count('"data-album-card-id": a.id') < 2:
    raise SystemExit('No se encontraron las tarjetas ya modificadas')

marker = '    /* v43: duelo con miras blancas + nombres centrados */'
css = """    /* v109: en táctil la carátula se revela mientras el dedo pasa por los álbumes */
    @media(hover:none),(pointer:coarse){
      .modern-album-card{touch-action:pan-y}
    }

"""
if css not in s:
    if marker not in s:
        raise SystemExit('No se encontró el marcador CSS')
    s = s.replace(marker, css + marker, 1)

p.write_text(s, encoding='utf-8')
