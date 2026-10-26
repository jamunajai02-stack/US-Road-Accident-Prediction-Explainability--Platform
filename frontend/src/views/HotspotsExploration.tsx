import React, { useState } from 'react';
import { useHotspots, useHotspotExplanation, useSystemMetrics } from '../api/queries';
import { LoadingSkeleton, ErrorBanner, EmptyState } from '../components/common/Feedback';
import {
  Flame,
  ShieldAlert,
  AlertTriangle,
  ChevronRight,
  Info,
  Layers,
  MapPin,
} from 'lucide-react';
import { formatRiskPercentage } from '../utils/risk';

export const HotspotsExploration: React.FC = () => {
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(null);

  const { data: hotspots, isLoading, error, refetch } = useHotspots();
  const { data: metrics } = useSystemMetrics();

  const {
    data: explanation,
    isLoading: isExpLoading,
  } = useHotspotExplanation(selectedClusterId || '', Boolean(selectedClusterId));

  const cutoffPct = metrics ? `${(metrics.hotspot_cutoff * 100).toFixed(0)}%` : '80%';

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 mb-2">
            <Flame className="w-3.5 h-3.5" />
            <span>Phase 4 Localized Micro Decision Tree Explainability</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            Danger Hotspots & Natural Language Explanations
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 max-w-2xl">
            Spatially connected clusters of road segments where calibrated accident probability meets or exceeds the alert threshold (currently <b>{cutoffPct}</b>). Micro decision trees are fitted locally per cluster to extract causative factors.
          </p>
        </div>

        <div className="px-5 py-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-center flex-shrink-0">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Active Hotspots
          </div>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono">
            {hotspots?.length || 0}
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <ErrorBanner
          title="Hotspot Query Error"
          message={error instanceof Error ? error.message : 'Failed to query active danger hotspots.'}
          onRetry={() => refetch()}
        />
      )}

      {/* Loading & Empty states */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <LoadingSkeleton rows={4} height="h-32" />
          <LoadingSkeleton rows={4} height="h-32" />
        </div>
      ) : !hotspots || hotspots.length === 0 ? (
        <EmptyState
          icon={<ShieldAlert className="w-8 h-8 text-emerald-500" />}
          title="No Hotspots Currently Above Alert Threshold"
          description={`All evaluated road network segments are currently operating safely below the ${cutoffPct} risk cutoff.`}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* List of Hotspot Cluster Cards */}
          <div className="lg:col-span-1 space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
              Active Hazard Clusters ({hotspots.length})
            </h3>

            {hotspots.map((hs) => {
              const isSelected = selectedClusterId === hs.cluster_id;
              return (
                <div
                  key={hs.cluster_id}
                  onClick={() => setSelectedClusterId(hs.cluster_id)}
                  className={`p-4 rounded-2xl cursor-pointer border transition-all ${
                    isSelected
                      ? 'bg-rose-50/80 dark:bg-rose-950/40 border-rose-400 dark:border-rose-700 shadow-md ring-2 ring-rose-400/20'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-rose-300 dark:hover:border-rose-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
                      <Flame className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
                      <span>{hs.cluster_id}</span>
                    </span>
                    <span className="text-xs font-mono font-bold text-rose-600 dark:text-rose-400">
                      {formatRiskPercentage(hs.max_risk_probability)}
                    </span>
                  </div>

                  <div className="mt-2 text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                    <div className="flex items-center space-x-1">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      <span>
                        Centroid: ({hs.centroid_latitude.toFixed(4)}, {hs.centroid_longitude.toFixed(4)})
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Layers className="w-3 h-3 text-slate-400" />
                      <span>Affected Segments: {hs.edge_ids.length}</span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-700/60 text-[11px]">
                    <span className="text-slate-400">Avg Risk: {formatRiskPercentage(hs.avg_risk_probability)}</span>
                    <span className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center">
                      Explain <ChevronRight className="w-3 h-3 ml-0.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detailed Natural Language Explanation Breakdown */}
          <div className="lg:col-span-2">
            {selectedClusterId ? (
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700">
                  <div>
                    <span className="text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
                      Causative Decision Tree Explanation
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-0.5">
                      Cluster: {selectedClusterId}
                    </h3>
                  </div>
                  {explanation && (
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 uppercase">Tree Purity / Confidence</div>
                      <div className="text-base font-black text-indigo-600 dark:text-indigo-400 font-mono">
                        {(explanation.confidence_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>

                {isExpLoading ? (
                  <LoadingSkeleton rows={4} height="h-20" />
                ) : explanation ? (
                  <div className="space-y-4">
                    {/* Headline Banner */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-rose-500/10 via-rose-500/5 to-transparent border border-rose-200 dark:border-rose-800/80">
                      <div className="text-xs font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
                        Hazard Category
                      </div>
                      <div className="text-base font-bold text-slate-900 dark:text-white mt-1">
                        {explanation.summary}
                      </div>
                    </div>

                    {/* Causative Statement */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-1.5">
                        Causative Root Cause Analysis
                      </h4>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-700/80 font-medium">
                        "{explanation.causative_statement}"
                      </p>
                    </div>

                    {/* Driver Advisory */}
                    <div>
                      <h4 className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-1.5 flex items-center space-x-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Recommended Driver Safety Advisory</span>
                      </h4>
                      <p className="text-xs text-slate-800 dark:text-slate-200 bg-indigo-50 dark:bg-indigo-950/40 p-4 rounded-xl border border-indigo-200 dark:border-indigo-800 font-medium">
                        {explanation.driver_advisory}
                      </p>
                    </div>

                    {/* Contributing Factors Bullets */}
                    {explanation.contributing_factors?.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-2">
                          Decision Path Factors
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {explanation.contributing_factors.map((factor, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700/60 text-xs text-slate-700 dark:text-slate-300 flex items-start space-x-2"
                            >
                              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0" />
                              <span>{factor}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="h-full min-h-[300px] flex items-center justify-center p-8 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30 text-center">
                <div className="space-y-2">
                  <Info className="w-8 h-8 text-indigo-500 mx-auto" />
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Select a Danger Hotspot
                  </h4>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Click any active hotspot cluster card on the left to inspect its decision tree split logic and natural language explanations.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
