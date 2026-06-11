'use client';

import { useMarketStore } from '@/store/marketStore';
import { cn } from '@/lib/utils';
import { Circle } from 'lucide-react';

export function MarketStatus() {
  const status = useMarketStore((state) => state.marketStatus);

  const statusConfig = {
    OPEN: { label: 'Market Open', color: 'text-price-up', bgColor: 'bg-price-up/10' },
    CLOSED: { label: 'Market Closed', color: 'text-muted-foreground', bgColor: 'bg-muted' },
    PRE_MARKET: { label: 'Pre-Market', color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
    AFTER_HOURS: { label: 'After Hours', color: 'text-purple-500', bgColor: 'bg-purple-500/10' },
  };

  const config = statusConfig[status];

  return (
    <div className={cn('flex items-center gap-2 px-3 py-1.5 rounded-full', config.bgColor)}>
      <Circle className={cn('w-2 h-2 fill-current', config.color)} />
      <span className={cn('text-xs font-medium', config.color)}>{config.label}</span>
    </div>
  );
}
