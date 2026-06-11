'use client';

import { useLiveTicker } from '@/hooks/useLiveTicker';
import { useMarketStore } from '@/store/marketStore';
import { fmtPct, fmtPrice } from '@/lib/fintelli/format';

export function TickerStrip() {
  useLiveTicker();
  const indices = useMarketStore((s) => s.indices);
  const items = [...indices, ...indices];

  return (
    <div className="ticker-strip">
      <div className="ticker-track">
        {items.map((t, i) => {
          const up = t.changePercent >= 0;
          return (
            <div key={`${t.symbol}-${i}`} className="tick-item">
              <span className="tick-sym">{t.symbol}</span>
              <span className="tick-p">{fmtPrice(t.price)}</span>
              <span style={{ fontSize: 10, fontWeight: 600, fontFamily: 'JetBrains Mono', color: up ? 'var(--green)' : 'var(--red)' }}>
                {up ? '▲' : '▼'} {fmtPct(t.changePercent)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
