const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const OUT_DIR = path.join(__dirname);
const HTML_PATH = path.join(OUT_DIR, 'vietnam_tou2026_presentation_v2.html');
const PPTX_PATH = path.join(OUT_DIR, 'vietnam_tou2026_presentation_v2.pptx');

const COLORS = {
  titleBg: '1A5276',
  sectionBg: '1B4F72',
  slideBg: 'FFFFFF',
  title: '1A3550',
  body: '2C3E50',
  accent: '27AE60',
  muted: '7F8C8D',
  footer: '95A5A6',
  red: 'E74C3C',
  blue: '3498DB',
  cardBg: 'EBF5FB',
  cardBorder: 'D5E8F5',
  tableBorder: 'E0E0E0',
};

const DATA = {
  title: 'Vietnam TOU 2026',
  subtitle: 'TOU Analysis V2',
  audience: 'Internal Allotrope review using the Phase 5/6 tariff impact outputs',
  asOf: 'May 2026',
  execSummary: [
    'Worst revenue hit: Emivest Bundled Discount moved by -$63,305 (-11.26%).',
    'Best preserved case: Fixed EVN PPA kept Emivest nearly flat at -$6,076 (-1.08%).',
    'Largest upside: Ecoplexus 40MW DPPA gained +$1,348,006 revenue and +$11.8M NPV.',
    'Core mechanism: the tariff removed the morning peak and collapsed BESS from two cycles to one.',
  ],
  tariffRows: [
    ['Off-Peak (Mon-Sat)', '22:00-04:00', '00:00-06:00'],
    ['Normal (Mon-Sat)', '04:00-09:30, 11:30-17:00, 20:00-22:00', '06:00-17:30, 22:30-24:00'],
    ['Peak (Mon-Sat)', '09:30-11:30 and 17:00-20:00', '17:30-22:30'],
    ['Sunday', 'Normal 04:00-22:00 / Off-Peak 22:00-04:00', 'Normal 06:00-24:00 / Off-Peak 00:00-06:00'],
    ['BESS cycles/day', '2', '1'],
  ],
  emivestCases: [
    { label: 'Bundled Discount', oldRevenue: 562144, newRevenue: 498839, deltaRevenue: -63305, deltaRevenuePct: -11.26, oldIrr: 25.31, newIrr: 22.06, deltaIrr: -3.25, deltaNpv: -659445, oldDscr: 1.96, newDscr: 1.64 },
    { label: 'Separate PV+BESS', oldRevenue: 562144, newRevenue: 525804, deltaRevenue: -36341, deltaRevenuePct: -6.46, oldIrr: 25.31, newIrr: 23.61, deltaIrr: -1.70, deltaNpv: -323683, oldDscr: 1.96, newDscr: 1.78 },
    { label: 'DPPA (CfD)', oldRevenue: 562144, newRevenue: 542467, deltaRevenue: -19677, deltaRevenuePct: -3.50, oldIrr: 25.31, newIrr: 24.55, deltaIrr: -0.76, deltaNpv: -116188, oldDscr: 1.96, newDscr: 1.86 },
    { label: 'Fixed EVN PPA', oldRevenue: 562144, newRevenue: 556068, deltaRevenue: -6076, deltaRevenuePct: -1.08, oldIrr: 25.31, newIrr: 25.32, deltaIrr: 0.00, deltaNpv: 53174, oldDscr: 1.96, newDscr: 1.93 },
  ],
  ecoplexus: {
    oldRevenue: 5543642,
    newRevenue: 6891647,
    deltaRevenue: 1348006,
    deltaRevenuePct: 24.32,
    oldProjectIrr: 6.26,
    newProjectIrr: 9.31,
    oldEquityIrr: 5.71,
    newEquityIrr: 8.70,
    oldNpv: 6009427,
    newNpv: 17808162,
    deltaNpv: 11798735,
    oldDscr: 1.28,
    newDscr: 1.27,
    oldDppaRevenue: 2547079,
    newDppaRevenue: 3166432,
    oldGridSavings: 2996563,
    newGridSavings: 3725215,
  },
  decomposition: [
    { label: 'Loss of morning peak uplift', value: -65343, explanation: 'Solar no longer lands in a morning peak block.' },
    { label: 'BESS cycle reduction', value: -32609, explanation: 'One peak cycle removes half of the old arbitrage rhythm.' },
    { label: 'Shifted peak window', value: 34640, explanation: 'Later discharge better aligns with evening load.' },
    { label: 'Off-peak rate changes', value: 7, explanation: 'Minimal impact in this case.' },
  ],
  mitigations: [
    'Re-price bundled and DPPA offers against the lower evening-only uplift.',
    'Re-tune BESS dispatch to preserve state of charge until the evening peak.',
    'Separate PV-heavy and BESS-heavy commercial structures when updating discounts.',
    'Keep both tariff baselines in regression artifacts until the 2026 schedule is the default.',
  ],
  oldDispatch: [
    { h: 0, s: 0, b: 0, g: 964 }, { h: 1, s: 0, b: 0, g: 972 }, { h: 2, s: 0, b: 0, g: 966 }, { h: 3, s: 0, b: 0, g: 939 },
    { h: 4, s: 0, b: 0, g: 923 }, { h: 5, s: 0.4, b: 0, g: 910 }, { h: 6, s: 150, b: 0, g: 855 }, { h: 7, s: 421, b: 0, g: 446 },
    { h: 8, s: 712, b: 0, g: 394 }, { h: 9, s: 918, b: 0, g: 374 }, { h: 10, s: 996, b: 13, g: 312 }, { h: 11, s: 1001, b: 6, g: 303 },
    { h: 12, s: 945, b: 0, g: 374 }, { h: 13, s: 916, b: 0, g: 413 }, { h: 14, s: 793, b: 0, g: 556 }, { h: 15, s: 602, b: 0, g: 747 },
    { h: 16, s: 344, b: 0, g: 981 }, { h: 17, s: 60, b: 735, g: 518 }, { h: 18, s: 0, b: 401, g: 892 }, { h: 19, s: 0, b: 27, g: 1192 },
    { h: 20, s: 0, b: 0, g: 1268 }, { h: 21, s: 0, b: 0, g: 1282 }, { h: 22, s: 0, b: 0, g: 1258 }, { h: 23, s: 0, b: 0, g: 901 },
  ],
  newDispatch: [
    { h: 0, s: 0, b: 0, g: 964 }, { h: 1, s: 0, b: 0, g: 972 }, { h: 2, s: 0, b: 0, g: 966 }, { h: 3, s: 0, b: 0, g: 939 },
    { h: 4, s: 0, b: 0, g: 923 }, { h: 5, s: 0.4, b: 0, g: 910 }, { h: 6, s: 150, b: 0, g: 855 }, { h: 7, s: 421, b: 0, g: 446 },
    { h: 8, s: 712, b: 0, g: 394 }, { h: 9, s: 918, b: 0, g: 374 }, { h: 10, s: 881, b: 0, g: 440 }, { h: 11, s: 914, b: 0, g: 396 },
    { h: 12, s: 948, b: 0, g: 372 }, { h: 13, s: 946, b: 0, g: 382 }, { h: 14, s: 896, b: 0, g: 453 }, { h: 15, s: 716, b: 0, g: 634 },
    { h: 16, s: 374, b: 0, g: 951 }, { h: 17, s: 60, b: 0, g: 1253 }, { h: 18, s: 0, b: 790, g: 502 }, { h: 19, s: 0, b: 513, g: 706 },
    { h: 20, s: 0, b: 27, g: 1241 }, { h: 21, s: 0, b: 22, g: 1261 }, { h: 22, s: 0, b: 20, g: 1238 }, { h: 23, s: 0, b: 0, g: 901 },
  ],
};

