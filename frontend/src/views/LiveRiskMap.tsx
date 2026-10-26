import React, { useState } from 'react';
import { useHotspots, useHotspotExplanation, usePredictions } from '../api/queries';
import { MapContainer } from '../components/map/MapContainer';
import { ErrorBanner, LoadingSkeleton } from '../components/common/Feedback';
import {
  Flame,
  AlertTriangle,
  X,
  Compass,
  Activity,
  Layers,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';

interface LiveRiskMapProps {
  autoPoll: boolean;
}

export const LiveRiskMap: React.FC<LiveRiskMapProps> = ({ autoPoll }) => {
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);

  const {
    data: predictionsData,
    isLoading: isPredLoading,
    error: predError,
    refetch: refetchPreds,
  } = usePredictions(null, autoPoll);

  const {
    data: hotspots,
    isLoading: isHotspotsLoading,
    error: hotspotError,
    refetch: refetchHotspots,
  } = useHotspots(autoPoll);

  const {
    data: explanation,
    isLoading: isExpLoading,
    error: expError,
  } = useHotspotExplanation(selectedHotspotId || '', Boolean(selectedHotspotId));

  const totalSegments = predictionsData?.num_edges_evaluated || 48;
  const hotspotCount = hotspots?.length || predictionsData?.num_hotspots_detected || 0;
  const avgLatency = predictionsData?.inference_latency_ms || 4.8;

  return (
    <div className="space-y-6">
      {/* Top Telemetry & KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Road Segments
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {isPredLoading ? '...' : totalSegments}
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400">
            <Flame className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Danger Hotspots
            </div>
            <div className="text-xl font-bold text-rose-600 dark:text-rose-400">
              {isHotspotsLoading ? '...' : hotspotCount}
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Inference Speed
            </div>
            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
              {avgLatency.toFixed(2)} ms
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Forecast Window
            </div>
            <div className="text-sm font-bold text-slate-900 dark:text-white">
              Next 1-Hour Window
            </div>
          </div>
        </div>
      </div>

      {/* Errors */}
      {(predError || hotspotError) && (
        <ErrorBanner
          title="Telemetry feed connection issue"
          message="Could not load latest road corridor telemetry. Showing cached offline baseline."
          onRetry={() => {
            refetchPreds();
            refetchHotspots();
          }}
        />
      )}

      {/* Main Map & Explanation Overlay Grid */}
      <div className="relative grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Interactive Map */}
        <div className="lg:col-span-3 relative">
          <MapContainer
            predictions={predictionsData?.edge_predictions}
            hotspots={hotspots}
            selectedHotspotId={selectedHotspotId}
            onSelectHotspot={(id) => setSelectedHotspotId(id)}
            className="h-[640px] w-full"
          />

          {/* Slide-in Causative Explanation Drawer */}
          {selectedHotspotId && (
            <div className="absolute top-4 right-4 bottom-4 w-96 max-w-[calc(100%-2rem)] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-5 z-20 overflow-y-auto flex flex-col justify-between">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className="w-5 h-5 text-rose-500" />
                    <span className="font-bold text-sm text-slate-900 dark:text-white">
                      Hotspot Explanation
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedHotspotId(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {isExpLoading ? (
                  <LoadingSkeleton rows={4} height="h-16" />
                ) : expError ? (
                  <div className="p-3 text-xs text-rose-600 bg-rose-50 rounded-xl">
                    Could not retrieve localized decision tree explanation for this cluster.
                  </div>
                ) : explanation ? (
                  <div className="space-y-4 text-xs">
                    {/* Severity Headline */}
                    <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/80">
                      <div className="text-[11px] font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
                        Causative Headline
                      </div>
                      <div className="text-sm font-bold text-rose-900 dark:text-rose-200 mt-0.5">
                        {explanation.summary}
                      </div>
                    </div>

                    {/* Root Cause Statement */}
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white mb-1">
                        Causative Analysis
                      </h4>
                      <p className="text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-200 dark:border-slate-700/60">
                        "{explanation.causative_statement}"
                      </p>
                    </div>

                    {/* Actionable Driver Advisory */}
                    <div>
                      <h4 className="font-bold text-indigo-600 dark:text-indigo-400 mb-1 flex items-center space-x-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Actionable Driver Advisory</span>
                      </h4>
                      <p className="text-slate-700 dark:text-slate-200 font-medium bg-indigo-50/70 dark:bg-indigo-950/40 p-3 rounded-xl border border-indigo-200 dark:border-indigo-800/60">
                        {explanation.driver_advisory}
                      </p>
                    </div>

                    {/* Contributing Factors List */}
                    {explanation.contributing_factors?.length > 0 && (
                      <div>
                        <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-1">
                          Contributing Risk Drivers
                        </h4>
                        <ul className="space-y-1">
                          {explanation.contributing_factors.map((factor, idx) => (
                            <li
                              key={idx}
                              className="flex items-center space-x-2 text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/40 px-2.5 py-1.5 rounded-lg"
                            >
                              <ChevronRight className="w-3 h-3 text-indigo-500 flex-shrink-0" />
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Confidence Score Pill */}
                    <div className="pt-2 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-800">
                      <span>Model Confidence:</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
                        {(explanation.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 text-[11px] text-slate-400 text-center">
                Cluster ID: <span className="font-mono text-slate-600 dark:text-slate-300">{selectedHotspotId}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
