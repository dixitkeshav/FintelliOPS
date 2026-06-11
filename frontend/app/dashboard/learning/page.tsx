'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PipelineList } from '@/components/fintelli/PipelineList';
import { LearningAgentCards } from '@/components/learning/LearningAgentCards';
import {
  apiClient,
  type LearningRunResult,
  type SyntheticLearner,
} from '@/lib/apiClient';

const DEFAULT_TOPICS = 'Azure fundamentals, Exam preparation';

export default function LearningPage() {
  const [learnerId, setLearnerId] = useState('L-1001');
  const [team, setTeam] = useState('TEAM-A');
  const [topics, setTopics] = useState(DEFAULT_TOPICS);
  const [activeRun, setActiveRun] = useState<{
    learner_id: string;
    team: string;
    topics: string[];
  } | null>(null);

  const { data: learners = [] } = useQuery({
    queryKey: ['learning-learners'],
    queryFn: () => apiClient.getLearningLearners(),
  });

  const { data: teams = [] } = useQuery({
    queryKey: ['learning-teams'],
    queryFn: () => apiClient.getLearningTeams(),
  });

  const { data: health } = useQuery({
    queryKey: ['learning-health'],
    queryFn: () => apiClient.getLearningHealth(),
  });

  const { data: result, isLoading } = useQuery({
    queryKey: ['learning-run', activeRun],
    queryFn: () =>
      activeRun
        ? apiClient.runLearningPipeline({
            learner_id: activeRun.learner_id,
            team: activeRun.team,
            topics: activeRun.topics,
          })
        : Promise.resolve(null),
    enabled: !!activeRun,
  });

  useEffect(() => {
    const learner = learners.find((l) => l.learner_id === learnerId);
    if (learner && teams.length) {
      const teamForLearner =
        learnerId === 'L-1001' || learnerId === 'L-1002'
          ? 'TEAM-A'
          : learnerId === 'L-1003' || learnerId === 'L-1004'
            ? 'TEAM-B'
            : 'TEAM-C';
      if (teams.includes(teamForLearner)) setTeam(teamForLearner);
    }
  }, [learnerId, learners, teams]);

  const selectedLearner = learners.find((l) => l.learner_id === learnerId);

  const handleRun = () => {
    setActiveRun({
      learner_id: learnerId,
      team,
      topics: topics.split(',').map((t) => t.trim()).filter(Boolean),
    });
  };

  return (
    <div>
      <div className="pg-head">
        <div className="pg-title">Enterprise Learning Certification</div>
        <div className="pg-sub">
          Microsoft Foundry Reasoning Agents · Work IQ · Foundry IQ · Fabric IQ · Synthetic data only
        </div>
      </div>

      {health && (
        <div className="card mb14">
          <div className="cb" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <span className="badge badge-gr">{health.status}</span>
            <span className="badge badge-bl">{health.agents?.length ?? 5} agents</span>
            <span className="badge badge-bl">3 IQ layers</span>
            <span className="badge badge-am">Demo data only</span>
          </div>
        </div>
      )}

      <div className="card mb14">
        <div className="cb">
          <div className="row" style={{ flexWrap: 'wrap', alignItems: 'flex-end', gap: 10 }}>
            <div>
              <label className="flabel">Learner (synthetic)</label>
              <select
                className="finput"
                style={{ width: 220 }}
                value={learnerId}
                onChange={(e) => setLearnerId(e.target.value)}
              >
                {learners.map((l: SyntheticLearner) => (
                  <option key={l.learner_id} value={l.learner_id}>
                    {l.learner_id} — {l.role} ({l.certification})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="flabel">Team</label>
              <select
                className="finput"
                style={{ width: 120 }}
                value={team}
                onChange={(e) => setTeam(e.target.value)}
              >
                {teams.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <label className="flabel">Study topics (comma-separated)</label>
              <input
                type="text"
                className="finput"
                style={{ width: '100%' }}
                value={topics}
                onChange={(e) => setTopics(e.target.value)}
              />
            </div>
            <button type="button" className="btn-pri" onClick={handleRun} disabled={isLoading}>
              {isLoading ? 'Running…' : '▶ Run Learning Pipeline'}
            </button>
          </div>
          {selectedLearner && (
            <p className="pg-sub" style={{ marginTop: 10 }}>
              {selectedLearner.role} · {selectedLearner.certification} · Practice{' '}
              {selectedLearner.practice_score_avg}% · {selectedLearner.hours_studied}h studied · Prior:{' '}
              {selectedLearner.exam_outcome}
            </p>
          )}
        </div>
      </div>

      <div className="card mb14">
        <div className="ch">
          <div className="ct">🔄 Multi-Agent Pipeline</div>
          {result?.exam_ready != null && (
            <span className={`badge ${result.exam_ready ? 'badge-gr' : 'badge-am'}`}>
              {result.exam_ready ? 'Exam ready' : 'Needs preparation'}
            </span>
          )}
        </div>
        <PipelineList steps={result?.pipeline} isLoading={isLoading} />
        {result?.recommendation && (
          <div className="cb" style={{ borderTop: '1px solid var(--border)', paddingTop: 12 }}>
            <strong>Next step:</strong> {result.recommendation}
          </div>
        )}
      </div>

      <div className="pg-sub mb14">🧠 Agent Results (IQ-grounded)</div>
      <LearningAgentCards result={(result as LearningRunResult) ?? null} />
    </div>
  );
}
