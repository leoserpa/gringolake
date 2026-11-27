import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildCsvContent,
  csvEscape,
  formatDateBR,
  formatDayMonthBR,
  formatFlowBrl,
  formatPctSigned,
  formatPoints,
  signClass,
  toArray,
  toIsoDate,
} from '../components/formatters.js';

test('toArray normalizes arrays, iterables, query-like objects, and nullish inputs', () => {
  assert.deepEqual(toArray(null), []);
  assert.deepEqual(toArray(undefined), []);
  assert.deepEqual(toArray([1, 2]), [1, 2]);
  assert.deepEqual(toArray(new Set(['a', 'b'])), ['a', 'b']);
  assert.deepEqual(toArray({ toArray: () => [{ id: 1 }] }), [{ id: 1 }]);
});

test('toIsoDate and Brazilian date formatters handle ISO strings, Dates, and invalid inputs', () => {
  assert.equal(toIsoDate('2026-11-23T00:00:00Z'), '2026-11-23');
  assert.equal(toIsoDate(new Date('2026-11-23T12:00:00Z')), '2026-11-23');
  assert.equal(toIsoDate(null), null);
  assert.equal(toIsoDate('not-a-date'), null);

  assert.equal(formatDateBR('2026-11-23'), '23/11/2026');
  assert.equal(formatDateBR(null), '—');
  assert.equal(formatDayMonthBR('2026-11-23'), '23/11');
  assert.equal(formatDayMonthBR(''), '');
});

test('formatFlowBrl applies ADR-007 adaptive mi/bi scale across k, mi, and bi inputs', () => {
  // Zero threshold (< 0.05 mi)
  assert.equal(formatFlowBrl(0, { inputUnit: 'mi' }), 'R$ 0');
  assert.equal(formatFlowBrl(0.04, { inputUnit: 'mi' }), 'R$ 0');
  assert.equal(formatFlowBrl(-0.04, { inputUnit: 'mi' }), 'R$ 0');
  assert.equal(formatFlowBrl(0.01, { inputUnit: 'mi', prefix: '', compactAxis: true }), '0');

  // Millions (< 999.95 mi)
  assert.equal(formatFlowBrl(449.5, { inputUnit: 'mi' }), '+R$ 449,5 mi');
  assert.equal(formatFlowBrl(-104.9, { inputUnit: 'mi' }), '-R$ 104,9 mi');
  assert.equal(formatFlowBrl(999.94, { inputUnit: 'mi' }), '+R$ 999,9 mi');
  assert.equal(formatFlowBrl(449.5, { inputUnit: 'mi', signed: false }), 'R$ 449,5 mi');

  // Billions (>= 999.95 mi)
  assert.equal(formatFlowBrl(999.95, { inputUnit: 'mi' }), '+R$ 1,00 bi');
  assert.equal(formatFlowBrl(-1500, { inputUnit: 'mi' }), '-R$ 1,50 bi');
  assert.equal(formatFlowBrl(16.97, { inputUnit: 'bi' }), '+R$ 16,97 bi');
  assert.equal(formatFlowBrl(0.45, { inputUnit: 'bi' }), '+R$ 450,0 mi');
  assert.equal(formatFlowBrl(-1490000, { inputUnit: 'k' }), '-R$ 1,49 bi');
  assert.equal(formatFlowBrl(88000, { inputUnit: 'k' }), '+R$ 88,0 mi');

  // Compact axis mode preserves exact HUD/table decimals on data values, while showing integer ticks cleanly
  assert.equal(formatFlowBrl(-104.92, { inputUnit: 'mi', compactAxis: true }), '-R$ 104,9 mi');
  assert.equal(formatFlowBrl(322.5, { inputUnit: 'mi', prefix: '', compactAxis: true }), '+322,5 mi');
  assert.equal(formatFlowBrl(-1.499871, { inputUnit: 'bi', prefix: '', compactAxis: true }), '-1,50 bi');
  assert.equal(formatFlowBrl(1.5, { inputUnit: 'bi', prefix: '', compactAxis: true }), '+1,50 bi');
  assert.equal(formatFlowBrl(2, { inputUnit: 'bi', prefix: 'R$ ', compactAxis: true }), '+R$ 2 bi');
  assert.equal(formatFlowBrl(250, { inputUnit: 'mi', prefix: '', compactAxis: true }), '+250 mi');
  assert.equal(formatFlowBrl(42.5, { inputUnit: 'mi', prefix: '', compactAxis: true }), '+42,5 mi');

  // Nullish / invalid
  assert.equal(formatFlowBrl(null), '—');
  assert.equal(formatFlowBrl(undefined, { emptyFallback: '' }), '');
});

test('formatPctSigned normalizes near-zero values and formats pt-BR percentages', () => {
  assert.equal(formatPctSigned(34.13), '+34,13%');
  assert.equal(formatPctSigned(-9.35), '-9,35%');
  assert.equal(formatPctSigned(0.004), '0,00%');
  assert.equal(formatPctSigned(-0.004), '0,00%');
  assert.equal(formatPctSigned(0, { compactAxis: true }), '0%');
  assert.equal(formatPctSigned(-0.95, { compactAxis: true }), '-0,95%');
  assert.equal(formatPctSigned(-3.4, { compactAxis: true }), '-3,40%');
  assert.equal(formatPctSigned(-8, { compactAxis: true }), '-8%');
  assert.equal(formatPctSigned(null), '—');
});

test('formatPoints and signClass follow Atelier Graphite table conventions', () => {
  assert.equal(formatPoints(166685.4), '166.685 pts');
  assert.equal(formatPoints(166685.4, { withUnit: false }), '166.685');
  assert.equal(formatPoints(null), '—');

  assert.equal(signClass(1.2), 'pos');
  assert.equal(signClass(-0.5), 'neg');
  assert.equal(signClass(0), 'neutral');
  assert.equal(signClass(0.04, { threshold: 0.05 }), 'neutral');
  assert.equal(signClass(null, { neutralClass: 'muted' }), 'muted');
});

test('csvEscape and buildCsvContent emit UTF-8 BOM and properly quote special characters', () => {
  assert.equal(csvEscape('plain'), 'plain');
  assert.equal(csvEscape('a,b'), '"a,b"');
  assert.equal(csvEscape('he said "ok"'), '"he said ""ok"""');
  assert.equal(csvEscape(null), '');

  const csv = buildCsvContent(
    ['ano', 'nota'],
    [
      [2026, 'Estrangeiro, B3'],
      [2025, 'Sem "aspas"'],
    ]
  );
  assert.equal(csv, '\uFEFFano,nota\n2026,"Estrangeiro, B3"\n2025,"Sem ""aspas"""');
});
