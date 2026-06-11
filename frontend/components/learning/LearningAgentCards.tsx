'use client';

import type { LearningRunResult } from '@/lib/apiClient';

const AGENT_META: Record<string, { icon: string; iq: string }> = {
  learning_path_curator: { icon: '📚', iq: 'Foundry IQ + Fabric IQ' },
  study_plan_generator: { icon: '📅', iq: 'Fabric IQ + Work IQ' },
  engagement_agent: { icon: '🔔', iq: 'Work IQ' },
  assessment_agent: { icon: '✅', iq: 'Foundry IQ + Fabric IQ' },
  manager_insights: { icon: '📊', iq: 'Fabric IQ + Work IQ' },
};

export function LearningAgentCards({ result }: { result: LearningRunResult | null }) {
  if (!result) {
    return <p style={{ fontSize: 13, color: 'var(--text-3)' }}>Run the learning pipeline to see agent outputs.</p>;
  }

  const agents = [
    { key: 'learning_path_curator', label: 'Learning Path Curator', data: result.learning_path_curator },
    { key: 'study_plan_generator', label: 'Study Plan Generator', data: result.study_plan_generator },
    { key: 'engagement_agent', label: 'Engagement Agent', data: result.engagement_agent },
    { key: 'assessment_agent', label: 'Assessment Agent', data: result.assessment_agent },
    { key: 'manager_insights', label: 'Manager Insights', data: result.manager_insights },
  ];

  return (
    <div className="g3">
      {agents.map(({ key, label, data }) => {
        const meta = AGENT_META[key];
        const passed = key === 'assessment_agent' && result.assessment_agent?.assessment?.passed;
        const badge = passed ? 'badge-gr' : key === 'assessment_agent' ? 'badge-am' : 'badge-bl';
        const badgeText =
          key === 'assessment_agent'
            ? passed
              ? 'EXAM READY'
              : 'PREPARE'
            : meta.iq.split(' ')[0].toUpperCase();

        return (
          <div key={key} className="card">
            <div className="ch">
              <div className="ct">
                {meta.icon} {label}
              </div>
              <span className={`badge ${badge}`}>{badgeText}</span>
            </div>
            <div className="cb">
              <div style={{ fontSize: 10, color: 'var(--text-4)', marginBottom: 8, textTransform: 'uppercase' }}>
                {meta.iq}
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 }}>{data?.summary}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
