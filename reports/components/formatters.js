/**
 * Shared formatting, date normalization, and CSV export utilities for GringoLake
 * Evidence.dev components (see ADR-007 for the unified R$ mi / R$ bi scale).
 */

const BR_LOCALE = 'pt-BR';
const MI_TO_BI_THRESHOLD = 999.95;
const ZERO_MI_EPSILON = 0.05;

/**
 * Normalizes plain arrays, Evidence query objects, and iterables to an Array.
 * @param {unknown} input
 * @returns {Array<any>}
 */
export function toArray(input) {
  if (!input) return [];
  if (Array.isArray(input)) return input;
  if (typeof input.toArray === 'function') return input.toArray();
  if (typeof input[Symbol.iterator] === 'function') return Array.from(input);
  return [];
}

/**
 * Normalizes a Date, ISO string, or timestamp into 'YYYY-MM-DD' (or null).
 * @param {unknown} val
 * @returns {string | null}
 */
export function toIsoDate(val) {
  if (val === null || val === undefined || val === '') return null;
  if (typeof val === 'string') {
    const match = val.match(/^(\d{4}-\d{2}-\d{2})/);
    if (match) return match[1];
    const parsed = new Date(val);
    return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
  }
  if (val instanceof Date) {
    return Number.isNaN(val.getTime()) ? null : val.toISOString().slice(0, 10);
  }
  if (typeof val === 'number' && Number.isFinite(val)) {
    const parsed = new Date(val);
    return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString().slice(0, 10);
  }
  return null;
}

/**
 * Formats an ISO date or Date instance as DD/MM/YYYY.
 * @param {unknown} val
 * @param {string} [fallback='—']
 * @returns {string}
 */
export function formatDateBR(val, fallback = '—') {
  if (!val) return fallback;
  const iso = toIsoDate(val);
  if (!iso || iso.length < 10) return typeof val === 'string' ? val : fallback;
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
}

/**
 * Formats an ISO date or Date instance as DD/MM (compact KPI badge date).
 * @param {unknown} val
 * @returns {string}
 */
