import { djangoApiUrl } from '@/lib/apiBase';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function djangoFetch(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(djangoApiUrl(path), {
    ...init,
    cache: 'no-store',
  });
  return response;
}

async function djangoJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await djangoFetch(path, init);
  const data = (await response.json().catch(() => ({}))) as T & { error?: string; detail?: string };
  if (!response.ok) {
    // Many dashboard calls are best-effort (polling). Return the parsed body instead
    // of throwing to avoid noisy stack traces during backend warmup/outages.
    // Callers can check `error` / `detail` fields when they care.
    return data as unknown as T;
  }
  return data;
}

export interface NewsItem {
  id: string;
  headline: string;
  source: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
  timestamp: Date;
  symbols: string[];
  url?: string;
  imageUrl?: string;
}

export interface ChartDataPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SentimentChartData {
  distribution: { labels: string[]; data: number[] };
  trend: {
    labels: string[];
    positive: number[];
    negative: number[];
  };
}

export interface LiveTickerItem {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
}

export interface PipelineStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  summary?: string;
  duration_ms?: number;
}

export interface SyntheticLearner {
  learner_id: string;
  role: string;
  certification: string;
  practice_score_avg: number;
  hours_studied: number;
  exam_outcome: string;
}

export interface LearningAgentOutput {
  summary?: string;
  iq_layers?: string[];
}

export interface LearningRunResult {
  error?: string;
  learner_id: string;
  team: string;
  topics: string[];
  learning_path_curator: LearningAgentOutput & {
    learning_path?: {
      certification?: string;
      role?: string;
      citations?: string[];
    };
  };
  study_plan_generator: LearningAgentOutput & {
    study_plan?: {
      daily_target_hours?: number;
      remaining_hours?: number;
      readiness_score?: number;
    };
  };
  engagement_agent: LearningAgentOutput & {
    engagement?: {
      reminders?: Array<{ window: string; message: string }>;
      capacity_risk?: string;
    };
  };
  assessment_agent: LearningAgentOutput & {
    assessment?: {
      passed?: boolean;
      practice_score_avg?: number;
      pass_threshold?: number;
      questions?: Array<{ id: string; question: string; citation: string }>;
    };
  };
  manager_insights: LearningAgentOutput & {
    manager_insights?: {
      exam_ready_count?: number;
      learner_count?: number;
      average_readiness?: number;
      at_risk_learners?: string[];
    };
  };
  recommendation?: string;
  exam_ready?: boolean;
  pipeline?: PipelineStep[];
  iq_layers?: { work_iq: boolean; foundry_iq: boolean; fabric_iq: boolean };
  foundry?: { configured: boolean; mode: string };
  data_notice?: string;
}

export interface ShockScorePayload {
  score: number;
  cause: string;
  headline: string;
  source: string;
  hedge: string;
  timestamp: string;
}

export interface ShockHistoryRow {
  date: string;
  direction: string;
  magnitude: number;
  intraday_range: number;
  cause_type: string;
  cause_summary?: string;
  headline: string;
  index?: string;
  news_evidence?: Array<{ title?: string; summary?: string; source?: string; url?: string }>;
  threshold_points?: number;
}

export interface QuantCatalogItem {
  id: string;
  name: string;
  category?: string;
  computed?: boolean;
}

export interface QuantCatalog {
  indicators: QuantCatalogItem[];
  candlestick_patterns: QuantCatalogItem[];
  strategies: Array<{ id: string; name: string; description?: string }>;
  indicator_count?: number;
  pattern_count?: number;
  strategy_count?: number;
}

export interface AgentsRunResult {
  error?: string;
  news_scout: { summary?: string; spike_detected?: boolean; spike_direction?: string };
  macro_context: { summary?: string; macro_links?: string[] };
  technical?: {
    summary?: string;
    signal?: string;
    indicators?: Record<string, number | null>;
    candlestick_patterns?: Array<{ id: string; name: string }>;
  };
  market_reaction: { summary?: string; historical_reaction?: string };
  risk: { summary?: string; risk_flags?: string[] };
  shock?: {
    shock_probability?: number;
    trigger_cause?: string;
    summary?: string;
    suggested_hedge?: string;
  };
  decision: { summary?: string; recommendation?: string };
  recommendation?: string;
  pipeline?: PipelineStep[];
  article_count?: number;
  news_source?: string;
  news_sources?: Record<string, number>;
  ticker?: string | null;
  selected_indicators?: string[];
}

