const PptxGenJS = require('pptxgenjs');
const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.defineLayout({ name: 'WIDE', width: 13.33, height: 7.5 });
pptx.layout = 'WIDE';

const COLORS = {
  bg: 'FFFFFF', navy: '1A5276', dark: '1A3550', text: '2C3E50',
  accent: '27AE60', muted: '7F8C8D', footer: '95A5A6', tableHdr: 'EBF5FB',
  red: 'E74C3C', orange: 'E67E22', blue: '3498DB'
};

function footer(slide) {
  slide.addText('Confidential — For Internal Use by Allotrope & Key Partners — Not for Further Circulation',
    { x: 0.3, y: 6.95, w: 12.7, h: 0.2, fontSize: 7, color: COLORS.footer, align: 'center' });
}

function titleBar(slide, title) {
  slide.addText(title, { x: 0.5, y: 0.3, w: 12.3, h: 0.65, fontSize: 22, color: COLORS.dark, bold: true });
  slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 0.97, w: 12.3, h: 0.04, fill: { color: COLORS.accent }, line: { color: COLORS.accent } });
}

// ---------- TITLE SLIDE ----------
const s1 = pptx.addSlide();
s1.background = { color: COLORS.navy };
s1.addText('ALLOTROPE', { x: 0.6, y: 0.5, w: 12, h: 0.4, fontSize: 11, color: 'FFFFFF', charSpacing: 5 });
s1.addText('Vietnam TOU Tariff 2026', { x: 0.6, y: 2.4, w: 11.5, h: 1.8, fontSize: 36, color: 'FFFFFF', bold: true });
s1.addText('Revenue Impact Analysis — Old vs New Schedule Comparison\nEmivest & Ecoplexus 40MW Cases\nApril 2026', { x: 0.6, y: 4.4, w: 9, h: 0.8, fontSize: 13, color: 'BDC3C7' });

// ---------- SECTION: Tariff Change ----------
const s2 = pptx.addSlide();
s2.background = { color: '1B4F72' };
s2.addText('01', { x: 0.6, y: 1.2, w: 3, h: 1.8, fontSize: 72, color: COLORS.accent, bold: true });
s2.addText('Tariff Change Summary', { x: 0.6, y: 3.2, w: 12, h: 1.0, fontSize: 28, color: 'FFFFFF', bold: true });
footer(s2);

