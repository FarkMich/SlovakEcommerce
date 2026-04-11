/* Eurostat widget — isoc_ec_ib20 porovnanie SK vs EÚ krajiny.
   Požiadavky v HTML:
     <div id="eu-comparison-widget"></div>
     <span id="ec-year"></span>     (optional)
     <span id="ec-source"></span>   (optional)
   Live dáta pullujeme z /data/eurostat.json (updater beží cez GitHub Action /
   scheduled task). Ak fetch zlyhá, padneme na fallback konštanty nižšie. */
(function () {
  'use strict';

  var DATA = {
    year: '2025',
    source: 'Eurostat (isoc_ec_ib20) · Dáta za rok 2025, zverejnené február 2026',
    countries: [
      { code: 'IE', label: 'Írsko',     val: 96, flag: '🇮🇪', sk: false },
      { code: 'NL', label: 'Holandsko', val: 94, flag: '🇳🇱', sk: false },
      { code: 'DK', label: 'Dánsko',    val: 91, flag: '🇩🇰', sk: false },
      { code: 'CZ', label: 'Česko',     val: 87, flag: '🇨🇿', sk: false },
      { code: 'SK', label: 'Slovensko', val: 85, flag: '🇸🇰', sk: true  },
      { code: 'DE', label: 'Nemecko',   val: 82, flag: '🇩🇪', sk: false },
      { code: 'AT', label: 'Rakúsko',   val: 80, flag: '🇦🇹', sk: false },
      { code: 'HU', label: 'Maďarsko',  val: 79, flag: '🇭🇺', sk: false },
      { code: 'PL', label: 'Poľsko',    val: 77, flag: '🇵🇱', sk: false }
    ],
    euAvg: 78
  };

  function tryLoadLive(cb) {
    var r = new XMLHttpRequest();
    r.open('GET', '/data/eurostat.json?t=' + Date.now(), true);
    r.timeout = 3000;
    r.onload = function () {
      if (r.status === 200) {
        try {
          var d = JSON.parse(r.responseText);
          var buyers = d.online_buyers || {};
          var order = ['IE', 'NL', 'DK', 'CZ', 'SK', 'DE', 'AT', 'HU', 'PL'];
          var flags = { IE: '🇮🇪', NL: '🇳🇱', DK: '🇩🇰', SK: '🇸🇰', CZ: '🇨🇿', DE: '🇩🇪', AT: '🇦🇹', PL: '🇵🇱', HU: '🇭🇺' };
          var countries = order.map(function (code) {
            var c = buyers[code];
            return c && c.latest_value != null
              ? { code: code, label: c.label, val: c.latest_value, flag: flags[code] || '', sk: code === 'SK' }
              : null;
          }).filter(Boolean);
          if (countries.length > 0) {
            countries.sort(function (a, b) { return b.val - a.val; });
            DATA.countries = countries;
            DATA.year = (buyers.SK && buyers.SK.latest_year) || DATA.year;
            DATA.euAvg = (buyers.EU27_2020 && buyers.EU27_2020.latest_value) || DATA.euAvg;
          }
        } catch (e) { /* ignore malformed data */ }
      }
      cb();
    };
    r.onerror = r.ontimeout = cb;
    r.send();
  }

  function render() {
    var container = document.getElementById('eu-comparison-widget');
    var yearEl = document.getElementById('ec-year');
    var sourceEl = document.getElementById('ec-source');
    if (!container) return;
    if (yearEl) yearEl.textContent = DATA.year;
    if (sourceEl) sourceEl.textContent = DATA.source;

    var maxVal = Math.max.apply(null, DATA.countries.map(function (c) { return c.val; }));
    maxVal = Math.max(maxVal, DATA.euAvg || 0);

    var html = '';
    DATA.countries.forEach(function (c) {
      var pct = (c.val / maxVal * 100).toFixed(1);
      var color = c.sk
        ? 'linear-gradient(90deg, rgba(126,200,160,0.55), rgba(126,200,160,0.85))'
        : 'linear-gradient(90deg, rgba(212,165,90,0.22), rgba(212,165,90,0.42))';
      var avgPct = DATA.euAvg ? (DATA.euAvg / maxVal * 100).toFixed(1) : null;
      html += '<div class="ec-bar-row">' +
        '<div class="ec-bar-label' + (c.sk ? ' sk-label' : '') + '">' + c.flag + ' ' + c.label + '</div>' +
        '<div class="ec-bar-wrap">' +
          (avgPct ? '<div class="ec-avg-marker" style="left:' + avgPct + '%" data-label="EÚ ' + DATA.euAvg + '%"></div>' : '') +
          '<div class="ec-bar-fill" style="background:' + color + '" data-target="' + pct + '">' +
            '<span class="ec-bar-fill-val">' + c.val + ' %</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    });

    if (DATA.euAvg) {
      var euPct = (DATA.euAvg / maxVal * 100).toFixed(1);
      html += '<div class="ec-bar-row ec-eu-row">' +
        '<div class="ec-bar-label" style="color:var(--white20)">🇪🇺 EÚ priemer</div>' +
        '<div class="ec-bar-wrap">' +
          '<div class="ec-bar-fill" style="background:rgba(240,232,216,0.12)" data-target="' + euPct + '">' +
            '<span class="ec-bar-fill-val" style="color:var(--white40)">' + DATA.euAvg + ' %</span>' +
          '</div>' +
        '</div>' +
      '</div>';
    }

    container.innerHTML = html;

    /* Animate bar fills on scroll-in */
    var bars = container.querySelectorAll('.ec-bar-fill');
    var done = false;
    var obs = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting && !done) {
        done = true;
        bars.forEach(function (b, i) {
          setTimeout(function () { b.style.width = b.getAttribute('data-target') + '%'; }, i * 70);
        });
      }
    }, { threshold: 0.2 });
    obs.observe(container);
  }

  function init() { tryLoadLive(render); }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
