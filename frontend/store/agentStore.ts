import { create } from 'zustand';

export interface AgentInsight {
  id: string;
  agentName: string;
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  explanation: string;
  timestamp: Date;
  metrics?: Record<string, number | string | null | undefined>;
  extras?: Record<string, unknown>;
  called?: boolean;
}

interface AgentState {
  insights: AgentInsight[];
  addInsight: (insight: AgentInsight) => void;
  updateInsight: (id: string, data: Partial<AgentInsight>) => void;
  clearInsights: () => void;
  setInsights: (insights: AgentInsight[]) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  insights: [],
  addInsight: (insight) =>
    set((state) => ({ insights: [insight, ...state.insights] })),
  updateInsight: (id, data) =>
    set((state) => ({
      insights: state.insights.map((insight) =>
        insight.id === id ? { ...insight, ...data } : insight
      ),
    })),
  clearInsights: () => set({ insights: [] }),
  setInsights: (insights) => set({ insights }),
}));
