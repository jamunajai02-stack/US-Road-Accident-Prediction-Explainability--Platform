import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const LoadingSkeleton: React.FC<{ rows?: number; height?: string }> = ({
  rows = 4,
  height = 'h-12',
}) => {
  return (
    <div className="space-y-3 animate-pulse w-full">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={`bg-slate-200 dark:bg-slate-800 rounded-xl ${height} w-full`}
        />
      ))}
    </div>
  );
};

export const ErrorBanner: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Failed to load data', message, onRetry }) => {
  return (
    <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 flex items-start space-x-3">
      <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold">{title}</h4>
        <p className="text-xs text-rose-700 dark:text-rose-300 mt-0.5">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 inline-flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-lg bg-rose-100 dark:bg-rose-900/60 hover:bg-rose-200 dark:hover:bg-rose-900 text-rose-900 dark:text-rose-100 transition"
          >
            <RefreshCw className="w-3 h-3 mr-1" /> Retry Request
          </button>
        )}
      </div>
    </div>
  );
};

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => {
  return (
    <div className="py-12 px-4 text-center flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
      {icon && <div className="p-3 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 mb-3">{icon}</div>}
      <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mt-1">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
