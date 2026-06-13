'use client';

import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { LearningAgentResult } from '@/lib/apiClient';

export interface AgentCardProps {
  agentName: string;
  output: string;
  iqLayersUsed: string[];
  citations: { citation: string; content: string; score: number }[];
  fabricEntities: string[];
  workSignals: Record<string, unknown>;
  completed: boolean;
  error: string | null;
}

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

function formatAgentName(name: string): string {
  return name.replace(/Agent$/, '').replace(/([A-Z])/g, ' $1').trim();
}

export function LearningAgentCard({
  agentName,
  output,
  iqLayersUsed,
  citations,
  fabricEntities,
  workSignals,
  completed,
  error,
}: AgentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const hasError = !completed || !!error;

  return (
    <Card
      className={hasError ? 'border-red-500/50' : ''}
      style={{ background: 'var(--bg-card)', borderColor: hasError ? undefined : 'var(--border)' }}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle style={{ fontSize: 14, color: 'var(--text-1)' }}>
            {formatAgentName(agentName)}
          </CardTitle>
          <Badge
            variant={completed && !error ? 'default' : hasError ? 'destructive' : 'secondary'}
            className={completed && !error ? 'bg-green-500/20 text-green-400 border-green-500/30' : ''}
          >
            {completed && !error ? 'Complete' : hasError ? 'Error' : 'Pending'}
          </Badge>
        </div>
        {iqLayersUsed.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {iqLayersUsed.map((layer) => (
              <span
                key={layer}
                className={`text-xs px-2 py-0.5 rounded-full border ${IQ_COLORS[layer] || 'bg-gray-500/15 text-gray-400'}`}
              >
                {IQ_LABELS[layer] || layer}
              </span>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {hasError && error && (
          <p className="text-sm text-red-400 mb-2">{error}</p>
        )}
        {!hasError && (
          <>
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-left w-full mb-2"
              style={{ color: 'var(--accent)' }}
            >
              {expanded ? '▼ Hide output' : '▶ Show output'}
            </button>
            {expanded && (
              <div
                className="text-sm whitespace-pre-wrap rounded-md p-3 mb-3"
                style={{ background: 'var(--bg-inset)', color: 'var(--text-2)', lineHeight: 1.6 }}
              >
                {output}
              </div>
            )}
          </>
        )}
        {citations.length > 0 && (
          <div className="mt-2">
            <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--text-3)' }}>
              Sources ({citations.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {citations.map((c, i) => (
                <span
                  key={`${c.citation}-${i}`}
                  className="text-xs px-2 py-0.5 rounded border"
                  style={{ borderColor: 'var(--border)', color: 'var(--text-2)' }}
                  title={c.content.slice(0, 120)}
                >
                  {c.citation} · {Math.round((c.score || 0) * 100)}%
                </span>
              ))}
            </div>
          </div>
        )}
        {fabricEntities.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {fabricEntities.map((entity) => (
              <span
                key={entity}
                className="text-xs px-2 py-0.5 rounded"
                style={{ background: 'var(--bg-inset)', color: 'var(--text-3)' }}
              >
                {entity}
              </span>
            ))}
          </div>
        )}
        {Object.keys(workSignals).length > 0 && (
          <div className="text-xs mt-2" style={{ color: 'var(--text-3)' }}>
            Work signals: {JSON.stringify(workSignals).slice(0, 120)}
            {JSON.stringify(workSignals).length > 120 ? '…' : ''}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function agentResultToProps(
  agentName: string,
  result: LearningAgentResult
): AgentCardProps {
  return {
    agentName,
    output: result.output,
    iqLayersUsed: result.iq_layers_used,
    citations: result.citations,
    fabricEntities: result.fabric_entities,
    workSignals: result.work_signals,
    completed: result.completed,
    error: result.error,
  };
}
