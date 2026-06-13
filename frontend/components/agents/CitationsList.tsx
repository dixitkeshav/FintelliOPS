'use client';

import { Badge } from '@/components/ui/badge';
import type { FintelliCitation } from '@/lib/apiClient';

export function CitationsList({ citations }: { citations: FintelliCitation[] }) {
  if (!citations.length) return null;

  const counts: Record<string, number> = {};
  citations.forEach((c) => {
    counts[c.citation] = (counts[c.citation] || 0) + 1;
  });

  return (
    <div className="rounded-xl border p-4 space-y-3">
      <h3 className="text-sm font-semibold">All Sources ({citations.length})</h3>
      <div className="space-y-2">
        {Object.entries(counts).map(([name, count]) => {
          const sample = citations.find((c) => c.citation === name);
          return (
            <div key={name} className="text-xs border-b border-border/50 pb-2 last:border-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-primary">{name}</span>
                {sample?.doc_type && (
                  <Badge variant="outline" className="text-[10px]">
                    {sample.doc_type}
                  </Badge>
                )}
                <span className="text-muted-foreground">used {count}×</span>
              </div>
              {sample?.content && (
                <p className="text-muted-foreground mt-1 line-clamp-2">{sample.content}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
