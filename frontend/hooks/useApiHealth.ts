'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';
import { djangoOrigin } from '@/lib/apiBase';

export function useApiHealth() {
  const query = useQuery({
    queryKey: ['api-health'],
    queryFn: () => apiClient.checkHealth(),
    refetchInterval: 30000,
    staleTime: 10000,
    retry: 1,
  });

  return {
    isConnected: query.data?.ok === true,
    message: query.data?.message,
    backendUrl: djangoOrigin(),
    isLoading: query.isLoading,
    refetch: query.refetch,
  };
}
