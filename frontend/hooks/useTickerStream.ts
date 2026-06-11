'use client';

import { useEffect, useRef } from 'react';
import { WebSocketClient } from '@/lib/websocket';
import { useMarketStore } from '@/store/marketStore';

export function useTickerStream() {
  const wsRef = useRef<WebSocketClient | null>(null);
  const updateIndex = useMarketStore((state) => state.updateIndex);

  useEffect(() => {
    wsRef.current = new WebSocketClient('/ws/market/ticker/');

    wsRef.current.connect((data) => {
      if (data.type === 'price_update') {
        updateIndex(data.symbol, {
          price: data.price,
          change: data.change,
          changePercent: data.changePercent,
        });
      }
    });

    return () => {
      wsRef.current?.disconnect();
    };
  }, [updateIndex]);

  return wsRef.current;
}
