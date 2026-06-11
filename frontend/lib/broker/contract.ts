import type {
  ChartInterval,
  HistoricalCandle,
  NormalizedTick,
  OptionChainStrikeRow,
  PlaceOrderParams,
  BrokerProfileSummary,
} from './types';

/**
 * Pluggable broker contract for EDGE — swap Zerodha / Upstox / IB etc via registry.
 */
export interface BrokerClient {
  connect(apiKey: string, apiSecret: string, accessToken: string): Promise<void>;

  /**
   * Stream ticks for instrument tokens (`symbols` = numeric tokens as strings, e.g. `"256265"` for Nifty).
   * Zerodha KiteTicker requires numeric instrument_token; callers resolve symbols upstream or via instruments API.
   */
  subscribeToTicks(symbols: string[], onTick: (tick: NormalizedTick) => void): Promise<UnsubscribeTicks>;

  getHistoricalData(
    symbolInstrumentToken: string,
    interval: ChartInterval,
    fromDate: Date,
    toDate: Date
  ): Promise<HistoricalCandle[]>;

  /** Underlying symbol + expiry (YYYY-MM-DD) — Zerodha path filled in Phase 5 */
  getOptionChain(symbol: string, expiry: string): Promise<OptionChainStrikeRow[]>;

  placeOrder(params: PlaceOrderParams): Promise<{ orderId?: string }>;

  getPositions(): Promise<unknown>;

  getProfile(): Promise<BrokerProfileSummary>;
}

export type UnsubscribeTicks = () => void;
