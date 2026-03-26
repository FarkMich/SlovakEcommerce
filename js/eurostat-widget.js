/**
 * Slovak E-commerce — Eurostat Live Data Widget
 * Vkladaj do HTML pred </body>:
 *   <script src="/js/eurostat-widget.js"></script>
 *
 * Požiadavky v HTML:
 *   <div id="eu-comparison-widget"></div>
 *   <span class="eurostat-sk-value"></span>   ← auto-fill SK %
 *   <span class="eurostat-eu-value"></span>   ← auto-fill EÚ %
 *   <span class="eurostat-updated"></span>    ← auto-fill dátum aktualizácie
 */

(function () {
  'use strict';

  const DATA_URL = '/data/eurostat.json';

  // Farby pre krajiny (espresso/gold paleta)
  const COUNTRY_COLORS = {
    SK: '#C9A84C', // gold – zvýraznená
    CZ: '#6B8F71',
    IE: '#2C1A0E',
    NL: '#4A3728',
    DK: '#7A6A5A',
    DE: '#9A8A7A',
    AT: '#B8A898',
    PL: '#8A9A8A',
    HU: '#9A8A9A',
  };

  const EU_COLOR = '#CCCCCC';

  async function loadData() {
    try {
      const res = await fetch(DATA_URL + '?t=' + Date.now());
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } catch (e) {
      console.warn('[Eurostat Widget] Nedá sa načítať data/eurostat.json:', e.message);
      return null;
    }
  }

  function fillInlineValues(data) {
    if (!data) return;
    const buyers = data.online_buyers || {};

    // Naplní všetky <span class="eurostat-sk-value">
    const skVal = buyers.SK?.latest_value;
    document.querySelectorAll('.eurostat-sk-value').forEach(el => {
      if (skVal != null) el.textContent = skVal + ' %';
    });

    // EÚ priemer
    const euVal = buyers.EU27_2020?.latest_value;
    document.querySelectorAll('.eurostat-eu-value').forEach(el => {
      if (euVal != null) el.textContent = euVal + ' %';
    });

    // Dátum aktualizácie
    const updated = data.meta?.updated_display;
    document.querySelectorAll('.eurostat-updated').forEach(el => {
      if (updated) el.textContent = 'Zdroj: Eurostat · Aktualizované ' + updated;
    });
  }

  function buildComparisonChart(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !data) return;

    const buyers = data.online_buyers || {};

    // Zoraď krajiny podľa hodnoty (zostupne), EÚ priemer daj na koniec
    const countries = Object.entries(buyers)
      .filter(([code]) => code !== 'EU27_2020')
      .sort(([, a], [, b]) => (b.latest_value || 0) - (a.latest_value || 0));

    const euAvg = buyers.EU27_2020?.latest_value;
    const latestYear = data.online_buyers?.SK?.latest_year || '2024';

    // CSS
    const style = document.createElement('style');
    style.textContent = `
      .ec-chart { font-family: 'Sora', Arial, sans-serif; margin: 24px 0; }
      .ec-chart-title { font-size: 13px; color: #888; margin-bottom: 16px; letter-spacing: 0.05em; text-transform: uppercase; }
      .ec-bar-row { display: flex; align-items: center; margin-bottom: 10px; gap: 12px; }
      .ec-bar-label { width: 100px; font-size: 13px; color: #2C1A0E; flex-shrink: 0; text-align: right; }
      .ec-bar-label.sk { font-weight: 700; color: #C9A84C; }
      .ec-bar-wrap { flex: 1; height: 28px; background: #F5F5F5; border-radius: 4px; overflow: hidden; position: relative; }
      .ec-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s cubic-bezier(0.16,1,0.3,1); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; }
      .ec-bar-val { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; }
      .ec-bar-val.dark { color: #2C1A0E; }
      .ec-avg-line { position: absolute; top: 0; bottom: 0; width: 2px; background: rgba(44,26,14,0.25); z-index: 2; }
      .ec-avg-line::after { content: attr(data-label); position: absolute; top: -18px; left: 4px; font-size: 10px; color: #888; white-space: nowrap; }
      .ec-source { font-size: 11px; color: #aaa; margin-top: 12px; }
    `;
    document.head.appendChild(style);

    container.innerHTML = '';
    const chart = document.createElement('div');
    chart.className = 'ec-chart';

    const title = document.createElement('div');
    title.className = 'ec-chart-title';
    title.textContent = `Online nakupujúci – ${latestYear} (% používateľov internetu)`;
    chart.appendChild(title);

    const maxVal = Math.max(...countries.map(([, d]) => d.latest_value || 0), euAvg || 0);

    countries.forEach(([code, cdata]) => {
      const val = cdata.latest_value;
      if (val == null) return;

      const isSK = code === 'SK';
      const row = document.createElement('div');
      row.className = 'ec-bar-row';

      const lbl = document.createElement('div');
      lbl.className = 'ec-bar-label' + (isSK ? ' sk' : '');
      lbl.textContent = cdata.label;

      const wrap = document.createElement('div');
      wrap.className = 'ec-bar-wrap';

      // EÚ priemer vertikálna čiara
      if (euAvg) {
        const line = document.createElement('div');
        line.className = 'ec-avg-line';
        line.style.left = (euAvg / maxVal * 100) + '%';
        line.setAttribute('data-label', 'EÚ priemer ' + euAvg + '%');
        wrap.appendChild(line);
      }

      const fill = document.createElement('div');
      fill.className = 'ec-bar-fill';
      fill.style.width = '0%';
      fill.style.backgroundColor = isSK ? COUNTRY_COLORS.SK : (COUNTRY_COLORS[code] || '#ccc');

      const valEl = document.createElement('span');
      valEl.className = 'ec-bar-val' + (val < 30 ? ' dark' : '');
      valEl.textContent = val + ' %';

      fill.appendChild(valEl);
      wrap.appendChild(fill);

      row.appendChild(lbl);
      row.appendChild(wrap);
      chart.appendChild(row);

      // Animácia pri scroll
      setTimeout(() => { fill.style.width = (val / maxVal * 100) + '%'; }, 100);
    });

    // EÚ priemer row
    if (euAvg) {
      const avgRow = document.createElement('div');
      avgRow.className = 'ec-bar-row';
      avgRow.style.marginTop = '8px';
      avgRow.style.borderTop = '1px solid #eee';
      avgRow.style.paddingTop = '8px';

      const avgLbl = document.createElement('div');
      avgLbl.className = 'ec-bar-label';
      avgLbl.style.color = '#888';
      avgLbl.textContent = 'EÚ priemer';

      const avgWrap = document.createElement('div');
      avgWrap.className = 'ec-bar-wrap';

      const avgFill = document.createElement('div');
      avgFill.className = 'ec-bar-fill';
      avgFill.style.width = '0%';
      avgFill.style.backgroundColor = EU_COLOR;

      const avgVal = document.createElement('span');
      avgVal.className = 'ec-bar-val dark';
      avgVal.textContent = euAvg + ' %';

      avgFill.appendChild(avgVal);
      avgWrap.appendChild(avgFill);
      avgRow.appendChild(avgLbl);
      avgRow.appendChild(avgWrap);
      chart.appendChild(avgRow);

      setTimeout(() => { avgFill.style.width = (euAvg / maxVal * 100) + '%'; }, 200);
    }

    const source = document.createElement('div');
    source.className = 'ec-source';
    source.textContent = data.meta?.source + ' · Aktualizované ' + (data.meta?.updated_display || '');
    chart.appendChild(source);

    container.appendChild(chart);
  }

  // Spustenie po načítaní DOM
  function init() {
    loadData().then(data => {
      fillInlineValues(data);
      buildComparisonChart(data, 'eu-comparison-widget');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
