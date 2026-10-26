/**
 * Strict TypeScript types reconciled directly against FastAPI OpenAPI spec (v3.1.0).
 */

export type RiskBand = 'low' | 'moderate' | 'high' | 'severe';

export interface EdgeRiskPrediction {
  edge_id: string;
  timestamp: string;
  risk_score: number; // 0.0 - 1.0
  risk_band: RiskBand;
  is_hotspot: boolean;
  contributing_features: Record<string, number>;
}

export interface BatchInferenceResult {
  prediction_id: string;
  forecast_timestamp: string;
  num_edges_evaluated: number;
  num_hotspots_detected: number;
  inference_latency_ms: number;
  edge_predictions: EdgeRiskPrediction[];
}

export interface Waypoint {
  latitude: number;
  longitude: number;
  sequence_order?: number;
}

export interface RouteRequest {
  route_id: string;
  origin: Waypoint;
  destination: Waypoint;
  departure_time?: string;
  waypoints?: Waypoint[];
}

export interface DecisionRule {
  feature_name: string;
  operator: '<=' | '<' | '>=' | '>' | '==' | '!=';
  threshold_value: number;
  description?: string;
}

export interface HotspotRule {
  rule_id: string;
  cluster_id: string;
  conditions: DecisionRule[];
  rule_precision: number;
  support_sample_count: number;
}

export interface HotspotCluster {
  cluster_id: string;
  edge_ids: string[];
  centroid_latitude: number;
  centroid_longitude: number;
  avg_risk_probability: number;
  max_risk_probability: number;
  radius_meters?: number;
  top_rule?: HotspotRule | null;
}

export interface NaturalLanguageExplanation {
  cluster_id: string;
  summary: string;
  causative_statement: string;
  contributing_factors: string[];
  driver_advisory: string;
  confidence_score: number;
}

export interface DetourOption {
  detour_id: string;
  risk_reduction_pct: number;
  additional_distance_km: number;
  additional_time_minutes: number;
  geometry_polyline: string; // WKT LINESTRING
}

export interface AlertPayload {
  alert_id: string;
  created_at: string;
  hotspot_cluster_id: string;
  hazard_location: Waypoint;
  max_risk_probability: number;
  explanation: NaturalLanguageExplanation;
  suggested_detour?: DetourOption | null;
  affected_edge_ids: string[];
}

export interface RouteResponse {
  route_id: string;
  overall_safety_status: 'SAFE' | 'CAUTION' | 'HAZARDOUS' | string;
  max_risk_score: number;
  active_alerts: AlertPayload[];
  recommended_route_geometry: string; // WKT LINESTRING
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  graph_nodes: number;
  graph_edges: number;
}

export interface MetricsResponse {
  active_feature_cache: string;
  hotspot_cutoff: number;
  routing_engine: string;
}

export interface ApiErrorDetail {
  detail: string | Array<{ loc: (string | number)[]; msg: string; type: string }>;
}
