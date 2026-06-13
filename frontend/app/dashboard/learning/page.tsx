'use client';

import { useCallback, useEffect, useState } from 'react';
import { EvaluationCard } from '@/components/learning/EvaluationCard';
import { LearningAgentCard, agentResultToProps } from '@/components/learning/LearningAgentCard';
import { apiClient, type LearningRunResult } from '@/lib/apiClient';

const LEARNERS = ['L-1001', 'L-1002', 'L-1003'];
const TEAMS = ['TEAM-A', 'TEAM-B'];
const AGENT_ORDER = [
  'LearningPathCuratorAgent',
  'StudyPlanGeneratorAgent',
  'EngagementAgent',
  'AssessmentAgent',
  'ManagerInsightsAgent',
];

export default function LearningPage() {
  const [learnerId, setLearnerId] = useState('L-1001');
  const [teamId, setTeamId] = useState('TEAM-A');
  const [topics, setTopics] = useState<string[]>(['Azure Functions', 'AZ-204 exam prep']);
  const [availableTopics, setAvailableTopics] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<LearningRunResult | null>(null);
  const [visibleAgents, setVisibleAgents] = useState(0);
  const [health, setHealth] = useState<string>('');

  useEffect(() => {
    apiClient.getLearningTopics().then((r) => setAvailableTopics(r.topics || []));
    apiClient.getLearningHealth().then((h) => {
      setHealth(`${h.llm_provider} · ${h.azure_search_mode}`);
    });
  }, []);

  const toggleTopic = (topic: string) => {
    setTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const runPipeline = useCallback(async () => {
    if (!topics.length) return;
    setIsLoading(true);
    setResult(null);
    setVisibleAgents(0);

    const interval = setInterval(() => {
      setVisibleAgents((v) => Math.min(v + 1, AGENT_ORDER.length));
    }, 800);

    try {
      const res = await apiClient.runLearningPipeline(learnerId, teamId, topics);
      setResult(res);
      setVisibleAgents(AGENT_ORDER.length);
    } finally {
      clearInterval(interval);
      setIsLoading(false);
    }
  }, [learnerId, teamId, topics]);

  return (
    <div>
      <div className="pg-head">
        <div className="pg-title">Enterprise Learning Certification</div>
        <div className="pg-sub">
          5-agent pipeline · Foundry IQ + Fabric IQ + Work IQ · {health}
        </div>
      </div>

      <div className="card mb14">
        <div className="cb">
          <div className="row" style={{ flexWrap: 'wrap', alignItems: 'flex-end', gap: 12 }}>
            <div>
              <label className="flabel">Learner</label>
              <select
                className="finput"
                value={learnerId}
                onChange={(e) => setLearnerId(e.target.value)}
              >
                {LEARNERS.map((id) => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="flabel">Team</label>
              <select
                className="finput"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
              >
                {TEAMS.map((id) => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="btn-pri"
              onClick={runPipeline}
              disabled={isLoading || topics.length === 0}
            >
              {isLoading ? 'Running pipeline…' : '▶ Run Pipeline'}
            </button>
          </div>

          <div style={{ marginTop: 14 }}>
            <label className="flabel">Topics</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
              {availableTopics.slice(0, 12).map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => toggleTopic(topic)}
                  className="badge"
                  style={{
                    cursor: 'pointer',
                    background: topics.includes(topic) ? 'var(--accent-soft)' : 'var(--bg-inset)',
                    color: topics.includes(topic) ? 'var(--accent)' : 'var(--text-3)',
                    border: topics.includes(topic) ? '1px solid var(--accent)' : '1px solid var(--border)',
                  }}
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {isLoading && (
        <p style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 14 }}>
          Running agents… {visibleAgents}/{AGENT_ORDER.length} visible
        </p>
      )}

      {result?.error && (
        <div className="card mb14" style={{ borderColor: 'var(--red)' }}>
          <div className="cb" style={{ color: 'var(--red)' }}>{result.error}</div>
        </div>
      )}

      {result?.recommendation && (
        <div className="card mb14">
          <div className="cb">
            <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase' }}>
              Recommendation
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-1)', marginTop: 4 }}>
              {result.recommendation}
            </div>
            {result.learner && (
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6 }}>
                {result.learner.role} · {result.learner.certification} ·{' '}
                {result.learner.practice_score_avg}% practice avg
              </div>
            )}
          </div>
        </div>
      )}

      <div className="g2" style={{ marginBottom: 14 }}>
        {AGENT_ORDER.slice(0, isLoading ? visibleAgents : result ? AGENT_ORDER.length : 0).map(
          (name) => {
            const agentResult = result?.agents?.[name];
            if (!agentResult) {
              return (
                <div key={name} className="card">
                  <div className="cb" style={{ color: 'var(--text-3)', fontSize: 13 }}>
                    {name.replace(/Agent$/, '')} — running…
                  </div>
                </div>
              );
            }
            return (
              <LearningAgentCard key={name} {...agentResultToProps(name, agentResult)} />
            );
          }
        )}
      </div>

      {result?.evaluation && <EvaluationCard evaluation={result.evaluation} />}

      {result?.all_citations && result.all_citations.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="ch">
            <div className="ct">All Citations ({result.all_citations.length})</div>
          </div>
          <div className="cb">
            {result.all_citations.map((c, i) => (
              <div key={`${c.citation}-${i}`} style={{ marginBottom: 10, fontSize: 12 }}>
                <strong style={{ color: 'var(--accent)' }}>{c.citation}</strong>
                <span style={{ color: 'var(--text-3)', marginLeft: 8 }}>
                  score {Math.round((c.score || 0) * 100)}%
                </span>
                <div style={{ color: 'var(--text-2)', marginTop: 4, lineHeight: 1.5 }}>
                  {c.content.slice(0, 200)}…
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