export type BacktestMode = 'equity_intraday' | 'equity_delivery' | 'options' | 'legacy';

export interface BacktestTradeNews {
  title: string;
  summary?: string;
  url?: string;
  source?: string;
  sentiment?: string;
  sentiment_score?: number;
  relevance?: string | number;
}

export interface BacktestTradeExecution {
  decision: string;
  entry_date: string;
  entry_time: string;
  exit_date: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  stop_loss_price?: number | null;
  take_profit_price?: number | null;
  stop_loss_pct?: number | null;
  take_profit_pct?: number | null;
  strike?: number;
  strike_step?: number;
  strike_source?: string | null;
  option_expiry?: string | null;
  option_structure?: string | null;
  option_legs?: Array<{ leg: string; strike: number }> | null;
  chain_source?: string | null;
  session?: string;
  bar_ohlc?: { open: number; high: number; low: number; close: number };
}

export interface BacktestTrade {
  date: string;
  action: string;
  hold_type?: string;
  pnl_pct: number;
  execution?: BacktestTradeExecution;
  news: BacktestTradeNews[];
  metrics: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
    day_return_pct?: number;
    rsi?: number | null;
    mfi?: number | null;
    macd_hist?: number | null;
    bb_pct?: number | null;
    vwap_dist?: number | null;
    zigzag_trend?: number | null;
    avg_news_sentiment?: number;
  };
  reason: string;
  rules_matched?: unknown[];
}

export interface BacktestStrategyTemplate {
  id: string;
  name: string;
  description: string;
  mode_hint?: string;
  requires_news?: boolean;
  options_structure?: string;
}

export interface BacktestResult {
  error?: string;
  ticker?: string;
  mode?: string;
  period?: {
    start?: string;
    end?: string;
    days_requested?: number;
    start_date?: string | null;
    end_date?: string | null;
    bars_in_range?: number;
    label?: string;
  };
  only_news_events?: boolean;
  price_source?: string;
  kite_used?: boolean;
  kite_note?: string;
  yfinance_symbol?: string;
  sentiment_source?: string;
  price_only_sharpe?: number | null;
  strategy_sharpe?: number | null;
  ic?: number | null;
  total_return_price?: number | null;
  total_return_strategy?: number | null;
  num_days?: number;
  options_chain?: {
    available: boolean;
    proxy?: boolean;
    source?: string;
    note?: string;
    expiries_count?: number;
    chain_rows?: number;
    nearest_expiry?: string | null;
    symbol_checked?: string;
    symbols_tried?: string[];
    error?: string;
  };
  strategy?: {
    id?: string;
    name?: string;
    description?: string;
    parsed_rules?: unknown[];
    custom_prompt?: string;
    options_structure?: string;
    compile?: CompiledStrategy;
  };
  summary?: {
    total_trades: number;
    winning_trades: number;
    win_rate_pct: number;
    total_return_pct: number;
    news_articles_considered: number;
    trading_days_in_sample: number;
  };
  trades?: BacktestTrade[];
  news_pool?: Array<BacktestTradeNews & { date?: string }>;
  templates?: BacktestStrategyTemplate[];
  recent_price_context?: {
    approx_return_1m?: number | null;
    approx_return_3m?: number | null;
    annualized_volatility?: number | null;
  };
  explanation?: {
    headline?: string;
    recent_trend?: string;
    quarterly_context?: string;
    why_price_might_move?: string[];
    methodology?: string;
    strategy_note?: string;
    disclaimer?: string;
  };
}

export interface CompiledStrategy {
  rules?: unknown[];
  action?: string;
  options_structure?: string | null;
  risk_reward?: { stop_loss_pct?: number; take_profit_pct?: number };
  normalized_prompt?: string;
  fixes_applied?: string[];
  source?: string;
}

export interface BacktestRunOptions {
  mode?: BacktestMode;
  strategyId?: string;
  strategyPrompt?: string;
  onlyNewsEvents?: boolean;
  days?: number;
  startDate?: string;
  endDate?: string;
  periodLabel?: string;
  customOnly?: boolean;
  useGroqCompile?: boolean;
  compiledRules?: unknown[];
  useAlphaSentiment?: boolean;
  useKite?: boolean;
  kiteCredentials?: { apiKey?: string; accessToken?: string };
}

