'use client';

import { PipelineStep } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Loader2, Newspaper, AlertCircle } from 'lucide-react';

const DEFAULT_STEPS: PipelineStep[] = [
  { id: 'news_fetch', label: 'News ingestion', status: 'pending' },
  { id: 'news_scout', label: 'News Scout', status: 'pending' },
  { id: 'macro_context', label: 'Macro Context', status: 'pending' },
  { id: 'technical', label: 'Technical Analysis', status: 'pending' },
  { id: 'market_reaction', label: 'Market Reaction', status: 'pending' },
  { id: 'risk', label: 'Risk', status: 'pending' },
  { id: 'decision', label: 'Decision', status: 'pending' },
];

interface AgentPipelineProps {
  steps?: PipelineStep[];
  isLoading?: boolean;
  articleCount?: number;
  newsSource?: string;
  ticker?: string | null;
}

function StepIcon({ status, isLoading }: { status: PipelineStep['status']; isLoading?: boolean }) {
  if (isLoading || status === 'running') {
    return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
  }
  if (status === 'completed') {
    return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
  }
  if (status === 'error') {
    return <AlertCircle className="h-4 w-4 text-destructive" />;
  }
  return <Circle className="h-4 w-4 text-muted-foreground" />;
}

export function AgentPipeline({
  steps,
  isLoading,
  articleCount,
  newsSource,
  ticker,
}: AgentPipelineProps) {
  const displaySteps = steps?.length ? steps : DEFAULT_STEPS;

  return (
    <div className="rounded-xl border border-border/50 bg-card/40 p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Newspaper className="h-4 w-4 text-primary" />
          Agent pipeline
        </h2>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          {articleCount != null && <span>{articleCount} articles</span>}
          {newsSource && <span>· source: {newsSource.replace(/_/g, ' ')}</span>}
          {ticker && <span>· ticker: {ticker}</span>}
          {isLoading && <span className="text-primary">· running…</span>}
        </div>
      </div>
      <ol className="space-y-0">
        {displaySteps.map((step, index) => {
          const running = isLoading && step.status !== 'completed' && index === displaySteps.findIndex((s) => s.status !== 'completed');
          const status = running ? 'running' : step.status;
          return (
            <li key={step.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <StepIcon status={status} isLoading={running} />
                {index < displaySteps.length - 1 && (
                  <div
                    className={cn(
                      'w-px flex-1 min-h-[2rem] my-1',
                      status === 'completed' ? 'bg-emerald-500/40' : 'bg-border'
                    )}
                  />
                )}
              </div>
              <div className="pb-4 flex-1 min-w-0">
                <p className="text-sm font-medium">{step.label}</p>
                {step.summary && (
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed line-clamp-3">
                    {step.summary}
                  </p>
                )}
                {step.duration_ms != null && step.duration_ms > 0 && status === 'completed' && (
                  <p className="text-[10px] text-muted-foreground/80 mt-0.5">{step.duration_ms} ms</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
