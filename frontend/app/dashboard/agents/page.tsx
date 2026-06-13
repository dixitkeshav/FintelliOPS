'use client';

import { useEffect, useState } from 'react';
import { CitationsList } from '@/components/agents/CitationsList';
import { FintelliAgentCard } from '@/components/agents/FintelliAgentCard';
import { FintelliEvaluationCard } from '@/components/agents/FintelliEvaluationCard';
import { apiClient, type FintelliRunResult } from '@/lib/apiClient';

const SECTORS = ['Technology', 'Banking', 'Energy'];
const ANALYSTS = ['ANL-001', 'ANL-002'];
const AGENT_ORDER = [
  'NewsScoutAgent',
  'MacroContextAgent',
  'MarketReactionAgent',
  'RiskAgent',
  'DecisionAgent',
];

export default function AgentsPage() {
  const [query, setQuery] = useState('RBI holds repo rate, Nifty outlook');
  const [sector, setSector] = useState('Banking');
  const [analystId, setAnalystId] = useState('ANL-001');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<FintelliRunResult | null>(null);
  const [health, setHealth] = useState('');

  useEffect(() => {
    apiClient.getAgentsHealth().then((h) => {
      const llm = h.llm as { provider?: string } | undefined;
      const foundry = h.foundry_iq as { mode?: string } | undefined;
      setHealth(`${llm?.provider || 'unknown'} · ${foundry?.mode || 'local'}`);
    });
  }, []);

  const runPipeline = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setResult(null);
    try {
      const res = await apiClient.runFintelliPipeline(query.trim(), sector, analystId);
      setResult(res);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div className="pg-head">
        <div className="pg-title">FintelliOps Agent Pipeline</div>
        <div className="pg-sub">
          Foundry IQ + Fabric IQ + Work IQ · {health}
        </div>
      </div>

      <div className="card mb14">
        <div className="cb">
          <div className="row" style={{ flexWrap: 'wrap', alignItems: 'flex-end', gap: 12 }}>
            <div style={{ flex: 1, minWidth: 240 }}>
              <label className="flabel">Market query</label>
              <input
                type="text"
                className="finput"
                style={{ width: '100%' }}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="RBI rate hold, Nifty outlook"
              />
            </div>
            <div>
              <label className="flabel">Sector</label>
              <select className="finput" value={sector} onChange={(e) => setSector(e.target.value)}>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="flabel">Analyst</label>
              <select className="finput" value={analystId} onChange={(e) => setAnalystId(e.target.value)}>
                {ANALYSTS.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>
            <button type="button" className="btn-pri" onClick={runPipeline} disabled={isLoading || !query.trim()}>
              {isLoading ? 'Running…' : '▶ Run Pipeline'}
            </button>
          </div>
        </div>
      </div>

      {result?.error && (
        <div className="card mb14" style={{ borderColor: 'var(--red)' }}>
          <div className="cb" style={{ color: 'var(--red)' }}>{result.error}</div>
        </div>
      )}

      {result?.recommendation && (
        <div className="card mb14">
          <div className="cb">
            <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase' }}>Decision</div>
            <div style={{ fontSize: 14, color: 'var(--text-1)', marginTop: 4, whiteSpace: 'pre-wrap' }}>
              {result.recommendation.slice(0, 600)}
              {result.recommendation.length > 600 ? '…' : ''}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3 mb14">
        {AGENT_ORDER.map((name, idx) => {
          const agentResult = result?.agents?.[name];
          return (
            <div key={name}>
              {agentResult ? (
                <FintelliAgentCard agentName={name} result={agentResult} />
              ) : isLoading ? (
                <div className="card">
                  <div className="cb text-sm text-muted-foreground">
                    {name.replace(/Agent$/, '')} — running…
                  </div>
                </div>
              ) : null}
              {idx < AGENT_ORDER.length - 1 && agentResult && (
                <div className="text-center text-muted-foreground text-xs py-1">↓</div>
              )}
            </div>
          );
        })}
      </div>

      {result?.evaluation && <div className="mb14"><FintelliEvaluationCard evaluation={result.evaluation} /></div>}

      {result?.all_citations && result.all_citations.length > 0 && (
        <CitationsList citations={result.all_citations} />
      )}
    </div>
  );
}
