import React, { useState } from 'react';
import { useRouteCheck } from '../api/queries';
import { MapContainer } from '../components/map/MapContainer';
import { ErrorBanner } from '../components/common/Feedback';
import {
  Navigation,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Milestone,
  CheckCircle2,
  TrendingDown,
  Flame,
} from 'lucide-react';
import { Waypoint } from '../api/types';
import { getSafetyStatusClasses, formatRiskPercentage } from '../utils/risk';

export const RouteSafetyCheck: React.FC = () => {
  const [origin, setOrigin] = useState<Waypoint>({ latitude: 37.7749, longitude: -122.4194 });
  const [destination, setDestination] = useState<Waypoint>({ latitude: 37.7989, longitude: -122.395 });
  const [isPicking, setIsPicking] = useState<'origin' | 'destination' | null>(null);

  const { mutate: checkRoute, data: routeResult, isPending, error } = useRouteCheck();

  const handleRunCheck = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    checkRoute({
      route_id: `trip_${Date.now().toString(36)}`,
      origin,
      destination,
      departure_time: new Date().toISOString(),
    });
  };

  const handleMapClick = (waypoint: Waypoint) => {
    if (isPicking === 'origin') {
      setOrigin(waypoint);
      setIsPicking(null);
    } else if (isPicking === 'destination') {
      setDestination(waypoint);
      setIsPicking(null);
    }
  };

  const activeAlert = routeResult?.active_alerts?.[0];
  const detour = activeAlert?.suggested_detour;
  const statusStyles = routeResult ? getSafetyStatusClasses(routeResult.overall_safety_status) : null;

  return (
    <div className="space-y-6">
      {/* Route Form & Header */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-700">
          <div>
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 mb-2">
              <Navigation className="w-3.5 h-3.5" />
              <span>Valhalla Detour & Hazard Interception Engine</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Trip Safety & Hazard Avoidance Check
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Enter origin and destination coordinates (or click on the map) to evaluate forward accident risks and discover optimized detours.
            </p>
          </div>

          <button
            onClick={() => handleRunCheck()}
            disabled={isPending}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-semibold text-xs shadow-md shadow-indigo-500/20 transition flex items-center justify-center space-x-2 disabled:opacity-50 flex-shrink-0"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{isPending ? 'Evaluating Trip...' : 'Check Route Safety'}</span>
          </button>
        </div>

        {/* Origin / Destination Input Form */}
        <form onSubmit={handleRunCheck} className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
          {/* Origin Card */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
                <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                  A
                </span>
                <span>Origin Waypoint</span>
              </span>
              <button
                type="button"
                onClick={() => setIsPicking(isPicking === 'origin' ? null : 'origin')}
                className={`text-xs px-2.5 py-1 rounded-lg font-medium border transition ${
                  isPicking === 'origin'
                    ? 'bg-blue-600 text-white border-blue-600 animate-pulse'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                }`}
              >
                {isPicking === 'origin' ? 'Click on Map...' : 'Pick on Map'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={origin.latitude}
                  onChange={(e) => setOrigin({ ...origin, latitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs dark:text-white"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={origin.longitude}
                  onChange={(e) => setOrigin({ ...origin, longitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs dark:text-white"
                />
              </div>
            </div>
          </div>

          {/* Destination Card */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
                <span className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold">
                  B
                </span>
                <span>Destination Waypoint</span>
              </span>
              <button
                type="button"
                onClick={() => setIsPicking(isPicking === 'destination' ? null : 'destination')}
                className={`text-xs px-2.5 py-1 rounded-lg font-medium border transition ${
                  isPicking === 'destination'
                    ? 'bg-emerald-600 text-white border-emerald-600 animate-pulse'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                }`}
              >
                {isPicking === 'destination' ? 'Click on Map...' : 'Pick on Map'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={destination.latitude}
                  onChange={(e) => setDestination({ ...destination, latitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs dark:text-white"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-0.5">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={destination.longitude}
                  onChange={(e) => setDestination({ ...destination, longitude: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs dark:text-white"
                />
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Error state */}
      {error && (
        <ErrorBanner
          title="Route Evaluation Error"
          message={error instanceof Error ? error.message : 'Failed to query route safety check.'}
          onRetry={() => handleRunCheck()}
        />
      )}

      {/* Safety Status Banner */}
      {routeResult && statusStyles && (
        <div
          className={`p-5 rounded-2xl border ${statusStyles.bg} ${statusStyles.border} shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4 animate-in fade-in duration-300`}
        >
          <div className="flex items-center space-x-3.5">
            <div className={`p-3 rounded-xl ${statusStyles.iconBg}`}>
              {routeResult.overall_safety_status === 'SAFE' ? (
                <ShieldCheck className="w-6 h-6" />
              ) : routeResult.overall_safety_status === 'CAUTION' ? (
                <AlertTriangle className="w-6 h-6" />
              ) : (
                <ShieldAlert className="w-6 h-6 animate-bounce" />
              )}
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider opacity-75">
                Route Safety Assessment
              </div>
              <div className="text-lg font-black tracking-tight flex items-center space-x-2">
                <span>STATUS: {routeResult.overall_safety_status}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-right">
            <div>
              <div className="text-xs opacity-75">Max Corridor Risk</div>
              <div className="text-2xl font-black font-mono">
                {formatRiskPercentage(routeResult.max_risk_score)}
              </div>
            </div>
            <div>
              <div className="text-xs opacity-75">Alerts Triggered</div>
              <div className="text-2xl font-black font-mono">
                {routeResult.active_alerts?.length || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Alert & Detour Comparison Grid */}
      {activeAlert && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Causative Alert Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-rose-200 dark:border-rose-900/60 shadow-sm space-y-3.5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-700">
              <span className="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center space-x-1.5">
                <Flame className="w-4 h-4 animate-pulse" />
                <span>ACTIVE HAZARD ALERT [{activeAlert.alert_id}]</span>
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Peak Risk: {(activeAlert.max_risk_probability * 100).toFixed(1)}%
              </span>
            </div>

            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              {activeAlert.explanation?.summary}
            </h3>

            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
              {activeAlert.explanation?.causative_statement}
            </p>

            <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-xs">
              <div className="font-semibold text-indigo-700 dark:text-indigo-300 mb-0.5">
                Recommended Driver Action:
              </div>
              <div className="text-slate-700 dark:text-slate-300 font-medium">
                {activeAlert.explanation?.driver_advisory}
              </div>
            </div>
          </div>

          {/* Recommended Detour Card */}
          {detour && (
            <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/30 via-slate-900 to-slate-900 text-white border border-emerald-800/60 shadow-md space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-700">
                <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>RECOMMENDED SAFE DETOUR</span>
                </span>
                <span className="text-[11px] font-mono text-emerald-300">
                  ID: {detour.detour_id}
                </span>
              </div>

              {/* Big KPI Metric */}
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                <div>
                  <div className="text-[11px] text-emerald-300 font-semibold uppercase tracking-wider">
                    Accident Risk Reduction
                  </div>
                  <div className="text-3xl font-black text-emerald-400 font-mono mt-0.5 flex items-center space-x-1">
                    <TrendingDown className="w-7 h-7" />
                    <span>-{detour.risk_reduction_pct.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="text-right text-xs space-y-1">
                  <div className="flex items-center space-x-1 text-slate-300">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    <span>+{detour.additional_time_minutes} min</span>
                  </div>
                  <div className="flex items-center space-x-1 text-slate-300">
                    <Milestone className="w-3.5 h-3.5 text-blue-400" />
                    <span>+{detour.additional_distance_km} km</span>
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-300">
                This alternate detour bypasses high-risk segments (<span className="font-mono text-rose-400">{activeAlert.affected_edge_ids?.join(', ')}</span>) with heavy rainfall and severe curves while adding only minor travel delay.
              </div>
            </div>
          )}
        </div>
      )}

      {/* Map Rendering Primary vs Detour Routes */}
      <div className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm">
        <MapContainer
          originWaypoint={origin}
          destinationWaypoint={destination}
          primaryRouteWkt={routeResult?.recommended_route_geometry}
          detourRouteWkt={detour?.geometry_polyline}
          onMapClickWaypoint={handleMapClick}
          isPickingWaypoint={isPicking}
          className="h-[520px] w-full"
        />
      </div>
    </div>
  );
};
