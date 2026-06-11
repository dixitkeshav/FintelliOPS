import 'server-only';

import type { BrokerAdapter, BrokerConfig, OHLCV, OptionChainRow, Tick } from './types';

export class UpstoxAdapter implements BrokerAdapter {
  /**
   * Docs: https://upstox.com/developer/api-documentation/
   * Likely: OAuth + token exchange endpoints.
   */
  async connect(_config: BrokerConfig): Promise<{ success: boolean; profile?: unknown; error?: string }> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: WebSocket market feed endpoints (Upstox v2). */
  subscribeToTicks(_symbols: string[], _onTick: (tick: Tick) => void): void {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: WebSocket market feed endpoints (Upstox v2). */
  unsubscribeFromTicks(_symbols: string[]): void {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Historical candle endpoint (Upstox v2). */
  async getHistoricalData(_symbol: string, _interval: string, _from: Date, _to: Date): Promise<OHLCV[]> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Options chain endpoints (Upstox v2). */
  async getOptionChain(_symbol: string, _expiry: string): Promise<OptionChainRow[]> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Get profile endpoint (Upstox v2). */
  async getProfile(): Promise<unknown> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Positions endpoint (Upstox v2). */
  async getPositions(): Promise<unknown[]> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Holdings endpoint (Upstox v2). */
  async getHoldings(): Promise<unknown[]> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Funds/margins endpoint (Upstox v2). */
  async getFunds(): Promise<{ available: number; used: number }> {
    throw new Error('Upstox: not yet implemented');
  }

  /** Docs: Disconnect WS / revoke tokens. */
  async disconnect(): Promise<void> {
    throw new Error('Upstox: not yet implemented');
  }
}

