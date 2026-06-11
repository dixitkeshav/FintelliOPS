export interface BrokerConfig {
  broker: 'zerodha' | 'upstox' | 'fyers' | 'angelone' | 'custom';
  apiKey: string;
  apiSecret: string;
  accessToken: string;
  redirectUrl?: string;
}

export interface Tick {
  /** For Zerodha streaming: instrument token string */
  symbol: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: Date;
  /** open interest for F&O */
  oi?: number;
}

export interface OHLCV {
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OptionChainRow {
  strike: number;
  expiry: string;
  callLTP: number;
  callOI: number;
  callOIChange: number;
  callIV: number;
  callDelta: number;
  callTheta: number;
  callGamma: number;
  callVega: number;
  putLTP: number;
  putOI: number;
  putOIChange: number;
  putIV: number;
  putDelta: number;
  putTheta: number;
  putGamma: number;
  putVega: number;
}

export interface BrokerAdapter {
  connect(config: BrokerConfig): Promise<{ success: boolean; profile?: unknown; error?: string }>;
  disconnect(): Promise<void>;
  subscribeToTicks(symbols: string[], onTick: (tick: Tick) => void): void;
  unsubscribeFromTicks(symbols: string[]): void;
  getHistoricalData(symbol: string, interval: string, from: Date, to: Date): Promise<OHLCV[]>;
  getOptionChain(symbol: string, expiry: string): Promise<OptionChainRow[]>;
  getProfile(): Promise<unknown>;
  getPositions(): Promise<unknown[]>;
  getHoldings(): Promise<unknown[]>;
  getFunds(): Promise<{ available: number; used: number }>;
}
