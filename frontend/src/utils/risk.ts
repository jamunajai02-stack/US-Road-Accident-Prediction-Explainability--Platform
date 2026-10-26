import { RiskBand } from '../api/types';

export function formatRiskPercentage(risk: number | undefined | null): string {
  if (risk === undefined || risk === null || isNaN(risk)) return '0.0%';
  return `${(risk * 100).toFixed(1)}%`;
}

export function getRiskBand(risk: number): RiskBand {
  if (risk < 0.3) return 'low';
  if (risk < 0.6) return 'moderate';
  if (risk < 0.8) return 'high';
  return 'severe';
}

export function getRiskColorHex(band: RiskBand): string {
  switch (band) {
    case 'low':
      return '#10B981'; // green
    case 'moderate':
      return '#F59E0B'; // amber
    case 'high':
      return '#F97316'; // orange
    case 'severe':
      return '#EF4444'; // red
    default:
      return '#94A3B8';
  }
}

export function getRiskBadgeClasses(band: RiskBand): {
  bg: string;
  text: string;
  border: string;
  dot: string;
} {
  switch (band) {
    case 'low':
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-950/40',
        text: 'text-emerald-700 dark:text-emerald-300',
        border: 'border-emerald-200 dark:border-emerald-800/60',
        dot: 'bg-emerald-500',
      };
    case 'moderate':
      return {
        bg: 'bg-amber-50 dark:bg-amber-950/40',
        text: 'text-amber-700 dark:text-amber-300',
        border: 'border-amber-200 dark:border-amber-800/60',
        dot: 'bg-amber-500',
      };
    case 'high':
      return {
        bg: 'bg-orange-50 dark:bg-orange-950/40',
        text: 'text-orange-700 dark:text-orange-300',
        border: 'border-orange-200 dark:border-orange-800/60',
        dot: 'bg-orange-500',
      };
    case 'severe':
      return {
        bg: 'bg-rose-50 dark:bg-rose-950/40',
        text: 'text-rose-700 dark:text-rose-300',
        border: 'border-rose-200 dark:border-rose-800/60',
        dot: 'bg-rose-500 animate-pulse',
      };
  }
}

export function getSafetyStatusClasses(status: string): {
  bg: string;
  text: string;
  border: string;
  iconBg: string;
} {
  const norm = status?.toUpperCase();
  if (norm === 'SAFE') {
    return {
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
      text: 'text-emerald-800 dark:text-emerald-200',
      border: 'border-emerald-300 dark:border-emerald-800',
      iconBg: 'bg-emerald-500 text-white',
    };
  }
  if (norm === 'CAUTION') {
    return {
      bg: 'bg-amber-50 dark:bg-amber-950/30',
      text: 'text-amber-800 dark:text-amber-200',
      border: 'border-amber-300 dark:border-amber-800',
      iconBg: 'bg-amber-500 text-white',
    };
  }
  return {
    bg: 'bg-rose-50 dark:bg-rose-950/30',
    text: 'text-rose-800 dark:text-rose-200',
    border: 'border-rose-300 dark:border-rose-800',
    iconBg: 'bg-rose-500 text-white',
  };
}
