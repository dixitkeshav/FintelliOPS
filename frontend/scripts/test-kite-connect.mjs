/**
 * Kite Connect connectivity check.
 * Run: node --env-file=.env.local scripts/test-kite-connect.mjs [SYMBOL]
 */
import { KiteConnect } from 'kiteconnect';

const apiKey = process.env.KITE_API_KEY?.trim();
const accessToken = process.env.KITE_ACCESS_TOKEN?.trim();
const symbol = (process.argv[2] || 'RELIANCE').toUpperCase().replace(/\.NS$/, '');

function fail(msg) {
  console.error('FAIL:', msg);
  process.exit(1);
}

if (!apiKey || !accessToken) {
  fail('Set KITE_API_KEY and KITE_ACCESS_TOKEN in frontend/.env.local');
}

const kite = new KiteConnect({ api_key: apiKey });
kite.setAccessToken(accessToken);

console.log('Kite Connect diagnostics');
console.log('API route (library): GET /instruments/historical/:instrument_token/:interval');
console.log('---');

// 1) Session / profile
try {
  const profile = await kite.getProfile();
  console.log('OK  getProfile()', profile.user_name, profile.user_id, profile.email);
} catch (e) {
  fail(`getProfile — ${e.message}${formatKite(e)}`);
}

// 2) Margins (funds)
try {
  const margins = await kite.getMargins();
  const cash = margins?.equity?.available?.cash;
  console.log('OK  getMargins()', cash != null ? `cash=${cash}` : margins);
} catch (e) {
  console.warn('WARN getMargins()', e.message, formatKite(e));
}

// 3) Resolve NSE instrument token
let instrumentToken = null;
try {
  const res = await fetch('https://api.kite.trade/instruments');
  if (!res.ok) fail(`instruments dump HTTP ${res.status}`);
  const csv = await res.text();
  const lines = csv.split(/\r?\n/).filter(Boolean);
  const header = lines[0].split(',');
  const ti = (n) => header.indexOf(n);
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (
      cols[ti('exchange')] === 'NSE' &&
      cols[ti('instrument_type')] === 'EQ' &&
      cols[ti('tradingsymbol')] === symbol
    ) {
      instrumentToken = Number(cols[ti('instrument_token')]);
      break;
    }
  }
  if (!instrumentToken) fail(`NSE EQ symbol not found: ${symbol}`);
  console.log('OK  resolve', symbol, '→ instrument_token', instrumentToken);
} catch (e) {
  fail(`instruments — ${e.message}`);
}

// 4) LTP quote (market data permission)
try {
  const ltp = await kite.getLTP([`NSE:${symbol}`]);
  console.log('OK  getLTP(NSE:' + symbol + ')', ltp);
} catch (e) {
  console.warn('WARN getLTP()', e.message, formatKite(e));
}

// 5) Historical candles — same path as backtest
const to = new Date();
const from = new Date();
from.setFullYear(from.getFullYear() - 1);
try {
  const candles = await kite.getHistoricalData(instrumentToken, 'day', from, to, false);
  console.log('OK  getHistoricalData(day)', `rows=${candles?.length ?? 0}`);
  if (candles?.length) {
    const last = candles[candles.length - 1];
    console.log('    last candle:', last);
  }
} catch (e) {
  console.error('FAIL getHistoricalData()', e.message, formatKite(e));
  console.error(
    '\nIf error is "Insufficient permission": enable Historical / market data on your app at https://developers.kite.trade/apps'
  );
  process.exit(1);
}

console.log('---');
console.log('All checks passed. Kite historical API is working for this app/token.');

function formatKite(e) {
  const d = e?.response?.data;
  if (!d) return '';
  return ` | ${JSON.stringify(d)}`;
}