function currency(value) {
  const sign = value < 0 ? '-' : '';
  return `${sign}$${Math.abs(Math.round(value)).toLocaleString('en-US')}`;
}

function percent(value) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function pp(value) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)} pp`;
}

function times(value) {
  return `${value.toFixed(2)}x`;
}

function htmlEscape(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildTable(headers, rows) {
  const headerHtml = headers.map((header) => `<th>${htmlEscape(header)}</th>`).join('');
  const rowHtml = rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`).join('');
  return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${rowHtml}</tbody></table>`;
}

function maxDispatchTotal(points) {
  return Math.max(...points.map((point) => point.s + point.b + point.g));
}

function buildGroupedRevenueChart() {
  const width = 900;
  const height = 320;
  const margin = { top: 24, right: 24, bottom: 70, left: 72 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;
  const maxValue = Math.max(...DATA.emivestCases.flatMap((item) => [item.oldRevenue, item.newRevenue]));
  const groupWidth = chartWidth / DATA.emivestCases.length;
  const barWidth = groupWidth * 0.28;
  const ticks = 4;
  const yTicks = Array.from({ length: ticks + 1 }, (_, index) => Math.round((maxValue * index) / ticks));

  const bars = DATA.emivestCases.map((item, index) => {
    const groupX = margin.left + index * groupWidth;
    const oldHeight = (item.oldRevenue / maxValue) * chartHeight;
    const newHeight = (item.newRevenue / maxValue) * chartHeight;
    const oldX = groupX + groupWidth * 0.18;
    const newX = oldX + barWidth + 16;
    return `
      <rect x="${oldX}" y="${margin.top + chartHeight - oldHeight}" width="${barWidth}" height="${oldHeight}" rx="6" fill="#1A5276"></rect>
      <rect x="${newX}" y="${margin.top + chartHeight - newHeight}" width="${barWidth}" height="${newHeight}" rx="6" fill="#27AE60"></rect>
      <text x="${groupX + groupWidth / 2}" y="${height - 22}" text-anchor="middle" class="axis-label">${htmlEscape(item.label)}</text>
    `;
  }).join('');

  const grid = yTicks.map((tick) => {
    const y = margin.top + chartHeight - (tick / maxValue) * chartHeight;
    return `
      <line x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" stroke="#E7EDF3" stroke-width="1"></line>
      <text x="${margin.left - 12}" y="${y + 4}" text-anchor="end" class="axis-label">${Math.round(tick / 1000)}k</text>
    `;
  }).join('');

  return `
    <svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="Emivest old versus new revenue by PPA option">
      ${grid}
      <line x1="${margin.left}" y1="${margin.top + chartHeight}" x2="${width - margin.right}" y2="${margin.top + chartHeight}" stroke="#AAB7C4" stroke-width="1.2"></line>
      ${bars}
      <g>
        <rect x="${width - 240}" y="12" width="14" height="14" rx="3" fill="#1A5276"></rect>
        <text x="${width - 220}" y="24" class="legend-label">Old revenue</text>
        <rect x="${width - 124}" y="12" width="14" height="14" rx="3" fill="#27AE60"></rect>
        <text x="${width - 104}" y="24" class="legend-label">New revenue</text>
      </g>
    </svg>
  `;
}

function buildHorizontalDeltaChart() {
  const width = 900;
  const height = 280;
  const margin = { top: 24, right: 24, bottom: 24, left: 260 };
  const chartWidth = width - margin.left - margin.right;
  const rowHeight = 52;
  const maxAbs = Math.max(...DATA.decomposition.map((item) => Math.abs(item.value)));
  const zeroX = margin.left + chartWidth / 2;

  const rows = DATA.decomposition.map((item, index) => {
    const y = margin.top + index * rowHeight;
    const scaled = (Math.abs(item.value) / maxAbs) * (chartWidth / 2 - 30);
    const x = item.value >= 0 ? zeroX : zeroX - scaled;
    return `
      <text x="${margin.left - 12}" y="${y + 22}" text-anchor="end" class="axis-label">${htmlEscape(item.label)}</text>
      <rect x="${x}" y="${y + 8}" width="${scaled}" height="20" rx="5" fill="${item.value >= 0 ? '#27AE60' : '#E74C3C'}"></rect>
      <text x="${item.value >= 0 ? x + scaled + 8 : x - 8}" y="${y + 23}" text-anchor="${item.value >= 0 ? 'start' : 'end'}" class="value-label">${currency(item.value)}</text>
    `;
  }).join('');

  return `
    <svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="Revenue decomposition by driver">
      <line x1="${zeroX}" y1="${margin.top - 4}" x2="${zeroX}" y2="${height - margin.bottom}" stroke="#AAB7C4" stroke-width="1.4"></line>
      ${rows}
    </svg>
  `;
}

function buildDispatchChart(points, label) {
  const width = 540;
  const height = 280;
  const margin = { top: 16, right: 14, bottom: 36, left: 52 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;
  const maxValue = maxDispatchTotal(points);
  const barStep = chartWidth / points.length;
  const barWidth = Math.max(10, barStep - 4);

  const bars = points.map((point, index) => {
    const x = margin.left + index * barStep + 2;
    const solarHeight = (point.s / maxValue) * chartHeight;
    const bessHeight = (point.b / maxValue) * chartHeight;
    const gridHeight = (point.g / maxValue) * chartHeight;
    const gridY = margin.top + chartHeight - gridHeight;
    const bessY = gridY - bessHeight;
    const solarY = bessY - solarHeight;
    return `
      <rect x="${x}" y="${gridY}" width="${barWidth}" height="${gridHeight}" fill="#3498DB"></rect>
      <rect x="${x}" y="${bessY}" width="${barWidth}" height="${bessHeight}" fill="#27AE60"></rect>
      <rect x="${x}" y="${solarY}" width="${barWidth}" height="${solarHeight}" fill="#F39C12"></rect>
      ${index % 3 === 0 ? `<text x="${x + barWidth / 2}" y="${height - 12}" text-anchor="middle" class="axis-label">${point.h}</text>` : ''}
    `;
  }).join('');

  return `
    <div class="dispatch-card">
      <div class="dispatch-title">${htmlEscape(label)}</div>
      <svg viewBox="0 0 ${width} ${height}" class="chart-svg" role="img" aria-label="${htmlEscape(label)} dispatch chart">
        <line x1="${margin.left}" y1="${margin.top + chartHeight}" x2="${width - margin.right}" y2="${margin.top + chartHeight}" stroke="#AAB7C4" stroke-width="1.2"></line>
        ${bars}
      </svg>
      <div class="legend-inline">
        <span><i style="background:#F39C12"></i>Solar direct</span>
        <span><i style="background:#27AE60"></i>BESS discharge</span>
        <span><i style="background:#3498DB"></i>Grid import</span>
      </div>
    </div>
  `;
}

function renderHtml() {
  const emivestRows = DATA.emivestCases.map((item) => [
    htmlEscape(item.label),
    currency(item.newRevenue),
    `<span class="${item.deltaRevenue < 0 ? 'neg' : 'pos'}">${currency(item.deltaRevenue)}</span>`,
    `<span class="${item.deltaRevenuePct < 0 ? 'neg' : 'pos'}">${item.deltaRevenuePct.toFixed(2)}%</span>`,
    `<span class="${item.deltaIrr < 0 ? 'neg' : 'pos'}">${pp(item.deltaIrr)}</span>`,
    `<span class="${item.deltaNpv < 0 ? 'neg' : 'pos'}">${currency(item.deltaNpv)}</span>`,
    `${times(item.oldDscr)} -> ${times(item.newDscr)}`,
  ]);

  const tariffRows = DATA.tariffRows.map((row) => row.map((cell) => htmlEscape(cell)));
  const ecoRows = [
    ['Year 1 revenue', currency(DATA.ecoplexus.oldRevenue), currency(DATA.ecoplexus.newRevenue), `<span class="pos">${currency(DATA.ecoplexus.deltaRevenue)}</span>`],
    ['Project IRR', `${DATA.ecoplexus.oldProjectIrr.toFixed(2)}%`, `${DATA.ecoplexus.newProjectIrr.toFixed(2)}%`, `<span class="pos">${pp(DATA.ecoplexus.newProjectIrr - DATA.ecoplexus.oldProjectIrr)}</span>`],
    ['Equity IRR', `${DATA.ecoplexus.oldEquityIrr.toFixed(2)}%`, `${DATA.ecoplexus.newEquityIrr.toFixed(2)}%`, `<span class="pos">${pp(DATA.ecoplexus.newEquityIrr - DATA.ecoplexus.oldEquityIrr)}</span>`],
    ['NPV', currency(DATA.ecoplexus.oldNpv), currency(DATA.ecoplexus.newNpv), `<span class="pos">${currency(DATA.ecoplexus.deltaNpv)}</span>`],
    ['Min DSCR', times(DATA.ecoplexus.oldDscr), times(DATA.ecoplexus.newDscr), `<span class="neg">${(DATA.ecoplexus.newDscr - DATA.ecoplexus.oldDscr).toFixed(2)}x</span>`],
  ];
  const decompRows = DATA.decomposition.map((item) => [
    htmlEscape(item.label),
    `<span class="${item.value < 0 ? 'neg' : 'pos'}">${currency(item.value)}</span>`,
    htmlEscape(item.explanation),
  ]);

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vietnam TOU 2026 TOU Analysis V2</title>
  <style>
    :root {
      --bg: #ffffff;
      --surface: #f8f9fa;
      --title-bg: #1A5276;
      --section-bg: #1B4F72;
      --primary: #1A3550;
      --accent: #27AE60;
      --text: #2C3E50;
      --muted: #7F8C8D;
      --border: #E0E0E0;
      --red: #E74C3C;
      --blue: #3498DB;
      --card: #EBF5FB;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: #0f1720; color: var(--text); font-family: 'Segoe UI', Tahoma, Arial, sans-serif; }
    .deck { width: 100vw; height: calc(100vh - 54px); position: relative; overflow: hidden; }
    .slide { display: none; position: absolute; inset: 0; padding: 2.8rem 3.4rem; background: var(--bg); overflow-y: auto; }
    .slide.active { display: flex; flex-direction: column; }
    .title-slide { background: linear-gradient(160deg, #1A5276 0%, #163d5a 100%); color: #fff; justify-content: center; }
    .section-slide { background: linear-gradient(160deg, #1B4F72 0%, #16394f 100%); color: #fff; justify-content: center; }
    .brand { font-size: 0.8rem; letter-spacing: 0.38rem; text-transform: uppercase; color: #d9e3ea; margin-bottom: 2rem; }
    .hero-title { font-size: 3rem; line-height: 1.04; margin: 0 0 0.8rem; font-weight: 700; max-width: 12ch; }
    .hero-subtitle { font-size: 1.15rem; color: #d7e3ec; max-width: 44rem; line-height: 1.5; }
    .hero-meta { display: flex; gap: 1rem; margin-top: 2rem; color: #b8c7d2; font-size: 0.95rem; flex-wrap: wrap; }
    .section-number { font-size: 5rem; color: var(--accent); font-weight: 700; }
    .section-title { font-size: 2.1rem; margin-top: 0.5rem; max-width: 16ch; }
    .slide-title { font-size: 2rem; color: var(--primary); margin: 0; font-weight: 700; }
    .slide-caption { font-size: 0.98rem; color: var(--muted); margin: 0.65rem 0 1.3rem; }
    .title-rule { width: 100%; height: 4px; background: var(--accent); margin-bottom: 1.2rem; border-radius: 999px; }
    .nav { height: 54px; display: flex; align-items: center; justify-content: center; gap: 1rem; background: #f3f5f7; border-top: 1px solid #dbe2e8; }
    .nav button { border: 1px solid #ced6de; background: white; color: var(--text); border-radius: 999px; padding: 0.45rem 0.9rem; font-weight: 600; cursor: pointer; }
    .nav button:hover { border-color: var(--accent); }
    .counter { min-width: 5rem; text-align: center; color: var(--muted); font-weight: 600; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.4rem; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1rem 1.1rem; }
    .stat-card { background: var(--card); border: 1px solid #d5e8f5; border-radius: 16px; padding: 1rem; }
    .stat-value { font-size: 2rem; font-weight: 700; color: var(--accent); }
    .stat-label { color: var(--muted); text-transform: uppercase; letter-spacing: 0.06rem; font-size: 0.75rem; margin-top: 0.3rem; }
    .bullet-list { margin: 0; padding-left: 1.1rem; line-height: 1.6; }
    .bullet-list li { margin: 0.3rem 0; }
    table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
    th { background: #EBF5FB; color: var(--primary); text-align: left; padding: 0.65rem 0.72rem; border-bottom: 1px solid var(--border); }
    td { padding: 0.62rem 0.72rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .neg { color: var(--red); font-weight: 600; }
    .pos { color: var(--accent); font-weight: 600; }
    .quote { border-left: 4px solid var(--accent); padding-left: 1rem; color: var(--muted); font-size: 0.96rem; }
    .footer-note { margin-top: auto; padding-top: 1rem; color: #95A5A6; font-size: 0.72rem; text-align: center; }
    .chart-svg { width: 100%; height: auto; display: block; }
    .axis-label { fill: #6f7f8b; font-size: 12px; font-family: inherit; }
    .legend-label { fill: #2C3E50; font-size: 12px; font-family: inherit; }
    .value-label { fill: #2C3E50; font-size: 12px; font-weight: 600; font-family: inherit; }
    .dispatch-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1rem; }
    .dispatch-title { font-weight: 700; color: var(--primary); margin-bottom: 0.5rem; }
    .legend-inline { display: flex; gap: 1rem; flex-wrap: wrap; color: var(--muted); font-size: 0.82rem; margin-top: 0.5rem; }
    .legend-inline span { display: inline-flex; align-items: center; gap: 0.4rem; }
    .legend-inline i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; }
    .summary-band { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 1rem; }
    @media (max-width: 900px) {
      .slide { padding: 1.5rem; }
      .grid-2, .grid-3, .summary-band { grid-template-columns: 1fr; }
      .hero-title { font-size: 2.2rem; }
      .section-number { font-size: 4rem; }
    }
  </style>
</head>
<body>
  <div class="deck">
    <section class="slide title-slide active">
      <div class="brand">Allotrope</div>
      <h1 class="hero-title">Vietnam TOU 2026 TOU Analysis V2</h1>
      <div class="hero-subtitle">Updated HTML deck generated from the Phase 5/6 tariff impact report. Focus: how the new tariff reshapes revenue, dispatch, and financing outcomes across Emivest and Ecoplexus.</div>
      <div class="hero-meta">
        <span>${htmlEscape(DATA.asOf)}</span>
        <span>${htmlEscape(DATA.audience)}</span>
      </div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Executive Summary</h2>
      <div class="title-rule"></div>
      <div class="summary-band">
        <div class="card">
          <ul class="bullet-list">
            ${DATA.execSummary.map((item) => `<li>${htmlEscape(item)}</li>`).join('')}
          </ul>
        </div>
        <div class="grid-2">
          <div class="stat-card"><div class="stat-value">-${Math.abs(DATA.emivestCases[0].deltaRevenue).toLocaleString('en-US')}</div><div class="stat-label">Worst revenue move</div></div>
          <div class="stat-card"><div class="stat-value">+${Math.round(DATA.ecoplexus.deltaRevenue / 1000).toLocaleString('en-US')}k</div><div class="stat-label">Ecoplexus revenue gain</div></div>
          <div class="stat-card"><div class="stat-value">${DATA.emivestCases[3].newIrr.toFixed(2)}%</div><div class="stat-label">Most resilient Emivest IRR</div></div>
          <div class="stat-card"><div class="stat-value">${DATA.ecoplexus.newProjectIrr.toFixed(2)}%</div><div class="stat-label">New Ecoplexus project IRR</div></div>
        </div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide section-slide">
      <div class="section-number">01</div>
      <div class="section-title">Tariff Shift and Operating Logic</div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Tariff Change Summary</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">The tariff kept a five-hour peak window, but moved it entirely into the evening and removed the morning solar overlap.</div>
      ${buildTable(['Attribute', 'Old (<= Apr 21)', 'New (>= Apr 22)'], tariffRows)}
      <div class="grid-3" style="margin-top:1rem;">
        <div class="stat-card"><div class="stat-value" style="color:var(--red)">Lost</div><div class="stat-label">Morning peak solar uplift</div></div>
        <div class="stat-card"><div class="stat-value" style="color:var(--red)">2 -> 1</div><div class="stat-label">BESS cycles per day</div></div>
        <div class="stat-card"><div class="stat-value">17:30-22:30</div><div class="stat-label">Single peak block</div></div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Dispatch Implications</h2>
      <div class="title-rule"></div>
      <div class="grid-2">
        <div class="card">
          <h3 style="margin-top:0;color:var(--primary);">Old schedule</h3>
          <ul class="bullet-list">
            <li>Grid charge in off-peak hours 22:00-04:00.</li>
            <li>Morning peak captured solar plus a first BESS discharge.</li>
            <li>Midday recharge allowed a second evening cycle.</li>
            <li>The commercial model monetized both solar timing and battery arbitrage.</li>
          </ul>
        </div>
        <div class="card">
          <h3 style="margin-top:0;color:var(--primary);">New schedule</h3>
          <ul class="bullet-list">
            <li>Solar output from 06:00-17:30 is now normal-priced energy.</li>
            <li>BESS value concentrates in one evening discharge window.</li>
            <li>State-of-charge management becomes more important than daily cycling count.</li>
            <li>PV-heavy structures lose more value than fixed-price offtake structures.</li>
          </ul>
        </div>
      </div>
      <p class="quote" style="margin-top:1rem;">The tariff change is not a broad haircut. It is a shape change: less value during solar hours, more emphasis on evening alignment.</p>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide section-slide">
      <div class="section-number">02</div>
      <div class="section-title">Case-Level Financial Outcomes</div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Emivest Outcome by PPA Structure</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">All Emivest options start from the same old-tariff revenue base of ${currency(DATA.emivestCases[0].oldRevenue)}.</div>
      ${buildTable(['PPA option', 'New revenue', 'Delta revenue', 'Delta revenue %', 'Delta IRR', 'Delta NPV', 'DSCR move'], emivestRows)}
      <div class="grid-2" style="margin-top:1rem;">
        <div class="stat-card"><div class="stat-value" style="color:var(--red)">${currency(DATA.emivestCases[0].deltaRevenue)}</div><div class="stat-label">Worst hit: bundled discount</div></div>
        <div class="stat-card"><div class="stat-value">${currency(DATA.emivestCases[3].deltaRevenue)}</div><div class="stat-label">Best preserved: fixed EVN PPA</div></div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Emivest Revenue Comparison</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">The new schedule compresses the spread between structures, but fixed-price offtake remains the most insulated.</div>
      ${buildGroupedRevenueChart()}
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Ecoplexus 40MW DPPA Upside</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">Ecoplexus moves in the opposite direction because the later evening peak better matches its larger solar plus storage profile.</div>
      ${buildTable(['Metric', 'Old tariff', 'New tariff', 'Delta'], ecoRows)}
      <div class="grid-3" style="margin-top:1rem;">
        <div class="stat-card"><div class="stat-value">${DATA.ecoplexus.newProjectIrr.toFixed(2)}%</div><div class="stat-label">New project IRR</div></div>
        <div class="stat-card"><div class="stat-value">${currency(DATA.ecoplexus.deltaNpv)}</div><div class="stat-label">NPV gain</div></div>
        <div class="stat-card"><div class="stat-value">+${DATA.ecoplexus.deltaRevenuePct.toFixed(2)}%</div><div class="stat-label">Revenue uplift</div></div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide section-slide">
      <div class="section-number">03</div>
      <div class="section-title">Driver Breakdown and Dispatch View</div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Revenue Driver Decomposition</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">Bundled Discount for Emivest shows the cleanest read on what the tariff change is doing economically.</div>
      <div class="grid-2">
        <div class="card">
          ${buildTable(['Driver', 'Impact', 'Interpretation'], decompRows)}
        </div>
        <div class="card">
          ${buildHorizontalDeltaChart()}
        </div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Average-Day Dispatch Comparison</h2>
      <div class="title-rule"></div>
      <div class="slide-caption">Old tariff dispatch shows a morning-plus-evening rhythm; the new tariff concentrates value in the evening block.</div>
      <div class="grid-2">
        ${buildDispatchChart(DATA.oldDispatch, 'Old tariff dispatch')}
        ${buildDispatchChart(DATA.newDispatch, 'New tariff dispatch')}
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Recommended Actions</h2>
      <div class="title-rule"></div>
      <div class="grid-2">
        <div class="card">
          <ul class="bullet-list">
            ${DATA.mitigations.map((item) => `<li>${htmlEscape(item)}</li>`).join('')}
          </ul>
        </div>
        <div class="card">
          <h3 style="margin-top:0;color:var(--primary);">Commercial read-through</h3>
          <ul class="bullet-list">
            <li>Expect more pressure on PV-led C&amp;I offers than on fixed-price structures.</li>
            <li>Storage still matters, but only if it is dispatched for the evening window.</li>
            <li>Large systems with meaningful evening coincidence can improve under the new schedule.</li>
            <li>Pricing and dispatch assumptions should be refreshed together, not independently.</li>
          </ul>
        </div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>

    <section class="slide">
      <h2 class="slide-title">Bottom Line</h2>
      <div class="title-rule"></div>
      <div class="grid-2">
        <div class="card">
          <h3 style="margin-top:0;color:var(--primary);">Who loses</h3>
          <ul class="bullet-list">
            <li>Smaller C&amp;I structures that depended on morning solar peak pricing.</li>
            <li>Battery strategies designed around two monetizable cycles per day.</li>
          </ul>
        </div>
        <div class="card">
          <h3 style="margin-top:0;color:var(--primary);">Who wins</h3>
          <ul class="bullet-list">
            <li>Projects with stronger evening coincidence and storage that can hold energy later.</li>
            <li>Larger DPPA structures where the new peak amplifies evening delivery economics.</li>
          </ul>
        </div>
      </div>
      <div class="grid-3" style="margin-top:1rem;">
        <div class="stat-card"><div class="stat-value" style="color:var(--red)">-11.26%</div><div class="stat-label">Emivest worst revenue move</div></div>
        <div class="stat-card"><div class="stat-value">-1.08%</div><div class="stat-label">Emivest most resilient move</div></div>
        <div class="stat-card"><div class="stat-value">+24.32%</div><div class="stat-label">Ecoplexus revenue move</div></div>
      </div>
      <div class="footer-note">Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation</div>
    </section>
  </div>
  <nav class="nav">
    <button id="prev" type="button">Prev</button>
    <div id="counter" class="counter">1 / 12</div>
    <button id="next" type="button">Next</button>
  </nav>
  <script>
    const slides = Array.from(document.querySelectorAll('.slide'));
    let current = 0;
    const counter = document.getElementById('counter');
    function goTo(index) {
      slides[current].classList.remove('active');
      current = Math.max(0, Math.min(index, slides.length - 1));
      slides[current].classList.add('active');
      counter.textContent = (current + 1) + ' / ' + slides.length;
    }
    document.getElementById('prev').addEventListener('click', () => goTo(current - 1));
    document.getElementById('next').addEventListener('click', () => goTo(current + 1));
    document.addEventListener('keydown', (event) => {
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(event.key)) {
        event.preventDefault();
        goTo(current + 1);
      }
      if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(event.key)) {
        event.preventDefault();
        goTo(current - 1);
      }
      if (event.key === 'Home') {
        goTo(0);
      }
      if (event.key === 'End') {
        goTo(slides.length - 1);
      }
    });
  </script>
</body>
</html>`;

  fs.writeFileSync(HTML_PATH, html, 'utf8');
}

