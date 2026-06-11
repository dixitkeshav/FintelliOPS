'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient, NewsItem } from '@/lib/apiClient';

/** Fetches news from /api/fetch-news/ (Alpha Vantage). Polls every 30s. */
export function useNewsFeed() {
  const { data: news = [], isLoading, error } = useQuery<NewsItem[]>({
    queryKey: ['news'],
    queryFn: () => apiClient.getNews(100),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 15000,
  });

  return { news, isLoading, error };
}
