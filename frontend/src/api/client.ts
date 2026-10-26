import {
  BatchInferenceResult,
  HealthResponse,
  HotspotCluster,
  MetricsResponse,
  NaturalLanguageExplanation,
  RouteRequest,
  RouteResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status} ${response.statusText}`;
      let errorData = null;
      try {
        errorData = await response.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Response was not JSON
      }
      throw new ApiError(errorMessage, response.status, errorData);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network communication error',
      0,
      error
    );
  }
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),
  getMetrics: () => request<MetricsResponse>('/metrics'),
  
  predict: (edgeIds?: string[] | null) => {
    const params = (edgeIds && edgeIds.length)
      ? `?${edgeIds.map((id) => `edge_ids=${encodeURIComponent(id)}`).join('&')}`
      : '';
    return request<BatchInferenceResult>(`/v1/predict${params}`, { method: 'POST' });
  },
    
  checkRoute: (payload: RouteRequest) =>
    request<RouteResponse>('/v1/route-check', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    
  getHotspots: () => request<HotspotCluster[]>('/v1/hotspots'),
  
  getHotspotExplanation: (clusterId: string) =>
    request<NaturalLanguageExplanation>(`/v1/hotspots/${encodeURIComponent(clusterId)}/explanation`),
};
