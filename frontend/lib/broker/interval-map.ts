import type { ChartInterval } from './types';

/** Kite-supported intervals used by `getHistoricalData` */
export type KiteHistoryInterval =
  | 'minute'
  | '3minute'
  | '5minute'
  | '10minute'
  | '15minute'
  | '30minute'
  | '60minute'
  | 'day';

/** Map EDGE UI interval → Zerodha Kite historical interval */
export function chartIntervalToKite(interval: ChartInterval): KiteHistoryInterval {
  const map: Record<ChartInterval, KiteHistoryInterval> = {
    '1m': 'minute',
    '5m': '5minute',
    '10m': '10minute',
    '15m': '15minute',
    '30m': '30minute',
    '1h': '60minute',
    '1D': 'day',
  };
  return map[interval];
}
