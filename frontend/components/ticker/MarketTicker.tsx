'use client';

import { useMarketStore } from '@/store/marketStore';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function MarketTicker() {
  const indices = useMarketStore((state) => state.indices);

  // Duplicate the indices array to create seamless infinite scroll
  const tickerItems = [...indices, ...indices, ...indices];

  return (
    <div className="fixed bottom-0 left-0 right-0 h-12 bg-card/90 backdrop-blur-md border-t border-border z-50 overflow-hidden">
      <div className="flex items-center h-full animate-scroll-left">
        {tickerItems.map((index, i) => (
          <div
            key={`${index.symbol}-${i}`}
            className="flex items-center gap-3 px-6 border-r border-border/50 whitespace-nowrap"
          >
            <span className="font-semibold text-sm">{index.symbol}</span>
            <span className="text-foreground font-mono text-sm">
              {index.price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <div
              className={cn(
                'flex items-center gap-1 text-xs font-medium',
                index.change >= 0 ? 'text-price-up' : 'text-price-down'
              )}
            >
              {index.change >= 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span>
                {index.change >= 0 ? '+' : ''}
                {index.changePercent.toFixed(2)}%
              </span>
            </div>
          </div>
        ))}
      </div>
      <style jsx>{`
        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.33%);
          }
        }
        .animate-scroll-left {
          animation: scroll-left 30s linear infinite;
        }
      `}</style>
    </div>
  );
}