const s3 = pptx.addSlide();
titleBar(s3, 'Tariff Change Summary');
s3.addText('Vietnam TOU schedule effective April 22, 2026', { x: 0.5, y: 1.05, w: 12.3, h: 0.4, fontSize: 11, color: COLORS.muted });
const tariffTable = [
  [{ text: 'Attribute', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Old (≤ Apr 21)', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'New (≥ Apr 22)', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } }],
  ['Off-Peak (Mon–Sat)', '22:00–04:00', '00:00–06:00'],
  ['Normal (Mon–Sat)', '04:00–09:30, 11:30–17:00, 20:00–22:00', '06:00–17:30, 22:30–24:00'],
  ['Peak (Mon–Sat)', '09:30–11:30 and 17:00–20:00', '17:30–22:30'],
  ['Sunday', 'Normal 04:00–22:00 / Off-Peak 22:00–04:00', 'Normal 06:00–24:00 / Off-Peak 00:00–06:00'],
  ['BESS cycles/day', '2 (morning + evening peak)', '1 (evening peak only)']
];
s3.addTable(tariffTable, { x: 0.5, y: 1.5, w: 12.3, fontSize: 11, border: { type: 'solid', color: 'E0E0E0', pt: 0.5 }, rowH: 0.5, valign: 'middle' });
const stats1 = [
  { v: 'Lost', l: 'Morning Peak Solar Uplift' },
  { v: '2→1', l: 'BESS Cycles Per Day' },
  { v: '17:30–22:30', l: 'New Single Peak Block' }
];
stats1.forEach((st, i) => {
  const x = 0.6 + i * 4.2;
  s3.addShape(pptx.ShapeType.roundRect, { x, y: 5.0, w: 3.9, h: 1.2, fill: { color: COLORS.tableHdr }, line: { color: 'D5E8F5', width: 1 }, rectRadius: 0.1 });
  s3.addText(st.v, { x, y: 5.05, w: 3.9, h: 0.6, fontSize: 24, bold: true, color: COLORS.accent, align: 'center' });
  s3.addText(st.l, { x, y: 5.6, w: 3.9, h: 0.4, fontSize: 9, color: COLORS.muted, align: 'center' });
});
footer(s3);

// ---------- SECTION: BESS Dispatch ----------
const s4 = pptx.addSlide();
s4.background = { color: '1B4F72' };
s4.addText('02', { x: 0.6, y: 1.2, w: 3, h: 1.8, fontSize: 72, color: COLORS.accent, bold: true });
s4.addText('BESS Dispatch Impact', { x: 0.6, y: 3.2, w: 12, h: 1.0, fontSize: 28, color: 'FFFFFF', bold: true });
footer(s4);

const s5 = pptx.addSlide();
titleBar(s5, 'BESS Dispatch Impact');
// Left column
s5.addText('Old Schedule (2 Cycles/Day)', { x: 0.5, y: 1.2, w: 5.8, h: 0.4, fontSize: 14, color: COLORS.dark, bold: true });
s5.addText('• Charge: Off-peak 22:00–04:00\n• Peak 1: 09:30–11:30 (morning solar + BESS)\n• Charge 2: Normal 11:30–17:00 (from solar)\n• Peak 2: 17:00–20:00 (evening BESS)', { x: 0.5, y: 1.7, w: 5.8, h: 2.0, fontSize: 12, color: COLORS.text, valign: 'top', paraSpaceAfter: 4 });
// Right column
s5.addText('New Schedule (1 Cycle/Day)', { x: 7.0, y: 1.2, w: 5.8, h: 0.4, fontSize: 14, color: COLORS.dark, bold: true });
s5.addText('• Charge: Off-peak 00:00–06:00 (grid only)\n• Peak: 17:30–22:30 (evening BESS only)\n• Solar (06:00–17:30) now fully Normal hours\n• BESS preserves SOC through afternoon', { x: 7.0, y: 1.7, w: 5.8, h: 2.0, fontSize: 12, color: COLORS.text, valign: 'top', paraSpaceAfter: 4 });
const stats2 = [
  { v: '-50%', l: 'BESS Cycles Per Day' },
  { v: '~5hr', l: 'Peak Solar Overlap Lost' },
  { v: '5hr', l: 'Evening Peak Duration' }
];
stats2.forEach((st, i) => {
  const x = 0.6 + i * 4.2;
  s5.addShape(pptx.ShapeType.roundRect, { x, y: 4.5, w: 3.9, h: 1.4, fill: { color: COLORS.tableHdr }, line: { color: 'D5E8F5', width: 1 }, rectRadius: 0.1 });
  s5.addText(st.v, { x, y: 4.6, w: 3.9, h: 0.7, fontSize: 28, bold: true, color: COLORS.accent, align: 'center' });
  s5.addText(st.l, { x, y: 5.3, w: 3.9, h: 0.4, fontSize: 9, color: COLORS.muted, align: 'center' });
});
footer(s5);

// ---------- SECTION: Emivest ----------
const s6 = pptx.addSlide();
s6.background = { color: '1B4F72' };
s6.addText('03', { x: 0.6, y: 1.2, w: 3, h: 1.8, fontSize: 72, color: COLORS.accent, bold: true });
s6.addText('Emivest Case Results', { x: 0.6, y: 3.2, w: 12, h: 1.0, fontSize: 28, color: 'FFFFFF', bold: true });
footer(s6);

const s7 = pptx.addSlide();
titleBar(s7, 'Emivest — Revenue Impact (All PPA Options)');
s7.addText('Old baseline revenue: $562,144', { x: 0.5, y: 1.05, w: 12.3, h: 0.3, fontSize: 10, color: COLORS.muted });
const emivestTable = [
  [{ text: 'PPA Option', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'New Revenue', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Delta $', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Delta %', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Δ IRR', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Δ NPV', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } }],
  ['Bundled Discount', '$498,839', '-$63,305', '-11.3%', '-3.25pp', '-$659,445'],
  ['Separate PV+BESS', '$525,804', '-$36,341', '-6.5%', '-1.70pp', '-$323,683'],
  ['DPPA (CfD)', '$542,467', '-$19,677', '-3.5%', '-0.76pp', '-$116,188'],
  ['Fixed EVN PPA', '$556,068', '-$6,076', '-1.1%', '+0.00pp', '+$53,174']
];
s7.addTable(emivestTable, { x: 0.5, y: 1.5, w: 12.3, fontSize: 11, border: { type: 'solid', color: 'E0E0E0', pt: 0.5 }, rowH: 0.45, valign: 'middle' });
const stats3 = [
  { v: '-$63,305', l: 'Worst Hit (Bundled Discount)', c: COLORS.red },
  { v: '-$6,076', l: 'Best Preserved (Fixed PPA)', c: COLORS.accent }
];
stats3.forEach((st, i) => {
  const x = 0.6 + i * 4.2;
  s7.addShape(pptx.ShapeType.roundRect, { x, y: 4.8, w: 3.9, h: 1.2, fill: { color: COLORS.tableHdr }, line: { color: 'D5E8F5', width: 1 }, rectRadius: 0.1 });
  s7.addText(st.v, { x, y: 4.9, w: 3.9, h: 0.6, fontSize: 24, bold: true, color: st.c, align: 'center' });
  s7.addText(st.l, { x, y: 5.45, w: 3.9, h: 0.4, fontSize: 9, color: COLORS.muted, align: 'center' });
});
footer(s7);

// ---------- SECTION: Revenue Decomposition ----------
const s8 = pptx.addSlide();
titleBar(s8, 'Emivest — Revenue Decomposition by Driver');
s8.addText('Bundled Discount option — root cause breakdown', { x: 0.5, y: 1.05, w: 12.3, h: 0.3, fontSize: 10, color: COLORS.muted });
const decompTable = [
  [{ text: 'Driver', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Impact', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Explanation', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } }],
  ['Loss of morning peak uplift', '-$65,343', 'Solar kWh (09:30–11:30) now earns Normal rate'],
  ['BESS cycle reduction', '-$32,609', 'Single cycle halves BESS arbitrage revenue'],
  ['Shifted peak window (timing)', '+$34,640', 'Later peak extends discharge into higher-load hours'],
  ['Off-peak rate changes', '+$7', 'Minimal effect due to low off-peak consumption']
];
s8.addTable(decompTable, { x: 0.5, y: 1.5, w: 12.3, fontSize: 11, border: { type: 'solid', color: 'E0E0E0', pt: 0.5 }, rowH: 0.5, valign: 'middle' });
footer(s8);

