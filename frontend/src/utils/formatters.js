/**
 * Formatting and color utility functions for Sanchaar.
 */

export function formatNumber(num, decimals = 0) {
  if (num === null || num === undefined || isNaN(num)) return '0';
  return Number(num).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatCompactNumber(num) {
  if (num === null || num === undefined || isNaN(num)) return '0';
  return Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(num);
}

export function formatPercentage(num) {
  if (num === null || num === undefined || isNaN(num)) return '0%';
  return `${Number(num) > 0 ? '+' : ''}${Number(num).toFixed(1)}%`;
}

export function formatHour(hour) {
  const h = Number(hour) % 24;
  const period = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 === 0 ? 12 : h % 12;
  return `${displayHour}:00 ${period}`;
}

export function getDemandBadge(level) {
  switch ((level || '').toLowerCase()) {
    case 'low':
      return {
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800',
        dot: 'bg-emerald-500',
        label: 'Low Demand',
      };
    case 'moderate':
      return {
        bg: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800',
        dot: 'bg-blue-500',
        label: 'Moderate',
      };
    case 'high':
      return {
        bg: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800',
        dot: 'bg-amber-500',
        label: 'High Demand',
      };
    case 'very high':
    case 'very_high':
      return {
        bg: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800',
        dot: 'bg-rose-500',
        label: 'Very High (Peak)',
      };
    default:
      return {
        bg: 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
        dot: 'bg-slate-400',
        label: level || 'Normal',
      };
  }
}
