import 'server-only';

import { KiteConnect, KiteTicker, type Tick } from 'kiteconnect';

import type { BrokerClient, UnsubscribeTicks } from '../contract';
import { chartIntervalToKite } from '../interval-map';
import type {
  BrokerProfileSummary,
  ChartInterval,
  HistoricalCandle,
  NormalizedTick,
  OptionChainStrikeRow,
  PlaceOrderParams,
} from '../types';

function parseInstrumentTokens(symbols: string[]): number[] {
  const tokens = symbols
    .map((s) => Number(String(s).trim()))
    .filter((n) => Number.isFinite(n) && n > 0);
  if (tokens.length !== symbols.length) {
    throw new Error(
      'Zerodha subscribeToTicks: every entry in `symbols` must be a numeric instrument_token string (e.g. "256265").'
    );
  }
  return tokens;
}

function kiteTickToNormalized(t: Tick): NormalizedTick {
  const full = t as Extract<Tick, { volume_traded?: number }>;
  return {
    instrumentToken: t.instrument_token,
    lastPrice: t.last_price,
    lastTradedQuantity: 'last_traded_quantity' in t ? t.last_traded_quantity : undefined,
    volumeTraded: 'volume_traded' in full ? full.volume_traded : undefined,
    openInterest: 'oi' in full ? full.oi : undefined,
    ohlc: 'ohlc' in t ? t.ohlc : undefined,
    timestamp:
      'last_trade_time' in t && t.last_trade_time
        ? t.last_trade_time
        : 'exchange_timestamp' in t && t.exchange_timestamp
          ? t.exchange_timestamp
          : undefined,
  };
}

export class ZerodhaKiteBroker implements BrokerClient {
  private kite: KiteConnect | null = null;
  private apiKey: string | null = null;
  private accessToken: string | null = null;

  async connect(apiKey: string, apiSecret: string, accessToken: string): Promise<void> {
    void apiSecret;
    this.apiKey = apiKey;
    this.accessToken = accessToken;
    const k = new KiteConnect({ api_key: apiKey });
    k.setAccessToken(accessToken);
    this.kite = k;
  }

  private requireKite(): KiteConnect {
    if (!this.kite || !this.accessToken || !this.apiKey) {
      throw new Error('Broker not connected — call connect(apiKey, apiSecret, accessToken) first.');
    }
    return this.kite;
  }

  async subscribeToTicks(symbols: string[], onTick: (t: NormalizedTick) => void): Promise<UnsubscribeTicks> {
    const tokens = parseInstrumentTokens(symbols);
    const apiKey = this.apiKey ?? '';
    const accessToken = this.accessToken ?? '';
    if (!apiKey || !accessToken) {
      throw new Error('Broker not connected — session required for WebSocket.');
    }

    const ticker = new KiteTicker({
      api_key: apiKey,
      access_token: accessToken,
    });

    const handler = (batch: Tick[]) => {
      for (const raw of batch) {
        onTick(kiteTickToNormalized(raw));
      }
    };

    ticker.on('ticks', handler);
    ticker.on('connect', () => {
      ticker.subscribe(tokens);
      ticker.setMode(ticker.modeFull, tokens);
    });
    ticker.connect();

    return () => {
      try {
        ticker.unsubscribe(tokens);
      } catch {
        /* noop */
      }
      ticker.disconnect();
    };
  }

  async getHistoricalData(
    symbolInstrumentToken: string,
    interval: ChartInterval,
    fromDate: Date,
    toDate: Date
  ): Promise<HistoricalCandle[]> {
    const kite = this.requireKite();
    const token = Number(symbolInstrumentToken);
    if (!Number.isFinite(token)) {
      throw new Error('getHistoricalData: Zerodha expects numeric instrument_token as `symbolInstrumentToken`.');
    }
    const kiteInterval = chartIntervalToKite(interval);
    const rows = await kite.getHistoricalData(token, kiteInterval, fromDate, toDate, false, true);
    return rows.map((r) => ({
      time: r.date,
      open: r.open,
      high: r.high,
      low: r.low,
      close: r.close,
      volume: r.volume,
      openInterest: r.oi,
    }));
  }

  async getOptionChain(_symbol: string, _expiry: string): Promise<OptionChainStrikeRow[]> {
    void _symbol;
    void _expiry;
    // Full NFO chain + greeks batching lands in Options panel phase; return typed empty for now.
    return [];
  }

  async placeOrder(_params: PlaceOrderParams): Promise<{ orderId?: string }> {
    void _params;
    throw new Error('placeOrder is scaffold-only — not enabled for live trading yet.');
  }

  async getPositions(): Promise<unknown> {
    return this.requireKite().getPositions();
  }

  async getProfile(): Promise<BrokerProfileSummary> {
    const p = await this.requireKite().getProfile();
    return {
      userName: p.user_name,
      userShortname: p.user_shortname,
      email: p.email,
      broker: p.broker,
    };
  }
}