function addFooter(slide) {
  slide.addText(
    'Confidential - For Internal Use by Allotrope & Key Partners - Not for Further Circulation',
    { x: 0.3, y: 6.95, w: 12.7, h: 0.2, fontSize: 7, fontFace: 'Calibri', color: COLORS.footer, align: 'center' },
  );
}

function addTitleBar(slide, pptx, title, caption) {
  slide.addText(title, {
    x: 0.5, y: 0.3, w: 12.3, h: 0.65,
    fontSize: 22, fontFace: 'Calibri Light', color: COLORS.title, bold: true,
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 0.97, w: 12.3, h: 0.04,
    fill: { color: COLORS.accent }, line: { color: COLORS.accent },
  });
  if (caption) {
    slide.addText(caption, {
      x: 0.5, y: 1.05, w: 12.3, h: 0.35,
      fontSize: 11, fontFace: 'Calibri', color: COLORS.muted,
    });
  }
}

function addSectionDivider(pptx, number, title) {
  const slide = pptx.addSlide();
  slide.background = { color: COLORS.sectionBg };
  slide.addText(number, {
    x: 0.6, y: 1.2, w: 3, h: 1.8,
    fontSize: 72, fontFace: 'Calibri Light', color: COLORS.accent, bold: true,
  });
  slide.addText(title, {
    x: 0.6, y: 3.2, w: 12, h: 1.0,
    fontSize: 28, fontFace: 'Calibri Light', color: 'FFFFFF', bold: true,
  });
  addFooter(slide);
  return slide;
}

