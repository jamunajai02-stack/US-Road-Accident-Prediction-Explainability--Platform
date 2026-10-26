import React from 'react';
import {
  MapPin,
  Table,
  Navigation,
  Flame,
  Activity,
  RefreshCw,
  Sun,
  Moon,
  ShieldCheck,
} from 'lucide-react';
import { useSystemHealth } from '../../api/queries';

export type ViewType = 'map' | 'explorer' | 'route' | 'hotspots' | 'health';

interface NavbarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
  autoPoll: boolean;
  onToggleAutoPoll: () => void;
  onManualRefresh: () => void;
  isRefreshing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onViewChange,
  isDarkMode,
  onToggleDarkMode,
  autoPoll,
  onToggleAutoPoll,
  onManualRefresh,
  isRefreshing,
}) => {
  const { data: health } = useSystemHealth();

  const navItems: { id: ViewType; label: string; icon: React.ReactNode }[] = [
    { id: 'map', label: 'Risk Map', icon: <MapPin className="w-4 h-4" /> },
    { id: 'explorer', label: 'Predictions Explorer', icon: <Table className="w-4 h-4" /> },
    { id: 'route', label: 'Route Safety Check', icon: <Navigation className="w-4 h-4" /> },
    { id: 'hotspots', label: 'Danger Hotspots', icon: <Flame className="w-4 h-4" /> },
    { id: 'health', label: 'System Trust', icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onViewChange('map')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 via-indigo-600 to-rose-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-base font-bold bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 dark:from-white dark:via-slate-200 dark:to-indigo-200 bg-clip-text text-transparent">
                SafeCorridor AI
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                US Accident Predictor
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? 'bg-slate-900 text-white dark:bg-indigo-600 dark:text-white shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Controls & Telemetry Badge */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* 60s Refresh Polling Indicator */}
            <div className="hidden lg:flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <span className={`w-2 h-2 rounded-full ${autoPoll ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
              <span>{autoPoll ? 'Updated every 60s' : 'Auto-update paused'}</span>
              <button
                onClick={onToggleAutoPoll}
                title={autoPoll ? 'Pause 60s updates' : 'Enable 60s updates'}
                className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold underline hover:no-underline ml-1"
              >
                {autoPoll ? 'Pause' : 'Enable'}
              </button>
            </div>

            {/* Manual Refresh button */}
            <button
              onClick={onManualRefresh}
              disabled={isRefreshing}
              title="Refresh telemetry"
              className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
            </button>

            {/* System Status Pill */}
            <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>{health?.status === 'HEALTHY' ? 'API Online' : 'Connecting...'}</span>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={onToggleDarkMode}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              aria-label="Toggle theme"
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden overflow-x-auto py-2 border-t border-slate-200 dark:border-slate-800 space-x-1 no-scrollbar">
          {navItems.map((item) => {
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  active
                    ? 'bg-slate-900 text-white dark:bg-indigo-600 dark:text-white'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
