'use client';

import { useEffect, useState } from 'react';
import { useAgentStore } from '@/store/agentStore';
import { useAgentInsights } from '@/hooks/useAgentInsights';
import { PipelineList } from '@/components/fintelli/PipelineList';
import { AgentCardsGrid } from '@/components/fintelli/AgentCardsGrid';
import { apiClient, type QuantCatalog } from '@/lib/apiClient';

const DEFAULT_INDICATORS = ['rsi', 'mfi', 'macd_hist', 'sma_20', 'sma_50', 'return_21d', 'volume_sma_ratio'];

export default function AgentsPage() {
  const [ticker, setTicker] = useState('RELIANCE');
  const [activeTicker, setActiveTicker] = useState<string | undefined>(undefined);
  const [catalog, setCatalog] = useState<QuantCatalog | null>(null);
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(DEFAULT_INDICATORS);
  const insights = useAgentStore((s) => s.insights);
  const { isLoading, result } = useAgentInsights(activeTicker, { selectedIndicators });

  useEffect(() => {
    apiClient.getQuantCatalog().then(setCatalog);
  }, []);

  const toggleIndicator = (id: string) => {
    setSelectedIndicators((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const sourceCounts = result?.news_sources;
  const sourceLabel = result?.news_source;

  return (
    <div>
      <div className="pg-head">
        <div className="pg-title">Agent Insights</div>
        <div className="pg-sub">
          Merged NewsAPI + Yahoo · FinBERT · extended technicals · /api/agents/run/
        </div>
      </div>

      <div className="card mb14">
        <div className="cb">
          <div className="row" style={{ flexWrap: 'wrap', alignItems: 'flex-end', gap: 10 }}>
            <div>
              <label className="flabel">Ticker Symbol</label>
              <input
                type="text"
                className="finput"
                style={{ width: 200 }}
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="RELIANCE or NIFTY"
              />
            </div>
            <button
              type="button"
              className="btn-pri"
              onClick={() => setActiveTicker(ticker.trim() || undefined)}
              disabled={isLoading}
            >
              {isLoading ? 'Running…' : '▶ Run Pipeline'}
            </button>
          </div>
          {sourceLabel && (
            <p className="pg-sub" style={{ marginTop: 10 }}>
              News: <strong>{sourceLabel}</strong>
              {sourceCounts && (
                <>
                  {' '}
                  · NewsAPI {sourceCounts.newsapi ?? 0} · Yahoo {sourceCounts.yfinance ?? 0}
                  {(sourceCounts.finnhub ?? 0) > 0 && <> · Finnhub {sourceCounts.finnhub}</>}
                  {(sourceCounts.alpha_vantage ?? 0) > 0 && <> · Alpha {sourceCounts.alpha_vantage}</>}
                </>
              )}
            </p>
          )}
        </div>
      </div>

      {catalog && (
        <div className="card mb14">
          <div className="ch">
            <div className="ct">📈 Technical indicators</div>
            <span className="badge badge-bl">{selectedIndicators.length} selected</span>
          </div>
          <div className="cb" style={{ maxHeight: 160, overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {catalog.indicators
                .filter((i) => i.computed !== false)
                .map((ind) => (
                  <button
                    key={ind.id}
                    type="button"
                    className={`badge ${selectedIndicators.includes(ind.id) ? 'badge-gr' : 'badge-am'}`}
                    style={{ cursor: 'pointer', border: 'none' }}
                    onClick={() => toggleIndicator(ind.id)}
                  >
                    {ind.name}
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      <div className="card mb14">
        <div className="ch">
          <div className="ct">🔄 Pipeline Status</div>
          {result?.article_count != null && <span className="badge badge-bl">{result.article_count} articles</span>}
        </div>
        <PipelineList steps={result?.pipeline} isLoading={isLoading} />
      </div>

      <div className="pg-sub mb14">📊 Agent Results</div>
      <AgentCardsGrid insights={insights} />
    </div>
  );
}