function addStatCards(slide, stats, colX, colW) {
  stats.forEach((stat, index) => {
    const x = colX[index];
    slide.addShape('roundRect', {
      x, y: 5.0, w: colW, h: 1.35,
      fill: { color: COLORS.cardBg },
      line: { color: COLORS.cardBorder, width: 1 },
      rectRadius: 0.05,
    });
    slide.addText(stat.value, {
      x, y: 5.12, w: colW, h: 0.45,
      fontSize: 24, fontFace: 'Calibri Light', bold: true,
      color: stat.color, align: 'center',
    });
    slide.addText(stat.label, {
      x, y: 5.68, w: colW, h: 0.28,
      fontSize: 9, fontFace: 'Calibri', color: COLORS.muted, align: 'center',
    });
  });
}

function renderPptx() {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';

  const titleSlide = pptx.addSlide();
  titleSlide.background = { color: COLORS.titleBg };
  titleSlide.addText('ALLOTROPE', {
    x: 0.6, y: 0.5, w: 12, h: 0.35,
    fontSize: 11, fontFace: 'Calibri Light', color: 'FFFFFF', charSpacing: 5,
  });
  titleSlide.addText('Vietnam TOU 2026 TOU Analysis V2', {
    x: 0.6, y: 2.2, w: 11.6, h: 1.0,
    fontSize: 30, fontFace: 'Calibri Light', color: 'FFFFFF', bold: true,
  });
  titleSlide.addText('Updated deck from the Phase 5/6 tariff impact report\nEmivest and Ecoplexus case review\nMay 2026', {
    x: 0.6, y: 4.2, w: 10, h: 1.0,
    fontSize: 13, fontFace: 'Calibri', color: 'BDC3C7',
  });

  const summarySlide = pptx.addSlide();
  addTitleBar(summarySlide, pptx, 'Executive Summary', 'Updated TOU presentation regenerated with the refreshed present skill guidance.');
  summarySlide.addText(DATA.execSummary.map((item) => ({ text: item, options: { bullet: { indent: 14 } } })), {
    x: 0.5, y: 1.5, w: 8.0, h: 3.3,
    fontSize: 13, fontFace: 'Calibri', color: COLORS.body, breakLine: true, paraSpaceAfterPt: 8,
  });
  addStatCards(summarySlide, [
    { value: currency(DATA.emivestCases[0].deltaRevenue), label: 'Worst Revenue Move', color: COLORS.red },
    { value: currency(DATA.ecoplexus.deltaRevenue), label: 'Ecoplexus Revenue Gain', color: COLORS.accent },
    { value: `${DATA.ecoplexus.newProjectIrr.toFixed(2)}%`, label: 'New Ecoplexus Project IRR', color: COLORS.accent },
  ], [0.6, 4.8, 9.0], 3.9);
  addFooter(summarySlide);

  addSectionDivider(pptx, '01', 'Tariff Shift and Operating Logic');

  const tariffSlide = pptx.addSlide();
  addTitleBar(tariffSlide, pptx, 'Tariff Change Summary', 'The five-hour peak window moved entirely into the evening, removing morning solar coincidence.');
  const tariffTable = [
    [
      { text: 'Attribute', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Old (<= Apr 21)', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'New (>= Apr 22)', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
    ],
    ...DATA.tariffRows.map((row) => row.map((cell) => ({ text: cell }))),
  ];
  tariffSlide.addTable(tariffTable, {
    x: 0.5, y: 1.45, w: 12.3,
    fontSize: 10, fontFace: 'Calibri', color: COLORS.body,
    border: { type: 'solid', color: COLORS.tableBorder, pt: 0.5 },
    rowH: 0.43, valign: 'middle', colW: [3.2, 4.4, 4.7],
  });
  addStatCards(tariffSlide, [
    { value: 'Lost', label: 'Morning Peak Solar Uplift', color: COLORS.red },
    { value: '2 -> 1', label: 'BESS Cycles Per Day', color: COLORS.red },
    { value: '17:30-22:30', label: 'Single Peak Block', color: COLORS.accent },
  ], [0.6, 4.8, 9.0], 3.9);
  addFooter(tariffSlide);

  const dispatchSlide = pptx.addSlide();
  addTitleBar(dispatchSlide, pptx, 'Dispatch Implications', 'The economic loss is driven by shape, not by a uniform rate cut.');
  dispatchSlide.addText('Old schedule', {
    x: 0.5, y: 1.45, w: 5.8, h: 0.3,
    fontSize: 14, fontFace: 'Calibri Light', color: COLORS.title, bold: true,
  });
  dispatchSlide.addText('• Charge in off-peak 22:00-04:00\n• Morning peak captured solar plus a first battery discharge\n• Midday recharge enabled a second evening cycle\n• Value stack combined solar timing and battery arbitrage', {
    x: 0.5, y: 1.8, w: 5.8, h: 2.2,
    fontSize: 13, fontFace: 'Calibri', color: COLORS.body, valign: 'top', breakLine: true, paraSpaceAfterPt: 6,
  });
  dispatchSlide.addShape(pptx.ShapeType.line, { x: 6.55, y: 1.45, w: 0, h: 4.9, line: { color: COLORS.tableBorder, width: 1 } });
  dispatchSlide.addText('New schedule', {
    x: 7.0, y: 1.45, w: 5.8, h: 0.3,
    fontSize: 14, fontFace: 'Calibri Light', color: COLORS.title, bold: true,
  });
  dispatchSlide.addText('• Solar from 06:00-17:30 is now fully normal-priced\n• Storage value concentrates in one evening discharge window\n• State-of-charge preservation matters more than cycle count\n• PV-heavy structures lose more value than fixed-price offtake structures', {
    x: 7.0, y: 1.8, w: 5.8, h: 2.2,
    fontSize: 13, fontFace: 'Calibri', color: COLORS.body, valign: 'top', breakLine: true, paraSpaceAfterPt: 6,
  });
  dispatchSlide.addText('Bottom line: the tariff change rewards evening alignment and penalizes structures that relied on morning solar uplift.', {
    x: 0.5, y: 6.25, w: 12.3, h: 0.3,
    fontSize: 10, fontFace: 'Calibri', color: COLORS.muted,
  });
  addFooter(dispatchSlide);

  addSectionDivider(pptx, '02', 'Case-Level Financial Outcomes');

  const emivestSlide = pptx.addSlide();
  addTitleBar(emivestSlide, pptx, 'Emivest Outcome by PPA Structure', `All four options start from ${currency(DATA.emivestCases[0].oldRevenue)} old-tariff revenue.`);
  const emivestTable = [
    [
      { text: 'PPA Option', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'New Rev', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Delta Rev', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Delta IRR', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Delta NPV', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
    ],
    ...DATA.emivestCases.map((item) => [item.label, currency(item.newRevenue), currency(item.deltaRevenue), pp(item.deltaIrr), currency(item.deltaNpv)]),
  ];
  emivestSlide.addTable(emivestTable, {
    x: 0.5, y: 1.45, w: 12.3,
    fontSize: 10.5, fontFace: 'Calibri', color: COLORS.body,
    border: { type: 'solid', color: COLORS.tableBorder, pt: 0.5 },
    rowH: 0.46, valign: 'middle', colW: [3.35, 2.0, 2.0, 1.6, 3.35],
  });
  addStatCards(emivestSlide, [
    { value: currency(DATA.emivestCases[0].deltaRevenue), label: 'Worst Hit: Bundled', color: COLORS.red },
    { value: currency(DATA.emivestCases[3].deltaRevenue), label: 'Best Preserved: Fixed PPA', color: COLORS.accent },
    { value: times(DATA.emivestCases[0].newDscr), label: 'Lowest New DSCR', color: COLORS.red },
  ], [0.6, 4.8, 9.0], 3.9);
  addFooter(emivestSlide);

  const ecoSlide = pptx.addSlide();
  addTitleBar(ecoSlide, pptx, 'Ecoplexus 40MW DPPA Upside', 'Ecoplexus benefits because the new evening peak better aligns with its larger solar plus storage profile.');
  const ecoTable = [
    [
      { text: 'Metric', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Old', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'New', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Delta', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
    ],
    ['Year 1 Revenue', currency(DATA.ecoplexus.oldRevenue), currency(DATA.ecoplexus.newRevenue), currency(DATA.ecoplexus.deltaRevenue)],
    ['Project IRR', `${DATA.ecoplexus.oldProjectIrr.toFixed(2)}%`, `${DATA.ecoplexus.newProjectIrr.toFixed(2)}%`, pp(DATA.ecoplexus.newProjectIrr - DATA.ecoplexus.oldProjectIrr)],
    ['Equity IRR', `${DATA.ecoplexus.oldEquityIrr.toFixed(2)}%`, `${DATA.ecoplexus.newEquityIrr.toFixed(2)}%`, pp(DATA.ecoplexus.newEquityIrr - DATA.ecoplexus.oldEquityIrr)],
    ['NPV', currency(DATA.ecoplexus.oldNpv), currency(DATA.ecoplexus.newNpv), currency(DATA.ecoplexus.deltaNpv)],
    ['Min DSCR', times(DATA.ecoplexus.oldDscr), times(DATA.ecoplexus.newDscr), `${(DATA.ecoplexus.newDscr - DATA.ecoplexus.oldDscr).toFixed(2)}x`],
  ];
  ecoSlide.addTable(ecoTable, {
    x: 0.5, y: 1.45, w: 12.3,
    fontSize: 10.5, fontFace: 'Calibri', color: COLORS.body,
    border: { type: 'solid', color: COLORS.tableBorder, pt: 0.5 },
    rowH: 0.5, valign: 'middle', colW: [3.4, 2.1, 2.1, 4.7],
  });
  addStatCards(ecoSlide, [
    { value: `${DATA.ecoplexus.newProjectIrr.toFixed(2)}%`, label: 'New Project IRR', color: COLORS.accent },
    { value: currency(DATA.ecoplexus.deltaNpv), label: 'NPV Gain', color: COLORS.accent },
    { value: `+${DATA.ecoplexus.deltaRevenuePct.toFixed(2)}%`, label: 'Revenue Uplift', color: COLORS.accent },
  ], [0.6, 4.8, 9.0], 3.9);
  addFooter(ecoSlide);

  addSectionDivider(pptx, '03', 'Driver Breakdown and Actions');

  const driverSlide = pptx.addSlide();
  addTitleBar(driverSlide, pptx, 'Revenue Driver Decomposition', 'Bundled Discount at Emivest isolates the commercial effect of the tariff shift most clearly.');
  const driverTable = [
    [
      { text: 'Driver', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Impact', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
      { text: 'Interpretation', options: { bold: true, fill: { color: COLORS.cardBg }, color: COLORS.title, fontFace: 'Calibri', fontSize: 11 } },
    ],
    ...DATA.decomposition.map((item) => [item.label, currency(item.value), item.explanation]),
  ];
  driverSlide.addTable(driverTable, {
    x: 0.5, y: 1.45, w: 12.3,
    fontSize: 10.5, fontFace: 'Calibri', color: COLORS.body,
    border: { type: 'solid', color: COLORS.tableBorder, pt: 0.5 },
    rowH: 0.56, valign: 'middle', colW: [3.7, 1.8, 6.8],
  });
  driverSlide.addText('Primary conclusion: most of the downside comes from the removal of the morning peak block, partly offset by improved evening timing.', {
    x: 0.5, y: 6.2, w: 12.3, h: 0.35,
    fontSize: 10, fontFace: 'Calibri', color: COLORS.muted,
  });
  addFooter(driverSlide);

  const actionsSlide = pptx.addSlide();
  addTitleBar(actionsSlide, pptx, 'Recommended Actions', 'Commercial repricing and dispatch retuning should move together.');
  actionsSlide.addText(DATA.mitigations.map((item) => ({ text: item, options: { bullet: { indent: 14 } } })), {
    x: 0.5, y: 1.45, w: 12.3, h: 3.0,
    fontSize: 13, fontFace: 'Calibri', color: COLORS.body, breakLine: true, paraSpaceAfterPt: 8,
  });
  addStatCards(actionsSlide, [
    { value: '-11.26%', label: 'Emivest Worst Revenue Move', color: COLORS.red },
    { value: '-1.08%', label: 'Fixed PPA Revenue Move', color: COLORS.accent },
    { value: '+24.32%', label: 'Ecoplexus Revenue Move', color: COLORS.accent },
  ], [0.6, 4.8, 9.0], 3.9);
  addFooter(actionsSlide);

  return pptx.writeFile({ fileName: PPTX_PATH });
}

async function main() {
  renderHtml();
  await renderPptx();
  console.log(`Generated ${path.basename(HTML_PATH)}`);
  console.log(`Generated ${path.basename(PPTX_PATH)}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
