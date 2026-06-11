'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, AgentsRunResult } from '@/lib/apiClient';
import { useAgentStore, AgentInsight } from '@/store/agentStore';

function signalFromText(s: string): AgentInsight['signal'] {
  const l = (s || '').toLowerCase();
  if (l.includes('positive') || l.includes('bullish') || l.includes('up')) return 'BULLISH';
  if (l.includes('negative') || l.includes('bearish') || l.includes('down')) return 'BEARISH';
  return 'NEUTRAL';
}

function mapAgentsResultToInsights(result: AgentsRunResult | null): AgentInsight[] {
  if (!result) return [];
  const insights: AgentInsight[] = [];
  const now = new Date();

  if (result.news_scout?.summary) {
    insights.push({
      id: 'news-scout',
      agentName: 'News Scout',
      signal:
        result.news_scout.spike_direction === 'positive'
          ? 'BULLISH'
          : result.news_scout.spike_direction === 'negative'
            ? 'BEARISH'
            : 'NEUTRAL',
      confidence: result.news_scout.spike_detected ? 78 : 65,
      explanation: result.news_scout.summary,
      timestamp: now,
      metrics: result.news_scout.spike_detected ? { spike: 1 } : undefined,
    });
  }

  if (result.macro_context?.summary) {
    insights.push({
      id: 'macro',
      agentName: 'Macro',
      signal: signalFromText(result.macro_context.summary),
      confidence: 72,
      explanation: result.macro_context.summary,
      timestamp: now,
      metrics: result.macro_context.macro_links?.length
        ? { macroFactors: result.macro_context.macro_links.length }
        : undefined,
    });
  }

  if (result.technical?.summary) {
    const techSignal = (result.technical.signal || '').toLowerCase();
    insights.push({
      id: 'technical',
      agentName: 'Technical',
      signal: techSignal === 'bullish' ? 'BULLISH' : techSignal === 'bearish' ? 'BEARISH' : 'NEUTRAL',
      confidence: 70,
      explanation: result.technical.summary,
      timestamp: now,
      metrics: result.technical.indicators,
    });
  }

  if (result.market_reaction?.summary) {
    insights.push({
      id: 'market-reaction',
      agentName: 'Market Reaction',
      signal: signalFromText(result.market_reaction.summary),
      confidence: 71,
      explanation: result.market_reaction.summary,
      timestamp: now,
    });
  }

  if (result.risk?.summary) {
    insights.push({
      id: 'risk',
      agentName: 'Risk',
      signal: (result.risk.risk_flags?.length || 0) > 2 ? 'BEARISH' : 'NEUTRAL',
      confidence: 68,
      explanation: result.risk.summary,
      timestamp: now,
      metrics: result.risk.risk_flags?.length ? { flags: result.risk.risk_flags.length } : undefined,
    });
  }

  const decisionText = result.decision?.recommendation || result.recommendation || result.decision?.summary;
  if (decisionText) {
    insights.push({
      id: 'decision',
      agentName: 'Decision',
      signal: signalFromText(decisionText),
      confidence: 75,
      explanation: decisionText,
      timestamp: now,
    });
  }

  return insights;
}

export type AgentInsightsOptions = {
  selectedIndicators?: string[];
  selectedPatterns?: string[];
};

/** Fetches agent insights from /api/agents/run/ and updates agent store */
export function useAgentInsights(ticker?: string, options?: AgentInsightsOptions) {
  const setInsights = useAgentStore((state) => state.setInsights);

  const { data: result, isLoading, isError, error, isFetching } = useQuery({
    queryKey: ['agent-insights', ticker, options?.selectedIndicators?.join(','), options?.selectedPatterns?.join(',')],
    queryFn: () =>
      apiClient.getAgentInsights(ticker, {
        selectedIndicators: options?.selectedIndicators,
        selectedPatterns: options?.selectedPatterns,
      }),
    enabled: Boolean(ticker),
    refetchInterval: 300000,
    staleTime: 120000,
  });

  useEffect(() => {
    if (!ticker) return;
    if (isLoading && !result) return;
    if (!result) {
      if (isError) {
        setInsights([
          {
            id: 'api-error',
            agentName: 'News Scout',
            signal: 'NEUTRAL',
            confidence: 0,
            explanation:
              'Could not reach the agent API. Ensure Django is running (see banner above).',
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
          agentName: 'News Scout',
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
