import 'server-only';

import type { KiteConnect } from 'kiteconnect';
import type { OptionChainRow } from '@/lib/broker/types';
import { blackScholesGreeks, impliedVolatilityNewton } from './greeks';

type InstrumentRow = {
  instrument_token: number;
  exchange: string;
  tradingsymbol: string;
  name: string;
  instrument_type: string;
  expiry: string;
  strike: number;
  segment: string;
};

let instrumentsCache:
  | { fetchedAtMs: number; rows: InstrumentRow[] }
  | null = null;

function parseCsvLine(line: string): string[] {
  // Simple CSV parser supporting quoted commas.
  const out: string[] = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"' && line[i + 1] === '"') {
      cur += '"';
      i++;
      continue;
    }
    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (ch === ',' && !inQuotes) {
      out.push(cur);
      cur = '';
      continue;
    }
    cur += ch;
  }
  out.push(cur);
  return out;
}

async function loadKiteInstruments(): Promise<InstrumentRow[]> {
  const now = Date.now();
  if (instrumentsCache && now - instrumentsCache.fetchedAtMs < 24 * 60 * 60 * 1000) {
    return instrumentsCache.rows;
  }

  const res = await fetch('https://api.kite.trade/instruments', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load Kite instruments dump (${res.status})`);
  const csv = await res.text();
  const lines = csv.split(/\r?\n/).filter(Boolean);
  const header = parseCsvLine(lines[0]);
  const idx = (name: string) => header.indexOf(name);

  const tokenI = idx('instrument_token');
  const exchangeI = idx('exchange');
  const tradingsymbolI = idx('tradingsymbol');
  const nameI = idx('name');
  const instrumentTypeI = idx('instrument_type');
  const expiryI = idx('expiry');
  const strikeI = idx('strike');
  const segmentI = idx('segment');

  const rows: InstrumentRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = parseCsvLine(lines[i]);
    if (cols.length < header.length) continue;
    const segment = cols[segmentI] ?? '';
    if (!segment.includes('NFO-OPT')) continue;
    const instrument_type = cols[instrumentTypeI] ?? '';
    if (instrument_type !== 'CE' && instrument_type !== 'PE') continue;
    const expiry = cols[expiryI] ?? '';
    if (!expiry) continue;
    rows.push({
      instrument_token: Number(cols[tokenI]),
      exchange: cols[exchangeI] ?? '',
      tradingsymbol: cols[tradingsymbolI] ?? '',
      name: cols[nameI] ?? '',
      instrument_type,
      expiry,
      strike: Number(cols[strikeI]),
      segment,
    });
  }

  instrumentsCache = { fetchedAtMs: now, rows };
  return rows;
}

function timeToExpiryYears(expiryIso: string): number {
  const expiry = new Date(`${expiryIso}T15:30:00+05:30`); // India market close-ish
  const ms = expiry.getTime() - Date.now();
  return Math.max(ms / (365 * 24 * 60 * 60 * 1000), 0);
}

export async function getOptionChainForZerodha(kite: KiteConnect, symbol: string, expiry: string): Promise<OptionChainRow[]> {
  const instruments = await loadKiteInstruments();
  const expiryNorm = expiry.trim();
  const symbolNorm = symbol.trim().toUpperCase();

  // Heuristic: instruments dump has `name` as underlying for indices (NIFTY, BANKNIFTY, SENSEX etc).
  const filtered = instruments.filter(
    (r) => r.expiry === expiryNorm && (r.name?.toUpperCase() === symbolNorm || r.tradingsymbol.toUpperCase().startsWith(symbolNorm))
  );
  if (filtered.length === 0) return [];

  // LTP batch (kite.getLTP accepts "NFO:TRADINGSYMBOL")
  const instrumentKeys = filtered.map((r) => `NFO:${r.tradingsymbol}`);
  const ltpResp = (await kite.getLTP(instrumentKeys)) as unknown as Record<string, { last_price?: number }>;

  // Spot proxy: use ATM strike midpoint to approximate spot if we don't have underlying quote wired yet.
  const strikes = Array.from(new Set(filtered.map((r) => r.strike))).sort((a, b) => a - b);
  const approxSpot = strikes[Math.floor(strikes.length / 2)] ?? 0;

  const T = timeToExpiryYears(expiryNorm);
  const r = 0.065; // 6.5% India risk-free proxy

  const byStrike = new Map<number, Partial<OptionChainRow>>();
  for (const inst of filtered) {
    const key = `NFO:${inst.tradingsymbol}`;
    const ltp = Number(ltpResp?.[key]?.last_price ?? 0);

    const strike = inst.strike;
    const base: Partial<OptionChainRow> = byStrike.get(strike) ?? { strike, expiry: expiryNorm };

    const type = inst.instrument_type === 'CE' ? 'call' : 'put';
    const iv = impliedVolatilityNewton({
      type,
      marketPrice: ltp,
      spot: approxSpot,
      strike,
      timeYears: T,
      rate: r,
      initialIv: 0.25,
    });
    const g = blackScholesGreeks({ type, spot: approxSpot, strike, timeYears: T, rate: r, iv });

    if (inst.instrument_type === 'CE') {
      base.callLTP = ltp;
      base.callOI = 0;
      base.callOIChange = 0;
      base.callIV = g.iv;
      base.callDelta = g.delta;
      base.callTheta = g.theta;
      base.callGamma = g.gamma;
      base.callVega = g.vega;
    } else {
      base.putLTP = ltp;
      base.putOI = 0;
      base.putOIChange = 0;
      base.putIV = g.iv;
      base.putDelta = g.delta;
      base.putTheta = g.theta;
      base.putGamma = g.gamma;
      base.putVega = g.vega;
    }
    byStrike.set(strike, base);
  }

  return Array.from(byStrike.values())
    .map((r) => ({
      strike: r.strike ?? 0,
      expiry: r.expiry ?? expiryNorm,
      callLTP: r.callLTP ?? 0,
      callOI: r.callOI ?? 0,
      callOIChange: r.callOIChange ?? 0,
      callIV: r.callIV ?? 0,
      callDelta: r.callDelta ?? 0,
      callTheta: r.callTheta ?? 0,
      callGamma: r.callGamma ?? 0,
      callVega: r.callVega ?? 0,
      putLTP: r.putLTP ?? 0,
      putOI: r.putOI ?? 0,
      putOIChange: r.putOIChange ?? 0,
      putIV: r.putIV ?? 0,
      putDelta: r.putDelta ?? 0,
      putTheta: r.putTheta ?? 0,
      putGamma: r.putGamma ?? 0,
      putVega: r.putVega ?? 0,
    }))
    .sort((a, b) => a.strike - b.strike);
}