export function formatDayMonthBR(val) {
  if (!val) return '';
  const iso = toIsoDate(val);
  if (!iso || iso.length < 10) return typeof val === 'string' ? val : '';
  return `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
}

const isExactInteger = (num) => Math.abs(num - Math.round(num)) < 1e-9;

/**
 * Formats monetary flows using GringoLake's adaptive R$ mi / R$ bi scale (ADR-007):
 * - |value_mi| < 0.05  -> "<prefix>0"
 * - |value_mi| >= 999.95 -> billions (2 decimals; compact integer ticks drop trailing zeros)
 * - otherwise -> millions (1 decimal; compact integer ticks drop trailing zeros)
 *
 * @param {unknown} value
 * @param {object} [options]
 * @param {'mi' | 'bi' | 'k'} [options.inputUnit='mi']
 * @param {boolean} [options.signed=true]
 * @param {string} [options.prefix='R$ ']
 * @param {boolean} [options.compactAxis=false]
 * @param {string} [options.emptyFallback='—']
 * @returns {string}
 */
export function formatFlowBrl(
  value,
  {
    inputUnit = 'mi',
    signed = true,
    prefix = 'R$ ',
    compactAxis = false,
    emptyFallback = '—',
  } = {}
) {
  if (value === null || value === undefined || value === '') return emptyFallback;
  const num = Number(value);
  if (!Number.isFinite(num)) return emptyFallback;

  let inMi = num;
  if (inputUnit === 'bi') inMi = num * 1000;
  else if (inputUnit === 'k') inMi = num / 1000;

  const absMi = Math.abs(inMi);
  if (absMi < ZERO_MI_EPSILON) {
    return `${prefix}0`;
  }

  const sign = inMi < 0 ? '-' : signed ? '+' : '';

  if (absMi >= MI_TO_BI_THRESHOLD) {
    const absBi = absMi / 1000;
    const useIntegerTick = compactAxis && isExactInteger(absBi);
    const formatted = absBi.toLocaleString(
      BR_LOCALE,
      useIntegerTick
        ? { minimumFractionDigits: 0, maximumFractionDigits: 0 }
        : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    );
    return `${sign}${prefix}${formatted} bi`;
  }

  const useIntegerTick = compactAxis && isExactInteger(absMi);
  const formatted = absMi.toLocaleString(
    BR_LOCALE,
    useIntegerTick
      ? { minimumFractionDigits: 0, maximumFractionDigits: 0 }
      : { minimumFractionDigits: 1, maximumFractionDigits: 1 }
  );
  return `${sign}${prefix}${formatted} mi`;
}

/**
 * Formats a signed percentage in pt-BR, normalizing tiny noise (< 0.005%) to zero.
 * @param {unknown} value
 * @param {object} [options]
 * @param {boolean} [options.compactAxis=false]
 * @param {string} [options.emptyFallback='—']
 * @returns {string}
 */
export function formatPctSigned(
  value,
  { compactAxis = false, emptyFallback = '—' } = {}
) {
  if (value === null || value === undefined || value === '') return emptyFallback;
  const num = Number(value);
  if (!Number.isFinite(num)) return emptyFallback;

  const normalized = Math.abs(num) < 0.005 ? 0 : num;
  if (normalized === 0 && compactAxis) return '0%';

  const sign = normalized > 0 ? '+' : normalized < 0 ? '-' : '';
  const absNorm = Math.abs(normalized);
  const useIntegerTick = compactAxis && isExactInteger(absNorm);
  const absFormatted = absNorm.toLocaleString(
    BR_LOCALE,
    useIntegerTick
      ? { minimumFractionDigits: 0, maximumFractionDigits: 0 }
      : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
  );
  return `${sign}${absFormatted}%`;
}

/**
 * Formats rounded Ibovespa points in pt-BR.
 * @param {unknown} value
 * @param {object} [options]
 * @param {boolean} [options.withUnit=true]
 * @param {string} [options.emptyFallback='—']
 * @returns {string}
 */
export function formatPoints(
  value,
  { withUnit = true, emptyFallback = '—' } = {}
) {
  if (value === null || value === undefined || value === '') return emptyFallback;
  const num = Number(value);
  if (!Number.isFinite(num)) return emptyFallback;
  const formatted = Math.round(num).toLocaleString(BR_LOCALE);
  return withUnit ? `${formatted} pts` : formatted;
}

/**
 * Returns semantic CSS sign class ('pos' | 'neg' | neutralClass) for Atelier Graphite tables.
 * @param {unknown} value
 * @param {object} [options]
 * @param {number} [options.threshold=0]
 * @param {string} [options.neutralClass='neutral']
 * @returns {string}
 */
export function signClass(value, { threshold = 0, neutralClass = 'neutral' } = {}) {
  if (value === null || value === undefined || value === '') return neutralClass;
  const num = Number(value);
  if (!Number.isFinite(num)) return neutralClass;
  if (num > threshold) return 'pos';
  if (num < -threshold) return 'neg';
  return neutralClass;
}

/**
 * RFC-4180 CSV cell escaping.
 * @param {unknown} value
 * @returns {string}
 */
export function csvEscape(value) {
  const str = value === null || value === undefined ? '' : String(value);
  if (/[",;\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Builds UTF-8 BOM CSV text from header names and a 2D array of row values.
 * @param {string[]} headers
 * @param {Array<Array<unknown>>} rowMatrix
 * @returns {string}
 */
export function buildCsvContent(headers, rowMatrix) {
  const lines = [
    headers.map(csvEscape).join(','),
    ...rowMatrix.map((cells) => cells.map(csvEscape).join(',')),
  ];
  return `\uFEFF${lines.join('\n')}`;
}

/**
 * Triggers a client-side UTF-8 CSV download.
 * @param {string} filename
 * @param {string[]} headers
 * @param {Array<Array<unknown>>} rowMatrix
 */
export function downloadCsv(filename, headers, rowMatrix) {
  if (!rowMatrix.length || typeof document === 'undefined') return;
  const csv = buildCsvContent(headers, rowMatrix);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
