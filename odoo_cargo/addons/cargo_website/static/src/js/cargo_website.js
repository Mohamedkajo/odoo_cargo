/* ============================================================
   Cargo Website — JavaScript helpers
   Runs after DOM ready. Alpine.js handles most interactivity;
   this file adds countdown timers and misc enhancements.
   ============================================================ */

(function () {
  'use strict';

  // ── Countdown timers ─────────────────────────────────────────────────────
  function updateCountdowns() {
    document.querySelectorAll('[data-countdown]').forEach(function (el) {
      var endIso = el.getAttribute('data-countdown');
      if (!endIso) return;
      var end  = new Date(endIso).getTime();
      var now  = Date.now();
      var diff = end - now;
      if (diff <= 0) {
        el.textContent = 'Ended';
        return;
      }
      var d = Math.floor(diff / 86400000);
      var h = Math.floor((diff % 86400000) / 3600000);
      var m = Math.floor((diff % 3600000) / 60000);
      if (d > 0)      el.textContent = d + 'd ' + h + 'h remaining';
      else if (h > 0) el.textContent = h + 'h ' + m + 'm remaining';
      else            el.textContent = m + 'm remaining';
    });
  }

  // ── Marketplace / blog client-side search redirect ───────────────────────
  function bindSearchForms() {
    document.querySelectorAll('[data-search-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var input = form.querySelector('input[type="search"], input[name="search"]');
        if (!input) return;
        var base = form.getAttribute('action') || window.location.pathname;
        var q    = encodeURIComponent(input.value.trim());
        window.location.href = base + (q ? '?search=' + q : '');
      });
    });
  }

  // ── Active nav link highlight ─────────────────────────────────────────────
  function highlightNav() {
    var path = window.location.pathname;
    document.querySelectorAll('nav a[href]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (href === '/' ? path === '/' : (href !== '/' && path.startsWith(href))) {
        a.classList.add('nav-active');
        a.classList.remove('text-gray-500');
        a.classList.add('text-primary');
      }
    });
  }

  // ── Init ─────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    highlightNav();
    bindSearchForms();
    updateCountdowns();
    if (document.querySelector('[data-countdown]')) {
      setInterval(updateCountdowns, 60000); // refresh every minute
    }
  });
})();
