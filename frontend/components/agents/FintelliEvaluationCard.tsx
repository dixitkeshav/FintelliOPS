'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { FintelliEvaluation } from '@/lib/apiClient';

function Metric({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="rounded-lg border p-3 text-center bg-muted/30">
      <p className="text-xs uppercase text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono">{pct}%</p>
      <div className="h-1.5 bg-muted rounded-full mt-2 overflow-hidden">
        <div className="h-full bg-primary rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function FintelliEvaluationCard({ evaluation }: { evaluation: FintelliEvaluation }) {
  if (!evaluation) return null;
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Pipeline Evaluation</CardTitle>
          <Badge className={evaluation.passed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
            {evaluation.passed ? 'PASSED' : 'FAILED'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <Metric label="Groundedness" value={evaluation.groundedness_score} />
          <Metric label="Relevance" value={evaluation.relevance_score} />
          <Metric label="Completion" value={evaluation.completion_score} />
        </div>
        <div className="text-center mb-3">
          <p className="text-xs text-muted-foreground">Overall Score</p>
          <p className="text-4xl font-bold font-mono text-primary">{evaluation.overall_score}</p>
          <p className="text-xs text-muted-foreground mt-1">Agents: {evaluation.agents_completed}</p>
        </div>
        {evaluation.safety_flags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 justify-center">
            {evaluation.safety_flags.map((flag) => (
              <Badge key={flag} variant="outline" className="text-amber-400 border-amber-500/30">
                ⚠ {flag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
