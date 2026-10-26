import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Navbar, ViewType } from './components/common/Navbar';
import { LiveRiskMap } from './views/LiveRiskMap';
import { PredictionsExplorer } from './views/PredictionsExplorer';
import { RouteSafetyCheck } from './views/RouteSafetyCheck';
import { HotspotsExploration } from './views/HotspotsExploration';
import { SystemHealth } from './views/SystemHealth';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('map');
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('theme') === 'dark' || window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [autoPoll, setAutoPoll] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const queryClient = useQueryClient();

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Navigation Header */}
      <Navbar
        currentView={currentView}
        onViewChange={setCurrentView}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        autoPoll={autoPoll}
        onToggleAutoPoll={() => setAutoPoll(!autoPoll)}
        onManualRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Viewport Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentView === 'map' && <LiveRiskMap autoPoll={autoPoll} />}
        {currentView === 'explorer' && <PredictionsExplorer />}
        {currentView === 'route' && <RouteSafetyCheck />}
        {currentView === 'hotspots' && <HotspotsExploration />}
        {currentView === 'health' && <SystemHealth />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 py-4 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            SafeCorridor AI &bull; US Road Accident Prediction & Localized Explainability Platform
          </div>
          <div className="font-mono text-[11px]">
            FastAPI Backend: <span className="text-emerald-600 dark:text-emerald-400 font-semibold">ONLINE (v0.1.0)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
