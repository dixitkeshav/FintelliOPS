'use client';

import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';
import { WebSocketClient } from '@/lib/websocket';
import { useMarketStore } from '@/store/marketStore';

/** Fetches live ticker data from /api/live-ticker/ and populates market store. Polls every 2 min. */
export function useLiveTicker() {
  const setIndices = useMarketStore((state) => state.setIndices);
  const updateIndex = useMarketStore((state) => state.updateIndex);
  const hasInitialized = useRef(false);
  const wsRef = useRef<WebSocketClient | null>(null);

  const { data: tickers = [] } = useQuery({
    queryKey: ['live-ticker'],
    queryFn: () => apiClient.getLiveTicker(),
    refetchInterval: 30000, // 30 seconds
    staleTime: 60000,
  });

  useEffect(() => {
    if (!tickers.length) return;
    const indices = tickers.map((t) => ({
      symbol: t.symbol.replace(/^\^/, '').split('.')[0].slice(0, 8),
      rawSymbol: t.symbol,
      price: t.price,
      change: (t.price * (t.change_pct / 100)),
      changePercent: t.change_pct,
      volume: 0,
    }));
    setIndices(indices);
    hasInitialized.current = true;
  }, [tickers, setIndices]);

  // Optional WS overlay: keeps existing polling fallback intact.
  useEffect(() => {
    wsRef.current = new WebSocketClient('/ws/dashboard/');
    wsRef.current.connect((raw) => {
      if (!raw || typeof raw !== 'object') return;
      const data = raw as {
        type?: string;
        symbol?: string;
        price?: number;
        change?: number;
        changePercent?: number;
      };
      if (data.type !== 'ticker_update' || !data.symbol || typeof data.price !== 'number') {
        return;
      }
      const symbol = data.symbol.replace(/^\^/, '').split('.')[0].slice(0, 8);
      updateIndex(symbol, {
        price: data.price,
        change: typeof data.change === 'number' ? data.change : 0,
        changePercent: typeof data.changePercent === 'number' ? data.changePercent : 0,
      });
    });
    return () => {
      wsRef.current?.disconnect();
      wsRef.current = null;
    };
  }, [updateIndex]);

  return tickers;
}
