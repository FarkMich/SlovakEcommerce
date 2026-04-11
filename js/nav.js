/* nav.js — scroll animations + active-link marker.
   Nav + footer sú statické v HTML (pozri scripts/inline_nav.py). */
(function () {
  var obs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.querySelectorAll('.bar-fill[data-w]').forEach(function (b, i) {
        setTimeout(function () { b.style.width = b.getAttribute('data-w') + '%'; }, i * 60);
      });
      e.target.querySelectorAll('.bw-bar-fill[data-w]').forEach(function (b, i) {
        setTimeout(function () { b.style.width = b.getAttribute('data-w') + '%'; }, i * 70);
      });
      e.target.querySelectorAll('.ec-bar-fill[data-target]').forEach(function (b, i) {
        setTimeout(function () { b.style.width = b.getAttribute('data-target') + '%'; }, i * 60);
      });
      obs.unobserve(e.target);
    });
  }, { threshold: 0.15 });

  function init() {
    document.querySelectorAll('.bar-chart, .bw-widget, #eu-comparison-widget, .ec-live-section').forEach(function (el) {
      obs.observe(el);
    });

    var cardObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.style.opacity = '1';
          e.target.style.transform = 'translateY(0)';
        }
      });
    }, { threshold: 0.08 });

    document.querySelectorAll('.card, .vyzva-card, .kpi-item').forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(16px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      cardObs.observe(el);
    });

    /* mark active nav link */
    var path = window.location.pathname;
    document.querySelectorAll('nav .nav-links a').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href) return;
      var base = href.split('/').pop();
      if (base && path.endsWith(base)) a.classList.add('active');
      if (href === '/' && (path === '/' || path === '/index.html')) a.classList.add('active');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
