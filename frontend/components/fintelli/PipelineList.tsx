'use client';

import type { PipelineStep } from '@/lib/apiClient';

const DEFAULT: PipelineStep[] = [
  { id: 'news_fetch', label: 'News ingestion', status: 'pending' },
  { id: 'news_scout', label: 'News Scout', status: 'pending' },
  { id: 'macro_context', label: 'Macro Context', status: 'pending' },
  { id: 'technical', label: 'Technical Analysis', status: 'pending' },
  { id: 'market_reaction', label: 'Market Reaction', status: 'pending' },
  { id: 'risk', label: 'Risk', status: 'pending' },
  { id: 'decision', label: 'Decision', status: 'pending' },
];

export function PipelineList({ steps, isLoading }: { steps?: PipelineStep[]; isLoading?: boolean }) {
  const display = steps?.length ? steps : DEFAULT;
  return (
    <>
      {display.map((step, index) => {
        let status = step.status;
        if (isLoading && status !== 'completed' && index === display.findIndex((s) => s.status !== 'completed')) {
          status = 'running';
        }
        const cls = status === 'completed' ? 'ps-done' : status === 'running' ? 'ps-run' : status === 'error' ? 'ps-pend' : 'ps-pend';
        const ico = status === 'completed' ? '✓' : status === 'running' ? '◌' : status === 'error' ? '!' : '○';
        return (
          <div key={step.id} className="pipe-step">
            <div className={`ps-ind ${cls}`}>{ico}</div>
            <div>
              <div className="ps-nm">{step.label}</div>
              <div className="ps-st">{step.summary || (status === 'running' ? 'Running…' : 'Pending')}</div>
            </div>
            <div className="ps-t">{step.duration_ms ? `${step.duration_ms}ms` : '—'}</div>
          </div>
        );
      })}
    </>
  );
}