export interface ScannerResultItem {
  symbol: string;
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  sentiment: 'positive' | 'negative' | 'neutral' | string;
  sentiment_score: number;
  momentum: number;
  sentiment_counts: {
    positive: number;
    negative: number;
    neutral: number;
    total: number;
  };
}

export interface ScannerResponse {
  period: string;
  results: ScannerResultItem[];
  source?: string;
}

export interface OptionsChainSide {
  bid: number | null;
  ask: number | null;
  lastPrice: number | null;
  impliedVolatility: number | null;
  openInterest: number | null;
  volume: number | null;
}

export interface OptionsChainRow {
  strike: number;
  call: OptionsChainSide;
  put: OptionsChainSide;
}

export interface OptionsChainResponse {
  symbol: string;
  expiry: string | null;
  expiries: string[];
  data: OptionsChainRow[];
  error?: string;
  /** Backend: yfinance | finnhub */
  source?: string;
}

export type IntradayDecisionType = 'BUY' | 'SELL' | 'NO_TRADE';

export interface IntradayTradeDecision {
  symbol: string;
  decision: IntradayDecisionType;
  reason: string;
  confidence: number;
  hold_minutes: number;
  entry_price: number | null;
  stop_loss: number | null;
  target_price: number | null;
  expected_move_pct: number;
  expected_profit_pct: number;
  risk_reward?: number | null;
  generated_at: string;
  price_source?: string;
}

function isSentiment(x: string): x is 'positive' | 'negative' | 'neutral' {
  return x === 'positive' || x === 'negative' || x === 'neutral';
}