// ---------- SECTION: Ecoplexus ----------
const s9 = pptx.addSlide();
s9.background = { color: '1B4F72' };
s9.addText('04', { x: 0.6, y: 1.2, w: 3, h: 1.8, fontSize: 72, color: COLORS.accent, bold: true });
s9.addText('Ecoplexus 40MW Results', { x: 0.6, y: 3.2, w: 12, h: 1.0, fontSize: 28, color: 'FFFFFF', bold: true });
footer(s9);

const s10 = pptx.addSlide();
titleBar(s10, 'Ecoplexus 40MW — DPPA (CfD) Impact');
const ecoTable = [
  [{ text: 'Metric', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Old Tariff', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'New Tariff', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Delta', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } }],
  ['Year 1 Revenue', '$5,543,642', '$6,891,647', '+$1,348,006 (+24.3%)'],
  ['Project IRR', '6.26%', '9.31%', '+3.06 pp'],
  ['Equity IRR', '5.71%', '8.70%', '+2.99 pp'],
  ['NPV', '$6,009,427', '$17,808,162', '+$11,798,735 (+196%)'],
  ['Min DSCR', '1.28x', '1.27x', '-0.01x (stable)'],
  ['Year 1 DPPA Rev', '$2,547,079', '$3,166,432', '+$619,353 (+24.3%)'],
  ['Year 1 Grid Savings', '$2,996,563', '$3,725,215', '+$728,652 (+24.3%)']
];
s10.addTable(ecoTable, { x: 0.5, y: 1.2, w: 12.3, fontSize: 11, border: { type: 'solid', color: 'E0E0E0', pt: 0.5 }, rowH: 0.4, valign: 'middle' });
const stats4 = [
  { v: '9.31%', l: 'New Project IRR' },
  { v: '+$11.8M', l: 'NPV Gain' },
  { v: '+24.3%', l: 'Revenue Uplift' }
];
stats4.forEach((st, i) => {
  const x = 0.6 + i * 4.2;
  s10.addShape(pptx.ShapeType.roundRect, { x, y: 5.0, w: 3.9, h: 1.2, fill: { color: COLORS.tableHdr }, line: { color: 'D5E8F5', width: 1 }, rectRadius: 0.1 });
  s10.addText(st.v, { x, y: 5.1, w: 3.9, h: 0.6, fontSize: 24, bold: true, color: COLORS.accent, align: 'center' });
  s10.addText(st.l, { x, y: 5.65, w: 3.9, h: 0.4, fontSize: 9, color: COLORS.muted, align: 'center' });
});
s10.addText('Why Ecoplexus gains: Larger solar+BESS system benefits from later peak timing (17:30–22:30) with higher evening load coincidence. DPPA CfD settlement amplifies the tariff spread.', { x: 0.5, y: 6.2, w: 12.3, h: 0.5, fontSize: 9, color: COLORS.muted });
footer(s10);

