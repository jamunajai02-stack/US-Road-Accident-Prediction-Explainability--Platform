import { http, HttpResponse } from 'msw';
import {
  BatchInferenceResult,
  HealthResponse,
  HotspotCluster,
  MetricsResponse,
  NaturalLanguageExplanation,
  RouteResponse,
} from '../api/types';

export const mockHealth: HealthResponse = {
  status: 'HEALTHY',
  service: 'accident-prediction-platform-api',
  version: '0.1.0',
  environment: 'development',
  timestamp: '2026-08-18T14:30:00Z',
  graph_nodes: 16,
  graph_edges: 48,
};

export const mockMetrics: MetricsResponse = {
  active_feature_cache: 'InMemoryLRUFeatureCache',
  hotspot_cutoff: 0.8,
  routing_engine: 'ValhallaRoutingAdapter',
};

export const mockPredictions: BatchInferenceResult = {
  prediction_id: 'pred_test_123',
  forecast_timestamp: '2026-08-18T14:30:00Z',
  num_edges_evaluated: 2,
  num_hotspots_detected: 1,
  inference_latency_ms: 4.82,
  edge_predictions: [
    {
      edge_id: '1_2_1000',
      timestamp: '2026-08-18T14:30:00Z',
      risk_score: 0.884,
      risk_band: 'severe',
      is_hotspot: true,
      contributing_features: { precipitation_mm: 14.5, visibility_km: 1.8, traffic_density: 0.94 },
    },
    {
      edge_id: '2_3_1001',
      timestamp: '2026-08-18T14:30:00Z',
      risk_score: 0.12,
      risk_band: 'low',
      is_hotspot: false,
      contributing_features: { precipitation_mm: 0.0, visibility_km: 10.0, traffic_density: 0.2 },
    },
  ],
};

export const mockHotspots: HotspotCluster[] = [
  {
    cluster_id: 'hotspot_cluster_1',
    edge_ids: ['1_2_1000'],
    centroid_latitude: 37.7749,
    centroid_longitude: -122.4194,
    avg_risk_probability: 0.884,
    max_risk_probability: 0.884,
    radius_meters: 500,
  },
];

export const mockExplanation: NaturalLanguageExplanation = {
  cluster_id: 'hotspot_cluster_1',
  summary: 'Wet Pavement & Sharp Curve Loss-of-Control Hazard',
  causative_statement: 'Accident probability elevated to 88.4% primarily driven by heavy rainfall.',
  contributing_factors: ['Rainfall: 14.5 mm/h', 'Visibility: 1.8 km', 'Sharp road curvature'],
  driver_advisory: 'Reduce speed by 15-20 mph and increase following distance.',
  confidence_score: 0.92,
};

export const mockRouteCheck: RouteResponse = {
  route_id: 'trip_test_456',
  overall_safety_status: 'HAZARDOUS',
  max_risk_score: 0.884,
  active_alerts: [
    {
      alert_id: 'alert_test_789',
      created_at: '2026-08-18T14:30:00Z',
      hotspot_cluster_id: 'hotspot_cluster_1',
      hazard_location: { latitude: 37.7749, longitude: -122.4194, sequence_order: 0 },
      max_risk_probability: 0.884,
      explanation: mockExplanation,
      suggested_detour: {
        detour_id: 'detour_1_avoid',
        risk_reduction_pct: 77.4,
        additional_distance_km: 1.8,
        additional_time_minutes: 3.5,
        geometry_polyline: 'LINESTRING (-122.4194 37.7749, -122.395 37.7989)',
      },
      affected_edge_ids: ['1_2_1000'],
    },
  ],
  recommended_route_geometry: 'LINESTRING (-122.4194 37.7749, -122.395 37.7989)',
};

export const handlers = [
  http.get('/health', () => HttpResponse.json(mockHealth)),
  http.get('/metrics', () => HttpResponse.json(mockMetrics)),
  http.post('/v1/predict', () => HttpResponse.json(mockPredictions)),
  http.get('/v1/hotspots', () => HttpResponse.json(mockHotspots)),
  http.get('/v1/hotspots/:id/explanation', () => HttpResponse.json(mockExplanation)),
  http.post('/v1/route-check', () => HttpResponse.json(mockRouteCheck)),
];
