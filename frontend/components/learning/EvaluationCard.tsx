'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { LearningEvaluation } from '@/lib/apiClient';

function MetricCard({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div
      className="rounded-lg p-3 text-center"
      style={{ background: 'var(--bg-inset)', border: '1px solid var(--border)' }}
    >
      <div className="text-xs uppercase tracking-wide mb-1" style={{ color: 'var(--text-3)' }}>
        {label}
      </div>
      <div className="text-2xl font-bold" style={{ color: 'var(--text-1)', fontFamily: 'JetBrains Mono' }}>
        {pct}%
      </div>
    </div>
  );
}

export function EvaluationCard({ evaluation }: { evaluation: LearningEvaluation }) {
  if (!evaluation) return null;

  return (
    <Card style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle style={{ fontSize: 15, color: 'var(--text-1)' }}>Pipeline Evaluation</CardTitle>
          <Badge
            className={
              evaluation.passed
                ? 'bg-green-500/20 text-green-400 border-green-500/30'
                : 'bg-red-500/20 text-red-400 border-red-500/30'
            }
          >
            {evaluation.passed ? 'PASSED' : 'FAILED'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <MetricCard label="Groundedness" value={evaluation.groundedness_score} />
          <MetricCard label="Relevance" value={evaluation.relevance_score} />
          <MetricCard label="Completion" value={evaluation.completion_score} />
        </div>
        <div className="text-center mb-3">
          <div className="text-xs uppercase" style={{ color: 'var(--text-3)' }}>Overall Score</div>
          <div
            className="text-4xl font-bold"
            style={{ color: 'var(--accent)', fontFamily: 'JetBrains Mono' }}
          >
            {evaluation.overall_score}
          </div>
        </div>
        {evaluation.safety_flags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 justify-center">
            {evaluation.safety_flags.map((flag) => (
              <Badge
                key={flag}
                variant="outline"
                className="bg-amber-500/10 text-amber-400 border-amber-500/30"
              >
                ⚠ {flag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
