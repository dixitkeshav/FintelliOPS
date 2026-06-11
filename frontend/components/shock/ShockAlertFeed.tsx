'use client';

export interface ShockAlertItem {
  score?: number;
  cause?: string;
  headline?: string;
  hedge?: string;
  source?: string;
  timestamp?: string;
  fired_at?: string;
}

const causeColors: Record<string, string> = {
  policy: '#534AB7',
  macro: '#0F6E56',
  geopolitical: '#993C1D',
  technical: '#854F0B',
  corporate: '#185FA5',
  unknown: '#5F5E5A',
};

interface ShockAlertFeedProps {
  alerts: ShockAlertItem[];
}

export function ShockAlertFeed({ alerts }: ShockAlertFeedProps) {
  return (
    <div className="flex flex-col gap-2.5">
      {alerts.length === 0 && (
        <p className="text-sm text-muted-foreground">No alerts fired yet.</p>
      )}
      {alerts.map((a, i) => {
        const cause = (a.cause || 'unknown').toLowerCase();
        const ts = a.timestamp || a.fired_at;
        return (
          <div
            key={`${ts}-${i}`}
            className="rounded-lg bg-muted/50 px-4 py-3 border-l-[3px]"
            style={{ borderLeftColor: causeColors[cause] || '#888' }}
          >
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium">{cause.toUpperCase()}</span>
              <span className="text-xs text-muted-foreground">
                {ts ? new Date(ts).toLocaleTimeString() : ''}
                {a.score != null ? ` · ${a.score}` : ''}
              </span>
            </div>
            <p className="text-sm mb-1.5">{a.headline}</p>
            {a.source && (
              <p className="text-xs text-muted-foreground mb-1">Source: {a.source}</p>
            )}
            <p className="text-xs text-muted-foreground m-0">{a.hedge}</p>
          </div>
        );
      })}
    </div>
  );
}
