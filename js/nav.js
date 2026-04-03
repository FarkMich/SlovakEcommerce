/* nav.js — injects nav + footer, marks active link, animates bars on scroll */
(function(){
  var PAGES = [
    { href: '/trh.html',       label: 'Trh' },
    { href: '/platformy.html', label: 'Platformy' },
    { href: '/eshopari.html',  label: 'E-shopári' },
    { href: '/doprava.html',   label: 'Doprava & platby' },
    { href: '/sk-vs-eu.html',  label: 'SK vs EÚ' },
  ];

  var LOGO_SVG = '<svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18 2L32 10V26L18 34L4 26V10L18 2Z" fill="rgba(212,165,90,0.10)" stroke="#d4a55a" stroke-width="1.2"/><polyline points="8,25 12,18 17,21 22,13 28,17" fill="none" stroke="#7ec8a0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="18" r="1.6" fill="#7ec8a0"/><circle cx="22" cy="13" r="1.6" fill="#d4a55a"/></svg>';

  var path = window.location.pathname.replace(/\/index\.html$/, '/');
  if (!path.endsWith('/') && !path.includes('.')) path += '/';

  function isActive(href) {
    var base = href.split('/').pop();
    return window.location.pathname.endsWith(base);
  }

  /* ── NAV ── */
  var nav = document.createElement('nav');
  nav.innerHTML =
    '<a href="/index.html" class="logo">' + LOGO_SVG +
    '<div class="logo-text">Slovak<span>e-commerce</span></div></a>' +
    '<ul class="nav-links">' +
    PAGES.map(function(p){
      return '<li><a href="' + p.href + '"' + (isActive(p.href) ? ' class="active"' : '') + '>' + p.label + '</a></li>';
    }).join('') +
    '</ul>' +
    '<a href="mailto:pr@slovakecommerce.sk" class="nav-cta">Spolupráca →</a>';
  document.body.insertBefore(nav, document.body.firstChild);

  /* ── FOOTER ── */
  var footer = document.createElement('footer');
  footer.innerHTML =
    '<div class="footer-top">' +
      '<div>' +
        '<a href="/index.html" class="logo" style="margin-bottom:14px;display:inline-flex;">' + LOGO_SVG +
        '<span class="logo-text" style="font-size:17px;margin-left:12px;">Slovak<span>e-commerce</span></span></a>' +
        '<p class="footer-desc">Komplexný prehľad slovenského e-commerce trhu. Dáta pre e-shopárov, médiá a investorov.</p>' +
        '<a href="mailto:pr@slovakecommerce.sk" class="footer-cta">Spolupráca a médiá →</a>' +
        '<a href="mailto:michal@slovakecommerce.sk" class="footer-cta outline" style="margin-top:6px;">michal@slovakecommerce.sk</a>' +
      '</div>' +
      '<div class="footer-col">' +
        '<h4>Sekcie</h4>' +
        '<ul class="footer-links">' +
        PAGES.map(function(p){ return '<li><a href="' + p.href + '">' + p.label + '</a></li>'; }).join('') +
        '</ul>' +
      '</div>' +
    '</div>' +
    '<div class="footer-bottom">' +
      '<div class="footer-copy">© 2026 Slovak e-commerce · slovakecommerce.sk</div>' +
      '<div class="footer-copy">Dáta: Heureka Group, Shoptet, Levosphere, Packeta, Eurostat, ŠÚ SR</div>' +
    '</div>';
  document.body.appendChild(footer);

  /* ── SCROLL ANIMATIONS ── */
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (!e.isIntersecting) return;
      e.target.querySelectorAll('.bar-fill[data-w]').forEach(function(b, i){
        setTimeout(function(){ b.style.width = b.getAttribute('data-w') + '%'; }, i * 60);
      });
      e.target.querySelectorAll('.bw-bar-fill[data-w]').forEach(function(b, i){
        setTimeout(function(){ b.style.width = b.getAttribute('data-w') + '%'; }, i * 70);
      });
      e.target.querySelectorAll('.ec-bar-fill[data-target]').forEach(function(b, i){
        setTimeout(function(){ b.style.width = b.getAttribute('data-target') + '%'; }, i * 60);
      });
      obs.unobserve(e.target);
    });
  }, { threshold: 0.15 });

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('.bar-chart, .bw-widget, #eu-comparison-widget, .ec-live-section').forEach(function(el){
      obs.observe(el);
    });
    // fade-in cards
    var cardObs = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (e.isIntersecting) { e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)'; }
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.card, .vyzva-card, .kpi-item').forEach(function(el){
      el.style.opacity = '0'; el.style.transform = 'translateY(16px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      cardObs.observe(el);
    });
  });
})();
