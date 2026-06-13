'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, AgentsRunResult, AgentCardPayload } from '@/lib/apiClient';
import { useAgentStore, AgentInsight } from '@/store/agentStore';

function signalFromText(s: string): AgentInsight['signal'] {
  const l = (s || '').toLowerCase();
  if (l.includes('positive') || l.includes('bullish') || l.includes('buy') || l.includes('up')) return 'BULLISH';
  if (l.includes('negative') || l.includes('bearish') || l.includes('sell') || l.includes('down')) return 'BEARISH';
  return 'NEUTRAL';
}

function confidenceFromCard(card: AgentCardPayload): number {
  if (card.metrics?.shock_probability != null) {
    return Math.round(Number(card.metrics.shock_probability) * 100);
  }
  if (card.signal === 'bullish' || card.signal === 'bearish') return 74;
  return 65;
}

function mapAgentCard(card: AgentCardPayload): AgentInsight {
  const sig = signalFromText(card.signal || card.output);
  return {
    id: card.id,
    agentName: card.name,
    signal: sig,
    confidence: confidenceFromCard(card),
    explanation: card.output,
    timestamp: new Date(),
    metrics: card.metrics as Record<string, number | string | null | undefined>,
    extras: {
      ...(card.extras || {}),
      macro_links: card.macro_links,
      risk_flags: card.risk_flags,
      action: card.action,
      called: card.called,
    },
    called: card.called,
  };
}

function mapAgentsResultToInsights(result: AgentsRunResult | null): AgentInsight[] {
  if (!result) return [];

  if (result.agents && Object.keys(result.agents).length > 0) {
    const order = [
      'news_scout',
      'macro_context',
      'technical',
      'market_reaction',
      'risk',
      'bull_research',
      'bear_research',
      'risk_committee',
      'debate',
      'shock',
      'decision',
    ];
    return order
      .filter((id) => result.agents?.[id])
      .map((id) => mapAgentCard(result.agents![id]));
  }

  // Legacy fallback if agents payload missing
  const insights: AgentInsight[] = [];
  const now = new Date();
  if (result.news_scout?.summary) {
    insights.push({
      id: 'news-scout',
      agentName: 'News Scout',
      signal: signalFromText(result.news_scout.spike_direction || ''),
      confidence: 70,
      explanation: result.news_scout.summary,
      timestamp: now,
    });
  }
  if (result.decision?.recommendation) {
    insights.push({
      id: 'decision',
      agentName: 'Decision',
      signal: signalFromText(result.decision.recommendation),
      confidence: 75,
      explanation: result.decision.recommendation,
      timestamp: now,
    });
  }
  return insights;
}

export type AgentInsightsOptions = {
  selectedIndicators?: string[];
  selectedPatterns?: string[];
  useSynthetic?: boolean;
};

/** Fetches agent insights from /api/agents/run/ and updates agent store */
export function useAgentInsights(ticker?: string, options?: AgentInsightsOptions) {
  const setInsights = useAgentStore((state) => state.setInsights);

  const { data: result, isLoading, isError, error, isFetching } = useQuery({
    queryKey: [
      'agent-insights',
      ticker,
      options?.useSynthetic,
      options?.selectedIndicators?.join(','),
      options?.selectedPatterns?.join(','),
    ],
    queryFn: () =>
      apiClient.getAgentInsights(ticker, {
        selectedIndicators: options?.selectedIndicators,
        selectedPatterns: options?.selectedPatterns,
        useSynthetic: options?.useSynthetic,
      }),
    enabled: Boolean(ticker),
    refetchInterval: options?.useSynthetic ? false : 300000,
    staleTime: options?.useSynthetic ? Infinity : 120000,
  });

  useEffect(() => {
    if (!ticker) return;
    if (isLoading && !result) return;
    if (!result) {
      if (isError) {
        setInsights([
          {
            id: 'api-error',
            agentName: 'Pipeline',
            signal: 'NEUTRAL',
            confidence: 0,
            explanation: 'Could not reach the agent API. Ensure Django is running (see banner above).',
            timestamp: new Date(),
          },
        ]);
      }
      return;
    }
    if (result.error) {
      setInsights([
        {
          id: 'agent-error',
          agentName: 'Pipeline',
          signal: 'NEUTRAL',
          confidence: 0,
          explanation: result.error,
          timestamp: new Date(),
        },
      ]);
      return;
    }
    setInsights(mapAgentsResultToInsights(result));
  }, [result, isLoading, isError, setInsights, ticker]);

  return { isLoading: isLoading || isFetching, result, isError, error };
}