export const apiClient = {
  /** Ping Django via proxy (live-ticker is lightweight). */
  async checkHealth(): Promise<{ ok: boolean; message?: string }> {
    try {
      const response = await djangoFetch('/api/live-ticker/');
      if (response.ok) return { ok: true };
      const data = await response.json().catch(() => ({}));
      return {
        ok: false,
        message: (data as { error?: string }).error || `Backend returned ${response.status}`,
      };
    } catch (e) {
      return {
        ok: false,
        message: e instanceof Error ? e.message : 'Backend unreachable',
      };
    }
  },

  /** Fetch news from /api/fetch-news/ (NewsAPI primary, Alpha Vantage fallback) */
  async getNews(limit = 50): Promise<NewsItem[]> {
    try {
      const data = await djangoJson<{ articles?: Record<string, unknown>[]; error?: string }>(
        '/api/fetch-news/?providers=newsapi,alpha_vantage'
      );
      const articles = data.articles || [];
      if (data.error && !articles.length) {
        // Treat upstream "no feed / rate limit" as an empty result.
        return [];
      }
      if (data.error) {
        // If the API returned partial data, still surface error via console.
        console.warn('fetch-news warning:', data.error);
      }
      return articles.map((item: { title?: string; summary?: string; url?: string; sentiment?: string; source?: string; time_published?: string }, i: number) => {
        const ts = item.time_published ? new Date(item.time_published.replace(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6')) : new Date();
        // Normalize sentiment to valid values
        const rawSentiment = (item.sentiment || 'neutral').toLowerCase();
        const sentiment = isSentiment(rawSentiment) ? rawSentiment : 'neutral';
        return {
          id: `news-${i}-${ts.getTime()}`,
          headline: item.title || 'No Title',
          source: (item.source || 'Alpha Vantage').replace(/^.*\/\/|www\.|\..*$/g, '').slice(0, 25),
          sentiment,
          sentimentScore: sentiment === 'positive' ? 0.7 : sentiment === 'negative' ? -0.5 : 0,
          timestamp: ts,
          symbols: [],
          url: item.url,
        };
      });
    } catch (error) {
      console.error('Error fetching news:', error);
      return [];
    }
  },

  /** Fetch OHLC chart data for a symbol from /api/market/{symbol}/history/ */
  async getChartData(symbol: string, period = '1mo'): Promise<ChartDataPoint[]> {
    try {
      const response = await djangoFetch(`/api/market/${encodeURIComponent(symbol)}/history/?period=${period}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to fetch chart data: ${response.statusText}`);
      }
      const data = await response.json();
      if (data.error) {
        // Handle backend errors gracefully - log but don't throw
        console.error('Backend error:', data.error);
        return [];
      }
      return (data.history || []).map((d: { timestamp: number; open: number; high: number; low: number; close: number; volume: number }) => ({
        timestamp: d.timestamp,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume || 0,
      }));
    } catch (error) {
      console.error('Error fetching chart data:', error);
      // Return empty array instead of throwing to prevent UI crashes
      return [];
    }
  },

  /** Run multi-agent pipeline and return unified insights */
  async getQuantCatalog(): Promise<QuantCatalog | null> {
    try {
      return await djangoJson<QuantCatalog>('/api/quant/catalog/');
    } catch (error) {
      console.error('Error fetching quant catalog:', error);
      return null;
    }
  },

  async getLearningHealth(): Promise<{
    status: string;
    challenge: string;
    agents: string[];
    iq_layers: string[];
    synthetic_data_only: boolean;
  } | null> {
    try {
      return await djangoJson('/api/learning/health/');
    } catch {
      return null;
    }
  },

  async getLearningLearners(): Promise<SyntheticLearner[]> {
    try {
      const data = await djangoJson<{ learners: SyntheticLearner[] }>('/api/learning/learners/');
      return data.learners || [];
    } catch {
      return [];
    }
  },

  async getLearningTeams(): Promise<string[]> {
    try {
      const data = await djangoJson<{ teams: string[] }>('/api/learning/teams/');
      return data.teams || [];
    } catch {
      return [];
    }
  },

  async runLearningPipeline(opts: {
    learner_id: string;
    team?: string;
    topics?: string[];
    certification?: string;
  }): Promise<LearningRunResult | null> {
    try {
      return await djangoJson<LearningRunResult>('/api/learning/run/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(opts),
      });
    } catch (error) {
      console.error('Error running learning pipeline:', error);
      return null;
    }
  },

  async getAgentInsights(
    ticker?: string,
    options?: { selectedIndicators?: string[]; selectedPatterns?: string[] }
  ): Promise<AgentsRunResult | null> {
    try {
      const body: {
        ticker?: string;
        selected_indicators?: string[];
        selected_patterns?: string[];
      } = {};
      if (ticker) body.ticker = ticker;
      if (options?.selectedIndicators?.length) body.selected_indicators = options.selectedIndicators;
      if (options?.selectedPatterns?.length) body.selected_patterns = options.selectedPatterns;
      return await djangoJson<AgentsRunResult>('/api/agents/run/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
    } catch (error) {
      console.error('Error fetching agent insights:', error);
      return null;
    }
  },

  /** Fetch sentiment distribution and trend from /api/chart-data/ */
  async getSentimentAnalytics(): Promise<SentimentChartData | null> {
    try {
      const response = await djangoFetch('/api/chart-data/');
      if (!response.ok) throw new Error('Failed to fetch sentiment analytics');
      return await response.json();
    } catch (error) {
      console.error('Error fetching sentiment analytics:', error);
      return null;
    }
  },

  /** Fetch live ticker data (indices, stocks) from /api/live-ticker/ */
  async getLiveTicker(): Promise<LiveTickerItem[]> {
    try {
      const data = await djangoJson<{ tickers?: LiveTickerItem[]; error?: string }>('/api/live-ticker/');
      if (data.error) return [];
      return data.tickers || [];
    } catch (error) {
      return [];
    }
  },

  /** Fetch scanner results from /api/scanner/ */
  async getScanner(symbols: string, period = '3mo'): Promise<ScannerResponse> {
    const params = new URLSearchParams({ symbols, period });
    const response = await djangoFetch(`/api/scanner/?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch scanner results');
    return await response.json();
  },

  /** Fetch options chain from /api/options-chain/ (yfinance first, Finnhub US fallback) */
  async getOptionsChain(symbol: string, expiry?: string, nocache?: boolean): Promise<OptionsChainResponse> {
    const params = new URLSearchParams({ symbol });
    if (expiry) params.set('expiry', expiry);
    if (nocache) params.set('nocache', '1');
    const response = await djangoFetch(`/api/options-chain/?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch options chain');
    return await response.json();
  },

  /** Build lightweight intraday decision for chart overlays. */
  async getIntradayTradeDecision(symbol: string, holdMinutes = 15): Promise<IntradayTradeDecision> {
    const params = new URLSearchParams({
      symbol: symbol.trim(),
      hold_minutes: String(holdMinutes),
    });
    const response = await djangoFetch(`/api/trade/decision/?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch intraday trade decision');
    return await response.json();
  },

  async getShockScore(): Promise<ShockScorePayload> {
    return djangoJson<ShockScorePayload>('/api/shock/score/');
  },

  async getShockUniverse(group = 'all'): Promise<{
    symbols: string[];
    large_cap: string[];
    mid_cap: string[];
    small_cap: string[];
    indices: Array<{ symbol: string; yf: string; type: string }>;
    source: string;
    count: number;
  }> {
    const params = new URLSearchParams({ group });
    return djangoJson(`/api/shock/universe/?${params}`);
  },

  async getShockLiveScan(threshold = 100, index = 'nifty'): Promise<{
    index: string;
    net_move_pts: number;
    threshold_pts: number;
    direction: string;
    shock_alert: boolean;
    open: number;
    close: number;
  }> {
    const params = new URLSearchParams({
      threshold: String(threshold),
      index,
    });
    return djangoJson(`/api/shock/live-scan/?${params}`);
  },

  async getShockHistory(
    page = 1,
    opts?: { cause?: string; direction?: string; index?: string; threshold?: number }
  ): Promise<{
    results: ShockHistoryRow[];
    total: number;
    pages: number;
  }> {
    const params = new URLSearchParams({ page: String(page) });
    if (opts?.cause) params.set('cause', opts.cause);
    if (opts?.direction) params.set('direction', opts.direction);
    if (opts?.index) params.set('index', opts.index);
    if (opts?.threshold != null) params.set('threshold', String(opts.threshold));
    return djangoJson(`/api/shock/history/?${params}`);
  },

  async getShockAlerts(): Promise<
    Array<{
      fired_at: string;
      score: number;
      cause: string;
      headline: string;
      source: string;
      hedge: string;
      status: string;
      eod_nifty_change: number | null;
    }>
  > {
    return djangoJson('/api/shock/alerts/');
  },

  async suggestBacktestStrategy(prefix: string): Promise<string[]> {
    const params = new URLSearchParams({ q: prefix });
    const response = await fetch(`/api/backtest/suggest?${params}`, { cache: 'no-store' });
    const data = await response.json();
    return data.suggestions || [];
  },

  async compileBacktestStrategy(
    strategyPrompt: string,
    mode = 'equity_delivery'
  ): Promise<CompiledStrategy> {
    const response = await fetch('/api/backtest/compile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy_prompt: strategyPrompt, mode }),
    });
    const data = await response.json();
    if (!response.ok) throw new ApiError(data.error || 'Compile failed', response.status, data);
    return data;
  },

  /** Strategy templates + options chain availability. */
  async getBacktestTemplates(ticker: string): Promise<{
    templates: BacktestStrategyTemplate[];
    options_chain: BacktestResult['options_chain'];
    catalog?: QuantCatalog;
  }> {
    const params = new URLSearchParams({ ticker: ticker.trim().toUpperCase() });
    const response = await fetch(`/api/backtest?${params}`, { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok) throw new ApiError(data.error || 'Failed to load templates', response.status, data);
    return data;
  },

  /** Run backtest (news/event mode or legacy sentiment mode). */
  async runBacktest(ticker: string, options: BacktestRunOptions = {}): Promise<BacktestResult> {
    const mode = options.mode ?? 'equity_delivery';
    const response = await fetch('/api/backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: ticker.trim().toUpperCase(),
        mode: mode === 'legacy' ? '' : mode,
        strategyId: options.strategyId,
        strategyPrompt: options.strategyPrompt,
        onlyNewsEvents: options.onlyNewsEvents,
        days: options.days ?? 126,
        startDate: options.startDate,
        endDate: options.endDate,
        periodLabel: options.periodLabel,
        customOnly: options.customOnly,
        useGroqCompile: options.useGroqCompile,
        compiledRules: options.compiledRules,
        useAlphaSentiment: options.useAlphaSentiment,
        useKite: options.useKite,
        apiKey: options.kiteCredentials?.apiKey,
        accessToken: options.kiteCredentials?.accessToken,
      }),
      cache: 'no-store',
    });
    const data = (await response.json()) as BacktestResult;
    if (!response.ok) {
      throw new ApiError(data.error || 'Backtest failed', response.status, data);
    }
    return data;
  },
};
