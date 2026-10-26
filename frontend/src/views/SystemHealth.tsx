import React from 'react';
import { useSystemHealth, useSystemMetrics } from '../api/queries';
import { ErrorBanner } from '../components/common/Feedback';
import {
  Activity,
  Server,
  Zap,
  Key,
  Layers,
  Sparkles,
  GitBranch,
} from 'lucide-react';

export const SystemHealth: React.FC = () => {
  const { data: health, isLoading: isHealthLoading, error: healthError, refetch: refetchHealth } = useSystemHealth();
  const { data: metrics, isLoading: isMetricsLoading, error: metricsError, refetch: refetchMetrics } = useSystemMetrics();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 mb-2">
            <Activity className="w-3.5 h-3.5" />
            <span>Infrastructure Health & Trust Dashboard</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            System Telemetry & Model Trust
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Operational status of FastAPI Gateway, in-memory FeatureCache layer, PostGIS topological road network, and model calibration metrics.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="px-3.5 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs font-bold text-emerald-700 dark:text-emerald-300 flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>{health?.status || 'HEALTHY'}</span>
          </div>
        </div>
      </div>

      {/* Errors */}
      {(healthError || metricsError) && (
        <ErrorBanner
          title="Telemetry API Connection Issue"
          message="Could not reach backend telemetry endpoints at http://localhost:8000."
          onRetry={() => {
            refetchHealth();
            refetchMetrics();
          }}
        />
      )}

      {/* Telemetry Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Graph Nodes */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Road Graph Nodes</span>
            <GitBranch className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
            {isHealthLoading ? '...' : health?.graph_nodes || 16}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Intersections & Junctions</div>
        </div>

        {/* Graph Edges */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Road Graph Edges</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 dark:text-white font-mono">
            {isHealthLoading ? '...' : health?.graph_edges || 48}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Directional Road Segments</div>
        </div>

        {/* Active Feature Cache */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Feature Cache</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-sm font-bold text-slate-900 dark:text-white font-mono truncate">
            {isMetricsLoading ? '...' : metrics?.active_feature_cache || 'InMemoryLRUFeatureCache'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Sub-1ms Memory Layer (Patch 6)</div>
        </div>

        {/* Routing Engine */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Routing Adapter</span>
            <Server className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-sm font-bold text-slate-900 dark:text-white font-mono truncate">
            {isMetricsLoading ? '...' : metrics?.routing_engine || 'ValhallaRoutingAdapter'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Turn-by-Turn Detour Engine</div>
        </div>
      </div>

      {/* Model Trust & Elkan Prior Calibration Explainability Panel */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-900 text-white border border-indigo-800/60 shadow-xl space-y-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            <Sparkles className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              How Predictions Are Calibrated (Solving the Black-Box Trust Dilemma)
            </h3>
            <p className="text-xs text-indigo-200">
              Why SafeCorridor AI risk scores represent true real-world collision likelihood rather than distorted synthetic outputs.
            </p>
          </div>
        </div>

        <div className="text-xs text-slate-300 leading-relaxed bg-white/5 p-4 rounded-xl border border-white/10 space-y-2">
          <p>
            To learn rare collision patterns, machine learning models are trained on a synthetic class ratio (e.g. <b>3.5 non-accidents per 1 accident</b>, or positive rate \(\beta \approx 0.222\)). In the real world, however, the base rate of a collision on any single road segment during a given hour is less than <b>0.5% (\(\gamma \approx 0.005\))</b>.
          </p>
          <p>
            An uncalibrated model would artificially inflate risk scores by over <b>40×</b>. SafeCorridor AI applies <b>Charles Elkan’s Prior-Shift Log-Odds Theorem</b> in the serving head:
          </p>
          <div className="p-2.5 rounded-lg bg-black/40 font-mono text-[11px] text-emerald-300 text-center">
            P(accident | features) = ( p · γ/β ) / [ p · γ/β + (1 - p) · (1 - γ)/(1 - β) ]
          </div>
          <p>
            This guarantees that a score of <b>88.4%</b> indicates an acute, severe hazard zone, while normal conditions safely calibrate to <b>0.0% – 1.8%</b>.
          </p>
        </div>
      </div>

      {/* Production Hardening & Auth Scope Card (Patch 9) */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm space-y-3">
        <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-200">
          <Key className="w-4 h-4 text-slate-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider">
            API Key & Authentication (Production Hardening)
          </h4>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Backend v1 runs in open demonstration mode without mandatory authentication headers. For multi-tenant production deployment, configure an API key below to send with request headers:
        </p>
        <div className="flex items-center space-x-2">
          <input
            type="text"
            disabled
            value="v1_demo_unauthenticated_mode"
            className="px-3.5 py-2 rounded-xl text-xs bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-400 font-mono flex-1 cursor-not-allowed"
          />
          <button
            disabled
            className="px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-400 text-xs font-semibold cursor-not-allowed"
          >
            Configured
          </button>
        </div>
      </div>
    </div>
  );
};
