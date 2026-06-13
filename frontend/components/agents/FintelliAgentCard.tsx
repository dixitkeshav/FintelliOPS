'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { FintelliAgentResult } from '@/lib/apiClient';

const IQ_COLORS: Record<string, string> = {
  foundry_iq: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  fabric_iq: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  work_iq: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
};

const IQ_LABELS: Record<string, string> = {
  foundry_iq: 'Foundry IQ',
  fabric_iq: 'Fabric IQ',
  work_iq: 'Work IQ',
};

function formatName(name: string): string {
  return name.replace(/Agent$/, '').replace(/([A-Z])/g, ' $1').trim();
}

export function FintelliAgentCard({
  agentName,
  result,
}: {
  agentName: string;
  result: FintelliAgentResult;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasError = !result.completed || !!result.error;

  return (
    <Card className={hasError ? 'border-red-500/50' : ''}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm">{formatName(agentName)}</CardTitle>
          <Badge
            variant={result.completed && !result.error ? 'default' : hasError ? 'destructive' : 'secondary'}
            className={result.completed && !result.error ? 'bg-green-500/20 text-green-400 border-green-500/30' : ''}
          >
            {result.completed && !result.error ? 'Complete' : hasError ? 'Error' : 'Pending'}
          </Badge>
        </div>
        {result.iq_layers_used.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {result.iq_layers_used.map((layer) => (
              <span
                key={layer}
                className={`text-xs px-2 py-0.5 rounded-full border ${IQ_COLORS[layer] || ''}`}
              >
                {IQ_LABELS[layer] || layer}
              </span>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {hasError && result.error && (
          <p className="text-sm text-red-400 mb-2">{result.error}</p>
        )}
        {!hasError && (
          <>
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary mb-2"
            >
              {expanded ? '▼ Hide output' : '▶ Show output'}
            </button>
            {expanded && (
              <p className="text-sm whitespace-pre-wrap text-muted-foreground leading-relaxed mb-3">
                {result.output}
              </p>
            )}
          </>
        )}
        {result.citations.length > 0 && (
          <div className="mt-2">
            <p className="text-xs font-semibold text-muted-foreground mb-1">
              Sources ({result.citations.length})
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.citations.map((c, i) => (
                <span
                  key={`${c.citation}-${i}`}
                  className="text-xs px-2 py-0.5 rounded border"
                  title={c.content?.slice(0, 120)}
                >
                  {c.citation} · {Math.round((c.score || 0) * (c.score <= 1 ? 100 : 1))}%
                </span>
              ))}
            </div>
          </div>
        )}
        {result.fabric_entities.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {result.fabric_entities.map((e) => (
              <span key={e} className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                {e}
              </span>
            ))}
          </div>
        )}
        {result.work_signals && Object.keys(result.work_signals).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {result.work_signals.briefing_time && (
              <Badge variant="outline" className="text-teal-400 border-teal-500/30">
                {String(result.work_signals.briefing_time)}
              </Badge>
            )}
            {result.work_signals.deliver_now != null && (
              <Badge variant="outline">
                deliver_now: {String(result.work_signals.deliver_now)}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
