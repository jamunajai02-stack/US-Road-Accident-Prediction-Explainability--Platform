import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import { RouteRequest } from './types';

export const QUERY_KEYS = {
  health: ['health'] as const,
  metrics: ['metrics'] as const,
  predict: (edgeIds?: string[] | null) => ['predict', edgeIds] as const,
  hotspots: ['hotspots'] as const,
  explanation: (clusterId: string) => ['explanation', clusterId] as const,
  route: (routeId: string) => ['route', routeId] as const,
};

export function useSystemHealth() {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: api.getHealth,
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: QUERY_KEYS.metrics,
    queryFn: api.getMetrics,
    staleTime: 30000,
  });
}

export function usePredictions(edgeIds?: string[] | null, autoPoll = true) {
  return useQuery({
    queryKey: QUERY_KEYS.predict(edgeIds),
    queryFn: () => api.predict(edgeIds),
    refetchInterval: autoPoll ? 60000 : false, // Poll every 60s as specified
    staleTime: 20000,
  });
}

export function useHotspots(autoPoll = true) {
  return useQuery({
    queryKey: QUERY_KEYS.hotspots,
    queryFn: api.getHotspots,
    refetchInterval: autoPoll ? 60000 : false,
    staleTime: 20000,
  });
}

export function useHotspotExplanation(clusterId: string, enabled = true) {
  return useQuery({
    queryKey: QUERY_KEYS.explanation(clusterId),
    queryFn: () => api.getHotspotExplanation(clusterId),
    enabled: Boolean(clusterId) && enabled,
    staleTime: 60000,
  });
}

export function useRouteCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RouteRequest) => api.checkRoute(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEYS.route(data.route_id), data);
    },
  });
}
