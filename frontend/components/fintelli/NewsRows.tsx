'use client';

import { formatDistanceToNow } from 'date-fns';
import type { NewsItem } from '@/lib/apiClient';
import { sentimentTag } from '@/lib/fintelli/format';

export function NewsRows({ items, limit }: { items: NewsItem[]; limit?: number }) {
  const list = limit ? items.slice(0, limit) : items;
  if (!list.length) {
    return <p style={{ padding: 18, fontSize: 13, color: 'var(--text-3)' }}>No live news available right now.</p>;
  }
  return (
    <>
      {list.map((n) => {
        const sent = sentimentTag(n.sentiment);
        const ts = n.timestamp instanceof Date ? n.timestamp : new Date(n.timestamp);
        return (
          <div key={n.id} className="ni">
            <div className="ni-h">{n.headline}</div>
            <div className="ni-meta">
              <span className={`tag ${sent.className}`}>{sent.label}</span>
              <span className="ni-src">{n.source}</span>
              <span className="ni-time">{formatDistanceToNow(ts, { addSuffix: true })}</span>
            </div>
          </div>
        );
      })}
    </>
  );
}
