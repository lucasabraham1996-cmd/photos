/* Atajo visual reservado para el administrador.
   No autentica, no guarda credenciales y no concede permisos. */
(function () {
  'use strict';
  function syncRouteTheme() {
    document.documentElement.setAttribute(
      'data-la-route',
      String(window.location.hash || '').startsWith('#/admin') ? 'admin' : 'public'
    );
  }
  syncRouteTheme();
  window.addEventListener('hashchange', syncRouteTheme);
  const MAX_INTERVAL_MS = 3000;
  const REQUIRED_TAPS = 5;
  let taps = 0;
  let lastAt = 0;

  document.addEventListener('click', function (event) {
    if (String(window.location.hash || '').startsWith('#/admin')) return;
    if (!(event.target instanceof Element)) return;
    // El propio logo conserva su función de volver a la galería en los primeros toques.
    const logo = event.target.closest('.la-insta-logo.la-home-logo-btn, .profile-home-btn, .la-home-logo-btn');
    if (!logo || !document.getElementById('root') || !document.getElementById('root').contains(logo)) return;
    // Ignorar clics sintéticos sin interacción real.
    if (event.isTrusted === false) return;

    const now = Date.now();
    taps = now - lastAt <= MAX_INTERVAL_MS ? taps + 1 : 1;
    lastAt = now;
    if (taps < REQUIRED_TAPS) return;

    taps = 0;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    // Es únicamente una ruta al login existente: Face ID, huella o PIN siguen siendo obligatorios.
    window.location.hash = '#/admin';
    syncRouteTheme();
  }, true);
})();