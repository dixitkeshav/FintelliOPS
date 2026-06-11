'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PriceWidgetProps {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

export function PriceWidget({ symbol, price, change, changePercent }: PriceWidgetProps) {
  const isPositive = change >= 0;

  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-card/50 border border-border/50 hover:bg-card transition-colors">
      <div className="flex flex-col">
        <span className="text-xs text-muted-foreground">{symbol}</span>
        <span className="font-mono text-sm font-semibold">
          {price.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </span>
      </div>
      <div
        className={cn(
          'flex items-center gap-1 text-xs font-medium',
          isPositive ? 'text-price-up' : 'text-price-down'
        )}
      >
        {isPositive ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        <span>
          {isPositive ? '+' : ''}
          {changePercent.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
