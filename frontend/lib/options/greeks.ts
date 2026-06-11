export type OptionType = 'call' | 'put';

type Greeks = {
  iv: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
};

// NOTE: We only base64-encode tokens in localStorage; for real security this should be encrypted storage or server-side secrets.
// Greeks math is deterministic and safe to compute client-side/server-side.

function normPdf(x: number): number {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

// Abramowitz & Stegun approximation for CDF
function normCdf(x: number): number {
  const sign = x < 0 ? -1 : 1;
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const a1 = 0.319381530;
  const a2 = -0.356563782;
  const a3 = 1.781477937;
  const a4 = -1.821255978;
  const a5 = 1.330274429;
  const poly = ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t;
  const approx = 1 - normPdf(Math.abs(x)) * poly;
  return sign === 1 ? approx : 1 - approx;
}

function bsPrice(params: {
  type: OptionType;
  spot: number;
  strike: number;
  timeYears: number;
  rate: number;
  iv: number;
}): number {
  const { type, spot: S, strike: K, timeYears: T, rate: r, iv: sigma } = params;
  if (T <= 0 || sigma <= 0 || S <= 0 || K <= 0) return 0;
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
  const d2 = d1 - sigma * sqrtT;
  if (type === 'call') return S * normCdf(d1) - K * Math.exp(-r * T) * normCdf(d2);
  return K * Math.exp(-r * T) * normCdf(-d2) - S * normCdf(-d1);
}

function bsVega(params: { spot: number; strike: number; timeYears: number; rate: number; iv: number }): number {
  const { spot: S, strike: K, timeYears: T, rate: r, iv: sigma } = params;
  if (T <= 0 || sigma <= 0 || S <= 0 || K <= 0) return 0;
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
  return S * normPdf(d1) * sqrtT;
}

export function impliedVolatilityNewton(params: {
  type: OptionType;
  marketPrice: number;
  spot: number;
  strike: number;
  timeYears: number;
  rate: number;
  initialIv?: number;
}): number {
  const { marketPrice, initialIv = 0.25 } = params;
  if (!Number.isFinite(marketPrice) || marketPrice <= 0) return 0;

  let iv = Math.min(Math.max(initialIv, 0.01), 3);
  for (let i = 0; i < 30; i++) {
    const price = bsPrice({ ...params, iv });
    const diff = price - marketPrice;
    if (Math.abs(diff) < 1e-6) break;
    const vega = bsVega({ spot: params.spot, strike: params.strike, timeYears: params.timeYears, rate: params.rate, iv });
    if (vega < 1e-8) break;
    iv = iv - diff / vega;
    if (!Number.isFinite(iv)) return 0;
    iv = Math.min(Math.max(iv, 0.01), 3);
  }
  return iv;
}

export function blackScholesGreeks(params: {
  type: OptionType;
  spot: number;
  strike: number;
  timeYears: number;
  rate: number;
  iv: number;
}): Greeks {
  const { type, spot: S, strike: K, timeYears: T, rate: r, iv: sigma } = params;
  if (T <= 0 || sigma <= 0 || S <= 0 || K <= 0) {
    return { iv: 0, delta: 0, gamma: 0, theta: 0, vega: 0 };
  }
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrtT);
  const d2 = d1 - sigma * sqrtT;

  const delta = type === 'call' ? normCdf(d1) : normCdf(d1) - 1;
  const gamma = normPdf(d1) / (S * sigma * sqrtT);
  // theta returned per-day for nicer display
  const thetaAnnual =
    type === 'call'
      ? (-S * normPdf(d1) * sigma) / (2 * sqrtT) - r * K * Math.exp(-r * T) * normCdf(d2)
      : (-S * normPdf(d1) * sigma) / (2 * sqrtT) + r * K * Math.exp(-r * T) * normCdf(-d2);
  const theta = thetaAnnual / 365;
  const vega = (S * normPdf(d1) * sqrtT) / 100; // per 1% IV change

  return { iv: sigma, delta, gamma, theta, vega };
}