// ---------- SECTION: Mitigations ----------
const s11 = pptx.addSlide();
s11.background = { color: '1B4F72' };
s11.addText('05', { x: 0.6, y: 1.2, w: 3, h: 1.8, fontSize: 72, color: COLORS.accent, bold: true });
s11.addText('Mitigations & Next Steps', { x: 0.6, y: 3.2, w: 12, h: 1.0, fontSize: 28, color: 'FFFFFF', bold: true });
footer(s11);

const s12 = pptx.addSlide();
titleBar(s12, 'Recommended Mitigations');
s12.addText(
  'R  Re-price PPA offers — Adjust bundled and DPPA offers against the lower evening-only uplift.\n   Solar no longer touches any peak block.\n\n' +
  'D  Re-tune BESS dispatch — Focus on evening peak capture. Preserve SOC during late-afternoon standard hours.\n\n' +
  'C  Review discount assumptions — Separate PV-heavy vs BESS-heavy product stacks.\n   The tariff shift impacts them differently.\n\n' +
  'K  Maintain both tariff baselines — Keep old/new regression artifacts until 2026 schedule\n   becomes the production default for all project types.\n\n' +
  'S  Sensitivity analysis — Evaluate strike price and discount adjustments under the new schedule.',
  { x: 0.5, y: 1.3, w: 12.3, h: 5.0, fontSize: 12, color: COLORS.text, valign: 'top', paraSpaceAfter: 6 }
);
footer(s12);

// ---------- SUMMARY ----------
const s13 = pptx.addSlide();
titleBar(s13, 'Summary & Key Takeaways');
const summaryTable = [
  [{ text: 'Metric', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Emivest (Worst)', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Emivest (Best)', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } },
   { text: 'Ecoplexus', options: { bold: true, fill: { color: COLORS.tableHdr }, color: COLORS.dark } }],
  ['Revenue Delta', '-$63,305 (-11.3%)', '-$6,076 (-1.1%)', '+$1,348,006 (+24.3%)'],
  ['Project IRR Delta', '-3.25 pp', '+0.00 pp', '+3.06 pp'],
  ['NPV Delta', '-$659,445', '+$53,174', '+$11,798,735'],
  ['DSCR Impact', '1.96x → 1.64x', '1.96x → 1.93x', '1.28x → 1.27x']
];
s13.addTable(summaryTable, { x: 0.5, y: 1.2, w: 12.3, fontSize: 11, border: { type: 'solid', color: 'E0E0E0', pt: 0.5 }, rowH: 0.45, valign: 'middle' });
s13.addText(
  'Key Messages:\n' +
  '• Small C&I (Emivest) is negatively impacted — hardest for Bundled Discount (-11.3% revenue)\n' +
  '• Large utility-scale (Ecoplexus) benefits significantly (+24% revenue, +3pp IRR)\n' +
  '• Fixed EVN PPA is the most resilient option for Emivest under the new schedule\n' +
  '• BESS dispatch strategy must be updated — the old 2-cycle pattern is no longer optimal',
  { x: 0.5, y: 4.0, w: 12.3, h: 2.5, fontSize: 12, color: COLORS.text, valign: 'top', paraSpaceAfter: 4 }
);
footer(s13);

pptx.writeFile({ fileName: 'results/vietnam_tou2026_presentation.pptx' })
  .then(() => console.log('PPTX created: results/vietnam_tou2026_presentation.pptx'))
  .catch(err => console.error('Error:', err));
