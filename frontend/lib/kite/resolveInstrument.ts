import 'server-only';

type InstrumentRow = {
  instrument_token: number;
  exchange: string;
  tradingsymbol: string;
  name: string;
  instrument_type: string;
};

let cache: { fetchedAtMs: number; rows: InstrumentRow[] } | null = null;

function parseCsvLine(line: string): string[] {
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

async function loadInstruments(): Promise<InstrumentRow[]> {
  const now = Date.now();
  if (cache && now - cache.fetchedAtMs < 24 * 60 * 60 * 1000) {
    return cache.rows;
  }
  const res = await fetch('https://api.kite.trade/instruments', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Kite instruments dump failed (${res.status})`);
  const csv = await res.text();
  const lines = csv.split(/\r?\n/).filter(Boolean);
  const header = parseCsvLine(lines[0]);
  const idx = (name: string) => header.indexOf(name);
  const rows: InstrumentRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = parseCsvLine(lines[i]);
    rows.push({
      instrument_token: Number(cols[idx('instrument_token')]),
      exchange: cols[idx('exchange')] ?? '',
      tradingsymbol: cols[idx('tradingsymbol')] ?? '',
      name: cols[idx('name')] ?? '',
      instrument_type: cols[idx('instrument_type')] ?? '',
    });
  }
  cache = { fetchedAtMs: now, rows };
  return rows;
}

/** Resolve NSE equity symbol (e.g. RELIANCE) to Kite instrument_token. */
export async function resolveNseEquityToken(symbol: string): Promise<number | null> {
  const raw = symbol.trim().toUpperCase().replace(/\.NS$/, '');
  if (!raw) return null;
  const rows = await loadInstruments();
  const exact = rows.find(
    (r) =>
      r.exchange === 'NSE' &&
      r.instrument_type === 'EQ' &&
      (r.tradingsymbol === raw || r.name.toUpperCase() === raw)
  );
  return exact?.instrument_token ?? null;
}
