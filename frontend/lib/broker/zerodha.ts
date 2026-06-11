import 'server-only';

import { KiteConnect, KiteTicker, type Tick as KiteTick } from 'kiteconnect';

import type { BrokerAdapter, BrokerConfig, OHLCV, OptionChainRow, Tick } from './types';
import { getOptionChainForZerodha } from '@/lib/options/zerodhaOptionChain';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function toTick(t: KiteTick): Tick {
  const full = t as unknown as {
    instrument_token: number;
    last_price: number;
    ohlc?: { open: number; high: number; low: number; close: number };
    volume_traded?: number;
    oi?: number;
    exchange_timestamp?: Date | null;
    last_trade_time?: Date | null;
  };

  return {
    symbol: String(full.instrument_token),
    ltp: Number(full.last_price ?? 0),
    open: Number(full.ohlc?.open ?? 0),
    high: Number(full.ohlc?.high ?? 0),
    low: Number(full.ohlc?.low ?? 0),
    close: Number(full.ohlc?.close ?? 0),
    volume: Number(full.volume_traded ?? 0),
    timestamp:
      (full.last_trade_time ?? undefined) ||
      (full.exchange_timestamp ?? undefined) ||
      new Date(),
    oi: typeof full.oi === 'number' ? full.oi : undefined,
  };
}

export class ZerodhaAdapter implements BrokerAdapter {
  private kite: KiteConnect | null = null;
  private ticker: KiteTicker | null = null;
  private apiKey: string | null = null;
  private accessToken: string | null = null;

  // simple local throttle for historical calls (Zerodha: ~3 req/sec)
  private lastHistoryCallAtMs = 0;

  async connect(config: BrokerConfig) {
    try {
      this.apiKey = config.apiKey;
      this.accessToken = config.accessToken;
      this.kite = new KiteConnect({ api_key: config.apiKey });
      this.kite.setAccessToken(config.accessToken);
      const profile = await this.kite.getProfile();
      return { success: true, profile };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, error: msg };
    }
  }

  async disconnect() {
    try {
      this.ticker?.disconnect();
    } finally {
      this.ticker = null;
      this.kite = null;
      this.apiKey = null;
      this.accessToken = null;
    }
  }

  subscribeToTicks(symbols: string[], onTick: (tick: Tick) => void) {
    if (!this.kite || !this.apiKey || !this.accessToken) {
      throw new Error('Zerodha: connect() must be called before subscribeToTicks().');
    }
    const tokens = symbols.map(Number).filter((n) => Number.isFinite(n));
    if (tokens.length !== symbols.length) {
      throw new Error('Zerodha: subscribeToTicks expects instrument tokens as numeric strings.');
    }

    this.ticker = new KiteTicker({
      api_key: this.apiKey,
      access_token: this.accessToken,
    });

    this.ticker.on('ticks', (ticks: KiteTick[]) => {
      ticks.forEach((t) => onTick(toTick(t)));
    });

    this.ticker.on('connect', () => {
      this.ticker!.subscribe(tokens);
      this.ticker!.setMode(this.ticker!.modeFull, tokens);
    });

    this.ticker.on('error', (err: unknown) => console.error('KiteTicker error:', err));
    this.ticker.on('disconnect', () => console.warn('KiteTicker disconnected'));

    this.ticker.connect();
  }

  unsubscribeFromTicks(symbols: string[]) {
    const tokens = symbols.map(Number).filter((n) => Number.isFinite(n));
    this.ticker?.unsubscribe(tokens);
  }

  async getHistoricalData(symbol: string, interval: string, from: Date, to: Date): Promise<OHLCV[]> {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getHistoricalData().');

    const now = Date.now();
    const elapsed = now - this.lastHistoryCallAtMs;
    if (elapsed < 400) await sleep(400 - elapsed);
    this.lastHistoryCallAtMs = Date.now();

    type KiteHistoryInterval = Parameters<KiteConnect['getHistoricalData']>[1];
    const raw = await this.kite.getHistoricalData(Number(symbol), interval as KiteHistoryInterval, from, to, false);
    return raw.map((c: { date: Date; open: number; high: number; low: number; close: number; volume: number }) => ({
      timestamp: new Date(c.date),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
      volume: c.volume,
    }));
  }

  async getOptionChain(symbol: string, expiry: string): Promise<OptionChainRow[]> {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getOptionChain().');
    return await getOptionChainForZerodha(this.kite, symbol, expiry);
  }

  async getProfile() {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getProfile().');
    return this.kite.getProfile();
  }

  async getFunds() {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getFunds().');
    const margins = await this.kite.getMargins();
    return {
      available: margins.equity.available.cash,
      used: margins.equity.utilised.debits,
    };
  }

  async getPositions() {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getPositions().');
    return this.kite.getPositions();
  }

  async getHoldings() {
    if (!this.kite) throw new Error('Zerodha: connect() must be called before getHoldings().');
    return this.kite.getHoldings();
  }
}

