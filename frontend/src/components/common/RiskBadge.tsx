import React from 'react';
import { RiskBand } from '../../api/types';
import { getRiskBadgeClasses } from '../../utils/risk';

interface RiskBadgeProps {
  band: RiskBand;
  score?: number;
  showDot?: boolean;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  band,
  score,
  showDot = true,
  className = '',
}) => {
  const styles = getRiskBadgeClasses(band);

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles.bg} ${styles.text} ${styles.border} ${className}`}
    >
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />}
      <span className="capitalize">{band}</span>
      {score !== undefined && (
        <span className="font-mono text-[11px] opacity-80">
          ({(score * 100).toFixed(1)}%)
        </span>
      )}
    </span>
  );
};
