'use client';

import type { AgentInsight } from '@/store/agentStore';
import { signalBadge } from '@/lib/fintelli/format';

const ICONS: Record<string, string> = {
  'News Scout': '📰',
  'Macro Context': '🌐',
  Macro: '🌐',
  'Technical Analysis': '📉',
  Technical: '📉',
  Risk: '⚠️',
  'Market Reaction': '🏦',
  'Bull Research': '🐂',
  'Bear Research': '🐻',
  'Risk Committee': '🛡️',
  'Debate Facilitator': '⚖️',
  Debate: '⚖️',
  'Shock Predictor': '⚡',
  Shock: '⚡',
  Decision: '🎯',
};

export function AgentCardsGrid({ insights }: { insights: AgentInsight[] }) {
  if (!insights.length) {
    return <p style={{ fontSize: 13, color: 'var(--text-3)' }}>Run the agent pipeline to see results.</p>;
  }
  return (
    <div className="g3">
      {insights.map((a) => {
        const fc = a.signal === 'BULLISH' ? 'var(--green)' : a.signal === 'BEARISH' ? 'var(--red)' : 'var(--accent)';
        const extras = a.extras || {};
        const macroLinks = extras.macro_links as string[] | undefined;
        const riskFlags = extras.risk_flags as string[] | undefined;
        const action = extras.action as string | undefined;

        return (
          <div key={a.id} className="card">
            <div className="ch">
              <div className="ct">
                {ICONS[a.agentName] || '🤖'} {a.agentName}
              </div>
              <span className={`badge ${signalBadge(a.signal)}`}>{a.signal}</span>
            </div>
            <div className="cb">
              {a.called !== false && (
                <div style={{ fontSize: 10, color: 'var(--green)', marginBottom: 6, textTransform: 'uppercase' }}>
                  ✓ Agent called
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-3)', marginBottom: 5 }}>
                <span>Confidence</span>
                <span style={{ fontWeight: 700, color: 'var(--text-1)' }}>{a.confidence}%</span>
              </div>
              <div style={{ height: 4, background: 'var(--bg-inset)', borderRadius: 2, marginBottom: 12, overflow: 'hidden' }}>
                <div style={{ width: `${a.confidence}%`, height: '100%', background: fc, borderRadius: 2 }} />
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-2)', lineHeight: 1.7 }}>{a.explanation}</div>
              {action && (
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-3)' }}>
                  Action: <strong style={{ color: 'var(--text-1)' }}>{action}</strong>
                </div>
              )}
              {macroLinks && macroLinks.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-3)' }}>
                  Macro: {macroLinks.slice(0, 3).join(' · ')}
                </div>
              )}
              {riskFlags && riskFlags.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--red)' }}>
                  Risks: {riskFlags.slice(0, 2).join(' · ')}
                </div>
              )}
              {a.metrics && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 12 }}>
                  {Object.entries(a.metrics)
                    .filter(([, v]) => v != null)
                    .slice(0, 4)
                    .map(([k, v]) => (
                      <div key={k}>
                        <div style={{ fontSize: 9.5, color: 'var(--text-3)', textTransform: 'uppercase' }}>{k}</div>
                        <div style={{ fontFamily: 'JetBrains Mono', fontSize: 12.5, fontWeight: 600 }}>{String(v)}</div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
