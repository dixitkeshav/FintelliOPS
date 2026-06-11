export function fmtPrice(n: number, opts?: { currency?: string; decimals?: number }): string {
  const decimals = opts?.decimals ?? 2;
  if (!Number.isFinite(n)) return '—';
  const cur = opts?.currency;
  const body = n.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  if (cur === 'INR') return `₹${body}`;
  if (cur === 'USD') return `$${body}`;
  return body;
}

export function fmtPct(n: number, signed = true): string {
  if (!Number.isFinite(n)) return '—';
  const prefix = signed && n > 0 ? '+' : '';
  return `${prefix}${n.toFixed(2)}%`;
}

export function changeClass(up: boolean): string {
  return up ? 'up' : 'dn';
}

export function sentimentTag(s: string): { label: string; className: string } {
  const l = (s || '').toLowerCase();
  if (l === 'positive' || l === 'pos') return { label: 'POSITIVE', className: 'tag-pos' };
  if (l === 'negative' || l === 'neg') return { label: 'NEGATIVE', className: 'tag-neg' };
  return { label: 'NEUTRAL', className: 'tag-neu' };
}

export function signalBadge(sig: string): string {
  const s = (sig || '').toUpperCase();
  if (s === 'BULLISH') return 'badge-gr';
  if (s === 'BEARISH') return 'badge-rd';
  return 'badge-bl';
}
