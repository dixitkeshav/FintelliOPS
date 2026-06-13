from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.core.cache import cache
import logging
import math
import requests
import json
import os
from datetime import datetime, timezone
from typing import Any
from .models import NewsArticle
from .sentiment import analyze_financial_sentiment
from . import finnhub_client as fh
from . import newsapi_client as na
from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = logging.getLogger(__name__)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "YOUR_API_KEY_HERE")


def _looks_like_corporate_notice(title: str) -> bool:
    t = (title or "").strip().lower()
    if not t:
        return False
    corporate_markers = (
        "consolidated",
        "standalone",
        "board meeting",
        "record date",
        "agm",
        "egm",
        "notlisted",
        "outcome of board meeting",
        "shareholding pattern",
    )
    return any(marker in t for marker in corporate_markers)


def _dedupe_articles(items):
    seen = set()
    out = []
    for item in items:
        title = (item.get("title") or "").strip().lower()
        url = (item.get("url") or "").strip().lower()
        key = title or url
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out

# Home/Dashboard View
def dashboard(request):
    try:
        articles = NewsArticle.objects.all().values('title', 'content', 'published_at')
        return render(request, 'index.html', {'articles': articles})
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

# News API endpoint (NewsAPI primary; fallback providers)
def fetch_news(request):
    providers_q = (request.GET.get("providers") or "").strip().lower()
    requested = {p.strip() for p in providers_q.split(",") if p.strip()} if providers_q else set()
    cache_key = f"fetch_news_financial_markets:{','.join(sorted(requested)) or 'default'}"
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse(cached)
    except Exception:
        pass

    use_newsapi = na.is_configured() and ((not requested) or ("newsapi" in requested))
    use_alpha = (not requested) or ("alpha_vantage" in requested) or ("alpha" in requested)
    use_finnhub = fh.is_configured() and (
        (not requested) or ("finnhub" in requested) or (("alpha_vantage" in requested) and len(requested) == 1)
    )

    articles = []
    sources = []

    if use_newsapi:
        api_articles = na.fetch_market_news(limit=30)
        if api_articles:
            for item in api_articles[:30]:
                lab = "neutral"
                try:
                    s, _ = analyze_financial_sentiment(
                        ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
                    )
                    lab = (s or "neutral").lower()
                except Exception:
                    pass
                articles.append(
                    {
                        "title": item.get("title", "No Title"),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", "#"),
                        "sentiment": lab,
                        "source": item.get("source") or "NewsAPI",
                        "time_published": item.get("time_published", ""),
                    }
                )
            sources.append("newsapi")

    if not articles and use_alpha:
        url = (
            "https://www.alphavantage.co/query"
            f"?function=NEWS_SENTIMENT&topics=financial_markets&apikey={ALPHA_VANTAGE_API_KEY}&limit=30"
        )
        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            feed = data.get("feed") or []
            if feed:
                articles.extend(
                    {
                        "title": item.get("title", "No Title"),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", "#"),
                        "sentiment": (item.get("overall_sentiment_label") or "Neutral").lower(),
                        "source": item.get("source", "Alpha Vantage"),
                        "time_published": item.get("time_published", ""),
                    }
                    for item in feed[:25]
                )
                sources.append("alpha_vantage")
        except Exception:
            logger.exception("fetch_news: alpha vantage failed")

    if not articles and use_finnhub:
        fh_items = fh.market_news("general")
        if fh_items:
            for item in fh_items[:20]:
                lab = "neutral"
                try:
                    s, _ = analyze_financial_sentiment(
                        ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
                    )
                    lab = (s or "neutral").lower()
                except Exception:
                    pass
                articles.append(
                    {
                        "title": item.get("title", "No Title"),
                        "summary": item.get("summary", ""),
                        "url": item.get("url", "#"),
                        "sentiment": lab,
                        "source": item.get("source") or "Finnhub",
                        "time_published": item.get("time_published", ""),
                    }
                )
            sources.append("finnhub")

    articles = _dedupe_articles(articles)[:30]

    try:
        for a in articles:
            title = (a.get("title") or "").strip()
            summary = (a.get("summary") or "").strip()
            if not title:
                continue
            NewsArticle.objects.update_or_create(
                title=title,
                defaults={"content": (summary or title)[:20000]},
            )
    except Exception:
        logger.exception("fetch_news: failed to persist NewsArticle records")

    try:
        payload = {
            "articles": articles,
            "source": sources[0] if len(sources) == 1 else "multi",
            "sources": sources,
        }
        if not articles:
            payload["error"] = "No news found from selected providers"
        try:
            cache.set(cache_key, payload, timeout=300)  # 5 min
        except Exception:
            pass
        return JsonResponse(payload)
    except Exception as e:
        # Keep API stable for the frontend.
        return JsonResponse({"articles": [], "error": str(e)}, status=200)

# Sentiment Distribution Chart Data (from recent news when available)
def sentiment_chart_data(request):
    try:
        articles = list(NewsArticle.objects.all().values_list("title", "content")[:200])
        if articles:
            from .sentiment import analyze_financial_sentiment
            pos = neg = neu = 0
            labels: list[str] = []
            for title, content in articles:
                text = (title or "") + " " + (content or "")[:500]
                if not text.strip():
                    continue
                try:
                    s, _ = analyze_financial_sentiment(text)
                    s = (s or "neutral").lower()
                    labels.append(s)
                    if s == "positive":
                        pos += 1
                    elif s == "negative":
                        neg += 1
                    else:
                        neu += 1
                except Exception:
                    neu += 1
            total = pos + neg + neu
            if total:
                chunk_size = max(1, len(labels) // 5)
                trend_positive = []
                trend_negative = []
                for i in range(5):
                    chunk = labels[i * chunk_size : (i + 1) * chunk_size]
                    trend_positive.append(sum(1 for x in chunk if x == "positive"))
                    trend_negative.append(sum(1 for x in chunk if x == "negative"))
                data = {
                    "distribution": {"labels": ["Positive", "Negative", "Neutral"], "data": [pos, neg, neu]},
                    "trend": {
                        "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
                        "positive": trend_positive,
                        "negative": trend_negative,
                    },
                }
            else:
                data = _default_chart_data()
        else:
            data = _default_chart_data()
    except Exception:
        data = _default_chart_data()
    return JsonResponse(data)


def _default_chart_data():
    return {
        "distribution": {"labels": ["Positive", "Negative", "Neutral"], "data": [62, 28, 10]},
        "trend": {"labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"], "positive": [60, 70, 65, 75, 80], "negative": [30, 20, 25, 15, 10]}
    }

# Sentiment Analysis for Pasted News (for /api/analyze-news/)
@csrf_exempt
@require_POST
def analyze_news_view(request):
    try:
        body = json.loads(request.body)
        text = body.get("text", "")
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        sentiment, probabilities = analyze_financial_sentiment(text)
        return JsonResponse({
            "sentiment": sentiment,
            "probabilities": {
                "positive": round(probabilities[2], 3),
                "neutral": round(probabilities[1], 3),
                "negative": round(probabilities[0], 3)
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Ticker Symbol Auto-Suggestion (for /api/search-ticker/)
def search_ticker(request):
    query = request.GET.get('q', '')  # Use 'q' to match frontend
    if not query:
        return JsonResponse({'results': []})

    url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={ALPHA_VANTAGE_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()

        # Return only the symbol for dropdown
        results = [match.get("1. symbol", "") for match in data.get("bestMatches", []) if match.get("1. symbol", "")]
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'results': []})

# FinBERT Sentiment Analysis API (for /api/analyze-sentiment/)
@api_view(['POST'])
def analyze_sentiment(request):
    text = request.data.get('text', '')
    if not text:
        return Response({"error": "No text provided."}, status=400)
    try:
        sentiment, probs = analyze_financial_sentiment(text)
        probs_dict = {"negative": float(probs[0]), "neutral": float(probs[1]), "positive": float(probs[2])}
        payload = {
            "sentiment": sentiment,
            "probabilities": probs_dict,
        }
        if getattr(settings, "FEATURE_GENAI_INSIGHTS", False):
            try:
                from intelligence.insights import build_genai_insights
                insights = build_genai_insights(text, sentiment, probs_dict, include_aspect=True)
                payload["insights"] = insights
            except Exception as e:
                logger.warning("GenAI insights failed: %s", e)
        return Response(payload)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# Custom Sentiment for Ticker (for /api/custom-sentiment/) — fetches news and aggregates
@api_view(['POST'])
def custom_sentiment(request):
    ticker = request.data.get('ticker', '').upper()
    if not ticker:
        return Response({"error": "No ticker provided."}, status=400)
    try:
        if na.is_configured():
            news = na.fetch_symbol_news(ticker, limit=20)
            if news:
                pos = neg = neu = 0
                for item in news:
                    text = ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
                    if not text.strip():
                        continue
                    try:
                        s, _ = analyze_financial_sentiment(text)
                        s = (s or "neutral").lower()
                        if s == "positive":
                            pos += 1
                        elif s == "negative":
                            neg += 1
                        else:
                            neu += 1
                    except Exception:
                        neu += 1
                total = pos + neg + neu
                if total > 0:
                    if pos > neg and pos > neu:
                        sentiment = "positive"
                    elif neg > pos and neg > neu:
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"
                    return Response(
                        {
                            "sentiment": sentiment,
                            "count": total,
                            "positive": pos,
                            "negative": neg,
                            "neutral": neu,
                            "source": "newsapi",
                        }
                    )
        if fh.is_configured():
            out = fh.aggregate_sentiment_company_news(ticker, days=14)
            out["source"] = "finnhub"
            return Response(out)
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}&limit=15"
        r = requests.get(url, timeout=15)
        data = r.json()
        feed = data.get("feed", [])
        if feed:
            pos = neg = neu = 0
            for item in feed:
                lab = (item.get("overall_sentiment_label") or "Neutral").lower()
                if lab == "positive": pos += 1
                elif lab == "negative": neg += 1
                else: neu += 1
            total = pos + neg + neu
            if pos > neg and pos > neu: sentiment = "positive"
            elif neg > pos and neg > neu: sentiment = "negative"
            else: sentiment = "neutral"
            return Response(
                {
                    "sentiment": sentiment,
                    "count": total,
                    "positive": pos,
                    "negative": neg,
                    "neutral": neu,
                    "source": "alpha_vantage",
                }
            )
        return Response({"sentiment": "neutral", "count": 0, "source": "none"})
    except Exception as e:
        return Response({"error": str(e), "sentiment": "neutral"}, status=500)


# ——— GenAI Intelligence: full insights for a single text ———
@api_view(['POST'])
def analyze_with_insights(request):
    """Returns sentiment + why_sentiment, risk_drivers, event_impact_summary, events, aspect_sentiment."""
    text = request.data.get('text', '')
    if not text:
        return Response({"error": "No text provided."}, status=400)
    try:
        sentiment, probs = analyze_financial_sentiment(text)
        probs_dict = {"negative": float(probs[0]), "neutral": float(probs[1]), "positive": float(probs[2])}
        from intelligence.insights import build_genai_insights
        insights = build_genai_insights(text, sentiment, probs_dict, include_aspect=True)
        return Response({"sentiment": sentiment, "probabilities": probs_dict, "insights": insights})
    except Exception as e:
        logger.exception("analyze_with_insights: %s", e)
        return Response({"error": str(e)}, status=500)


# ——— Agentic AI: run multi-agent pipeline ———
_last_iq_result: dict[str, Any] | None = None


def _format_iq_agent(agent_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "output": agent_result.get("output", ""),
        "iq_layers_used": agent_result.get("iq_layers_used", []),
        "citations": agent_result.get("citations", []),
        "fabric_entities": agent_result.get("fabric_entities", []),
        "work_signals": agent_result.get("work_signals", {}),
        "completed": agent_result.get("completed", False),
        "error": agent_result.get("error"),
    }


def _build_iq_response(context: dict[str, Any], orch: Any) -> dict[str, Any]:
    return {
        "pipeline_completed": context.get("pipeline_completed", False),
        "query": context.get("query", ""),
        "sector": context.get("sector", ""),
        "analyst_id": context.get("analyst_id", ""),
        "agents": {
            name: _format_iq_agent(result)
            for name, result in context.get("agents", {}).items()
        },
        "all_citations": context.get("all_citations", []),
        "evaluation": context.get("evaluation", {}),
        "recommendation": context.get("recommendation", ""),
        "iq_health": orch.health_check(),
        "pipeline_start": context.get("pipeline_start"),
        "pipeline_end": context.get("pipeline_end"),
    }


@api_view(["GET"])
def agents_health(request):
    """Health check for FintelliOps IQ pipeline and LLM."""
    from agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()
    return Response(orch.health_check())


@api_view(["GET"])
def agents_status(request):
    """Status of last IQ pipeline run."""
    global _last_iq_result
    if _last_iq_result is None:
        return Response({"status": "idle", "agents_completed": 0, "agents": {}})
    agents = _last_iq_result.get("agents", {})
    completed = sum(1 for a in agents.values() if a.get("completed"))
    return Response(
        {
            "status": "completed" if _last_iq_result.get("pipeline_completed") else "running",
            "agents_completed": completed,
            "agents_total": len(agents),
            "agents": {
                name: {"completed": r.get("completed", False), "agent_name": name}
                for name, r in agents.items()
            },
        }
    )


@api_view(['GET', 'POST'])
def agents_run(request):
    """Run FintelliOps IQ pipeline (query-based) or legacy ticker/news pipeline."""
    try:
        req_data = request.data if request.method == "POST" else request.GET
        query = (req_data.get("query") or "").strip()

        if query:
            sector = (req_data.get("sector") or "Technology").strip()
            analyst_id = (req_data.get("analyst_id") or "ANL-001").strip()
            from agents.orchestrator import AgentOrchestrator

            global _last_iq_result
            orch = AgentOrchestrator()
            context = orch.run_fintelliops(query=query, sector=sector, analyst_id=analyst_id)
            _last_iq_result = context
            return Response(_build_iq_response(context, orch))

        import time as _time

        fetch_started = _time.perf_counter()
        news_source = "unknown"
        news_source_counts: dict[str, int] = {}
        articles: list[dict] = []
        ticker = (req_data.get("ticker") or "").strip()
        use_synthetic = str(req_data.get("use_synthetic") or req_data.get("demo") or "").lower() in (
            "1", "true", "yes",
        )
        selected_indicators = req_data.get("selected_indicators") or []
        selected_patterns = req_data.get("selected_patterns") or []
        if isinstance(selected_indicators, str):
            selected_indicators = [s.strip() for s in selected_indicators.split(",") if s.strip()]
        if isinstance(selected_patterns, str):
            selected_patterns = [s.strip() for s in selected_patterns.split(",") if s.strip()]

        if use_synthetic:
            from agents.synthetic_data import aggregate_sentiment, load_synthetic_articles

            articles = load_synthetic_articles(ticker or "RELIANCE")
            news_source = "synthetic"
            news_source_counts = {"synthetic": len(articles)}
            agg = aggregate_sentiment(articles)
            fetch_ms = (_time.perf_counter() - fetch_started) * 1000
            from agents.orchestrator import AgentOrchestrator

            orch = AgentOrchestrator()
            result = orch.run(
                articles,
                ticker=ticker or "RELIANCE",
                aggregate_sentiment=agg,
                news_meta={
                    "source": news_source,
                    "fetch_ms": fetch_ms,
                    "sources": news_source_counts,
                },
                selected_indicators=selected_indicators,
                selected_patterns=selected_patterns,
            )
            return Response(result)

        if request.method == "POST" and request.data.get("articles"):
            articles = request.data["articles"]
            news_source = "client"
        elif ticker:
            from fetch_news.news_aggregator import fetch_merged_news

            merged = fetch_merged_news(ticker, limit=40, run_finbert=True)
            articles = [
                {
                    "title": i.get("title", ""),
                    "summary": i.get("summary", ""),
                    "sentiment": (i.get("sentiment") or "neutral").lower(),
                    "source": i.get("source", ""),
                    "provider": i.get("provider", ""),
                    "url": i.get("url", "#"),
                }
                for i in merged.get("articles", [])
            ]
            news_source = merged.get("source", "merged")
            news_source_counts = merged.get("sources") or {}
        else:
            from fetch_news.news_aggregator import fetch_merged_news

            merged = fetch_merged_news(None, limit=30, run_finbert=True, include_market=True)
            if merged.get("articles"):
                articles = [
                    {
                        "title": i.get("title", ""),
                        "summary": i.get("summary", ""),
                        "sentiment": (i.get("sentiment") or "neutral").lower(),
                    }
                    for i in merged["articles"]
                ]
                news_source = merged.get("source", "merged")
                news_source_counts = merged.get("sources") or {}
            else:
                td_articles = []
                feed = []
                api_articles = na.fetch_market_news(limit=25) if na.is_configured() else []

                if api_articles:
                    news_source = "newsapi"
                    articles = [
                        {
                            "title": i.get("title", ""),
                            "summary": i.get("summary", ""),
                            "sentiment": (i.get("sentiment") or "neutral").lower(),
                        }
                        for i in api_articles[:25]
                    ]
                else:
                    url = (
                        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
                        f"&topics=financial_markets&apikey={ALPHA_VANTAGE_API_KEY}&limit=25"
                    )
                    try:
                        r = requests.get(url, timeout=25)
                        feed = r.json().get("feed", [])
                    except Exception:
                        feed = []

                    if feed:
                        news_source = "alpha_vantage"
                        articles = [
                            {
                                "title": i.get("title", ""),
                                "summary": i.get("summary", ""),
                                "sentiment": (i.get("overall_sentiment_label") or "Neutral").lower(),
                            }
                            for i in feed[:25]
                        ]
                    elif fh.is_configured():
                        news_source = "finnhub"
                        fh_items = fh.market_news("general")
                        articles = [
                            {"title": x.get("title", ""), "summary": x.get("summary", ""), "sentiment": "neutral"}
                            for x in fh_items[:25]
                        ]

                if not articles:
                    from .sentiment import analyze_financial_sentiment

                    news_source = "database_finbert"
                    stored = list(
                        NewsArticle.objects.all()
                        .order_by("-published_at")
                        .values_list("title", "content")[:30]
                    )
                    articles = []
                    for title, content in stored:
                        text = ((title or "") + " " + (content or ""))[:2000]
                        if not text.strip():
                            continue
                        try:
                            s, _ = analyze_financial_sentiment(text)
                            articles.append(
                                {
                                    "title": title or "",
                                    "summary": content or "",
                                    "sentiment": (s or "neutral").lower(),
                                }
                            )
                        except Exception:
                            articles.append(
                                {
                                    "title": title or "",
                                    "summary": content or "",
                                    "sentiment": "neutral",
                                }
                            )

        fetch_ms = (_time.perf_counter() - fetch_started) * 1000
        agg = "neutral"
        if articles:
            p = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "positive")
            n = sum(1 for a in articles if (a.get("sentiment") or "").lower() == "negative")
            if p > n and p > len(articles) - p - n: agg = "positive"
            elif n > p: agg = "negative"
        from agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        result = orch.run(
            articles,
            ticker=ticker,
            aggregate_sentiment=agg,
            news_meta={
                "source": news_source,
                "fetch_ms": fetch_ms,
                "sources": news_source_counts,
            },
            selected_indicators=selected_indicators,
            selected_patterns=selected_patterns,
        )
        return Response(result)
    except Exception as e:
        logger.exception("agents_run: %s", e)
        return Response({"error": str(e)}, status=500)


# ——— Quant: catalog, signals and backtest ———
@api_view(["GET"])
def quant_catalog(request):
    """Indicators, candlestick patterns, and strategy templates for UI dropdowns."""
    from quant.catalog import get_full_catalog

    return Response(get_full_catalog())


@api_view(['POST'])
def quant_signals(request):
    """Return sentiment momentum, MA crossover, mean-reversion signal from provided sentiment series or last probs."""
    try:
        probs = request.data.get("probabilities") or request.data.get("last_probs")
        import pandas as pd
        from quant.signals import build_signal_payload, sentiment_score_from_probs
        sentiment_series = None
        if request.data.get("sentiment_series"):
            sentiment_series = pd.Series(request.data["sentiment_series"])
        payload = build_signal_payload(sentiment_series=sentiment_series, last_probs=probs, window=5)
        return Response(payload)
    except Exception as e:
        logger.exception("quant_signals: %s", e)
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def quant_backtest_compile(request):
    """Compile natural-language strategy to structured rules via Groq."""
    prompt = (request.data.get("strategy_prompt") or request.data.get("prompt") or "").strip()
    mode_hint = request.data.get("mode") or "equity_delivery"
    if not prompt:
        return Response({"error": "strategy_prompt required"}, status=400)
    try:
        from quant.strategy_engine import parse_strategy_prompt
        from quant.strategy_llm import compile_strategy

        groq_out = compile_strategy(prompt, mode_hint=mode_hint)
        rules = groq_out.get("rules") or []
        if not rules:
            rules = parse_strategy_prompt(prompt)
            groq_out["rules"] = rules
            groq_out["fixes_applied"] = list(groq_out.get("fixes_applied") or []) + [
                "Applied built-in parser for indicators"
            ]
        return Response(groq_out)
    except Exception as e:
        logger.exception("quant_backtest_compile: %s", e)
        return Response({"error": str(e)}, status=500)


@api_view(["GET", "POST"])
def quant_research_benchmark(request):
    """
    Research benchmark API with transaction costs/slippage and Indian symbols.

    Body/query params:
      - symbols: "RELIANCE.NS,^NSEI,INFY.NS" (optional)
      - include_global: true|false
      - days: 252 (90..756)
      - transaction_cost_bps: 8
      - slippage_bps: 4
      - include_agentic: true|false
    """
    qp = request.GET if request.method == "GET" else request.data
    symbols_raw = qp.get("symbols") or qp.get("universe") or ""
    if isinstance(symbols_raw, str):
        symbols = [x.strip().upper() for x in symbols_raw.split(",") if x.strip()]
    else:
        symbols = [str(x).strip().upper() for x in (symbols_raw or []) if str(x).strip()]

    def _as_bool(v: Any, default: bool = False) -> bool:
        if v is None:
            return default
        return str(v).strip().lower() in ("1", "true", "yes", "y")

    try:
        days = int(qp.get("days", 252))
    except (TypeError, ValueError):
        days = 252
    try:
        tc_bps = float(qp.get("transaction_cost_bps", 8))
    except (TypeError, ValueError):
        tc_bps = 8.0
    try:
        slippage_bps = float(qp.get("slippage_bps", 4))
    except (TypeError, ValueError):
        slippage_bps = 4.0

    include_global = _as_bool(qp.get("include_global"), default=False)
    include_agentic = _as_bool(qp.get("include_agentic"), default=True)

    try:
        from quant.research_benchmark import run_research_benchmark

        out = run_research_benchmark(
            symbols=symbols or None,
            include_global=include_global,
            days=days,
            transaction_cost_bps=tc_bps,
            slippage_bps=slippage_bps,
            include_agentic=include_agentic,
        )
        return Response(out)
    except Exception as e:
        logger.exception("quant_research_benchmark: %s", e)
        return Response({"error": str(e)}, status=500)


@api_view(['GET', 'POST'])
def quant_backtest(request):
    """
    Backtest API.
    GET ?templates=1 → list strategy templates.
    POST/GET with mode=equity_intraday|equity_delivery|options → event/news backtest with trade log.
    Legacy: omit mode → buy-and-hold vs sentiment (run_backtest).
    """
    qp = request.GET if request.method == "GET" else request.data

    if str(qp.get("catalog", "")).lower() in ("1", "true", "yes"):
        from quant.catalog import get_full_catalog

        return Response(get_full_catalog())

    if str(qp.get("templates", "")).lower() in ("1", "true", "yes"):
        from quant.strategy_engine import list_templates
        from quant.event_backtest import check_options_chain_available
        from quant.catalog import get_full_catalog

        ticker = qp.get("ticker", "RELIANCE")
        return Response(
            {
                "templates": list_templates(),
                "options_chain": check_options_chain_available(ticker),
                "catalog": get_full_catalog(),
            }
        )

    if str(qp.get("suggest", "")).lower() in ("1", "true", "yes"):
        from quant.strategy_llm import groq_suggest_next_words, suggest_phrases

        prefix = qp.get("q") or qp.get("prefix") or ""
        use_groq = str(qp.get("groq", "true")).lower() not in ("false", "0", "no")
        suggestions = groq_suggest_next_words(prefix) if use_groq and len(prefix) >= 2 else suggest_phrases(prefix)
        return Response({"suggestions": suggestions, "prefix": prefix})

    mode = (qp.get("mode") or "").strip().lower()
    ticker = qp.get("ticker", "RELIANCE")

    if mode in ("equity_intraday", "equity_delivery", "options", "intraday", "delivery"):
        if mode == "intraday":
            mode = "equity_intraday"
        if mode == "delivery":
            mode = "equity_delivery"
        try:
            days = int(qp.get("days", 126))
        except (TypeError, ValueError):
            days = 126
        days = max(30, min(days, 252))
        only_news = str(qp.get("only_news_events", "true")).lower() not in ("false", "0", "no")
        try:
            from quant.event_backtest import run_event_backtest

            price_history = None
            price_source = qp.get("price_source")
            if request.method == "POST" and request.data.get("price_history"):
                price_history = request.data["price_history"]
            custom_only = str(qp.get("custom_only", "false")).lower() in ("true", "1", "yes")
            use_groq = str(qp.get("use_groq_compile", "false")).lower() in ("true", "1", "yes")
            compiled_rules = None
            if request.method == "POST" and request.data.get("compiled_rules"):
                compiled_rules = request.data["compiled_rules"]
            result = run_event_backtest(
                ticker=ticker,
                mode=mode,
                template_id=qp.get("strategy_id") or qp.get("template_id"),
                strategy_prompt=qp.get("strategy_prompt"),
                only_news_events=only_news,
                days=days,
                start_date=qp.get("start_date") or None,
                end_date=qp.get("end_date") or None,
                period_label=qp.get("period_label") or None,
                price_history=price_history,
                price_source=price_source,
                custom_only=custom_only,
                compiled_rules=compiled_rules,
                use_groq_compile=use_groq,
            )
            return Response(result)
        except Exception as e:
            logger.exception("quant_backtest event: %s", e)
            return Response({"error": str(e)}, status=500)

    use_alpha = str(qp.get("use_alpha_sentiment", "true")).lower() not in ("false", "0", "no")
    try:
        days = int(qp.get("days", 126))
    except (TypeError, ValueError):
        days = 126
    days = max(30, min(days, 252))
    sentiment_series = None
    if request.method == "POST" and request.data.get("sentiment_series"):
        import pandas as pd
        sentiment_series = pd.Series(request.data["sentiment_series"])
    try:
        from quant.backtest import run_backtest
        price_history = None
        price_source = qp.get("price_source")
        if request.method == "POST" and request.data.get("price_history"):
            price_history = request.data["price_history"]
        result = run_backtest(
            ticker=ticker,
            sentiment_series=sentiment_series,
            days=days,
            alpha_vantage_key=ALPHA_VANTAGE_API_KEY,
            use_alpha_sentiment=use_alpha,
            price_history=price_history,
            price_source=price_source,
        )
        return Response(result)
    except Exception as e:
        logger.exception("quant_backtest: %s", e)
        return Response({"error": str(e)}, status=500)


# ——— Evaluation ———
@api_view(['POST'])
def evaluation_sentiment_accuracy(request):
    """Compare predicted vs ground truth labels. Body: { \"predicted\": [...], \"labels\": [...] }."""
    try:
        from evaluation.metrics import sentiment_accuracy
        predicted = request.data.get("predicted", [])
        labels = request.data.get("labels", [])
        out = sentiment_accuracy(predicted, labels)
        return Response(out)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def evaluation_latency(request):
    """Benchmark latency of sentiment analysis (and optionally insights)."""
    try:
        from evaluation.metrics import latency_benchmark
        from fetch_news.sentiment import analyze_financial_sentiment
        sample = "The Fed raised rates by 25 bps. Markets reacted negatively. Banking stocks fell."
        out = latency_benchmark(lambda: analyze_financial_sentiment(sample), num_runs=5)
        return Response(out)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ——— Symbol Deep-Dive Agent (price + news + similar stocks + prediction) ———
@api_view(['GET', 'POST'])
def symbol_deep_dive(request):
    """Run Symbol Deep-Dive agent: fetch price, details, news, similar stocks; predict and name similar stocks."""
    symbol = (request.GET if request.method == "GET" else request.data).get("symbol", "").strip().upper()
    if not symbol:
        return Response({"error": "symbol required"}, status=400)
    try:
        from agents.symbol_deep_dive import SymbolDeepDiveAgent
        agent = SymbolDeepDiveAgent()
        result = agent.run({
            "symbol": symbol,
            "alpha_vantage_api_key": ALPHA_VANTAGE_API_KEY,
            "newsapi_api_key": os.getenv("NEWSAPI_KEY", ""),
        })
        if result.get("error") and not result.get("prediction"):
            return Response(result, status=500)
        return Response(result)
    except Exception as e:
        logger.exception("symbol_deep_dive: %s", e)
        return Response({"error": str(e)}, status=500)


# ——— Market price history (OHLC) for charts ———
@api_view(['GET'])
def market_history(request, symbol: str):
    """Return OHLC history for a symbol. Query: period=1d|5d|1mo|3mo|6mo|1y"""
    period = request.GET.get('period', '1mo')
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y']
    if period not in valid_periods:
        period = '1mo'
    try:
        if fh.is_configured():
            rows, err = fh.stock_candles(symbol, period)
            if not err and rows:
                return Response({"symbol": symbol, "history": rows, "source": "finnhub"})
        import pandas as pd
        import yfinance as yf

        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        if hist is None or hist.empty:
            return Response({"error": "No data", "history": []})
        history = []
        for idx, row in hist.iterrows():
            ms = int(pd.Timestamp(idx).timestamp() * 1000)
            vol = row["Volume"] if "Volume" in row.index else 0
            if pd.isna(vol):
                vol = 0
            else:
                vol = int(vol)
            history.append(
                {
                    "timestamp": ms,
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": vol,
                }
            )
        return Response({"symbol": symbol, "history": history, "source": "yfinance"})
    except Exception as e:
        logger.warning("market_history: %s", e)
        return Response({"error": str(e), "history": []})


# ——— Live ticker / indices (for scrolling strip: symbol, price, change) ———
@api_view(['GET'])
def live_ticker(request):
    """Return list of { symbol, name, price, change_pct } for indices and popular tickers (Finnhub preferred, else yfinance)."""
    try:
        import yfinance as yf

        def _r2(x) -> float:
            try:
                v = float(x)
                if not math.isfinite(v):
                    return 0.0
                return round(v, 2)
            except (TypeError, ValueError):
                return 0.0

        # Indices and a few liquid names for the ticker strip
        symbols = [
            "^GSPC", "^DJI", "^IXIC", "^NSEI", "^BSESN", "^N225", "^FTSE", "^GDAXI",
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "RELIANCE.NS", "TCS.NS", "INFY.NS",
        ]
        out = []

        def _yf_row(sym: str) -> dict | None:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="5d")
                info = t.info or {}
                name = str(info.get("shortName") or info.get("longName") or sym)[:30]
                if hist is not None and len(hist) >= 2:
                    last = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    ch = ((last - prev) / prev * 100) if prev else 0
                else:
                    last = float(info.get("regularMarketPrice") or info.get("previousClose") or 0)
                    ch = 0
                return {"symbol": sym, "name": name, "price": _r2(last), "change_pct": _r2(ch)}
            except Exception:
                return None

        for s in symbols:
            row = None
            if fh.is_configured():
                q = fh.quote(s)
                if q is not None and q.get("c") is not None:
                    prof = fh.company_profile2(s)
                    name = str((prof or {}).get("name") or s)[:30]
                    last = float(q.get("c") or 0)
                    dp = q.get("dp")
                    if dp is None and q.get("pc") not in (None, 0) and last:
                        try:
                            pc = float(q["pc"])
                            dp = (float(q["c"]) - pc) / pc * 100.0 if pc else 0.0
                        except Exception:
                            dp = 0.0
                    row = {
                        "symbol": s,
                        "name": name,
                        "price": _r2(last),
                        "change_pct": _r2(dp if dp is not None else 0),
                    }
            if row is None:
                row = _yf_row(s)
            if row:
                out.append(row)
        src = "finnhub" if fh.is_configured() else "yfinance"
        return Response({"tickers": out, "source": src})
    except Exception as e:
        logger.warning("live_ticker: %s", e)
        return Response({"tickers": []})


# ——— Cross-domain ———
@api_view(['GET', 'POST'])
def cross_domain_news(request):
    """Fetch news for domain: crypto, commodities, fx, geopolitical. GET ?domain=crypto."""
    domain = (request.GET if request.method == "GET" else request.data).get("domain", "financial_markets")
    try:
        from cross_domain.sources import fetch_domain_news, cross_domain_reasoning
        articles = fetch_domain_news(domain, limit=20)
        summary = cross_domain_reasoning({domain: (articles[0].get("sentiment") if articles else "neutral")})
        return Response({"domain": domain, "articles": articles, "cross_domain_reasoning": summary})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ——— Screener / Scanner ———
@api_view(["GET"])
def scanner(request):
    """
    Simple functional screener:
    - sentiment from Alpha Vantage (NEWS_SENTIMENT) aggregated into pos/neg counts
    - momentum from yfinance price change
    - outputs BULLISH/BEARISH/NEUTRAL + confidence
    """
    symbols_csv = request.GET.get("symbols", "").strip()
    if not symbols_csv:
        symbols_csv = "^NSEI,AAPL,MSFT,NVDA,RELIANCE.NS"

    symbols = [s.strip().upper() for s in symbols_csv.split(",") if s.strip()]
    if len(symbols) > 25:
        symbols = symbols[:25]
    period = request.GET.get("period", "3mo")

    def _news_sentiment_for_ticker(ticker: str) -> dict:
        if na.is_configured():
            items = na.fetch_symbol_news(ticker, limit=15)
            if items:
                pos = neg = neu = 0
                for item in items:
                    text = ((item.get("title") or "") + " " + (item.get("summary") or ""))[:1500]
                    if not text.strip():
                        continue
                    try:
                        s, _ = analyze_financial_sentiment(text)
                        s = (s or "neutral").lower()
                        if s == "positive":
                            pos += 1
                        elif s == "negative":
                            neg += 1
                        else:
                            neu += 1
                    except Exception:
                        neu += 1
                count = pos + neg + neu
                if count > 0:
                    sentiment = "neutral"
                    if pos > neg and pos > neu:
                        sentiment = "positive"
                    elif neg > pos and neg > neu:
                        sentiment = "negative"
                    return {
                        "sentiment": sentiment,
                        "count": count,
                        "positive": pos,
                        "negative": neg,
                        "neutral": neu,
                    }
        try:
            url = (
                "https://www.alphavantage.co/query"
                f"?function=NEWS_SENTIMENT&tickers={ticker}"
                f"&apikey={ALPHA_VANTAGE_API_KEY}&limit=15"
            )
            r = requests.get(url, timeout=20)
            data = r.json()
            feed = data.get("feed", []) or []
            if not feed:
                return {"sentiment": "neutral", "count": 0, "positive": 0, "negative": 0, "neutral": 0}
            pos = neg = neu = 0
            for item in feed:
                lab = (item.get("overall_sentiment_label") or "Neutral").lower()
                if lab == "positive":
                    pos += 1
                elif lab == "negative":
                    neg += 1
                else:
                    neu += 1
            count = pos + neg + neu
            if count == 0:
                sentiment = "neutral"
            elif pos > neg and pos > neu:
                sentiment = "positive"
            elif neg > pos and neg > neu:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            return {
                "sentiment": sentiment,
                "count": count,
                "positive": pos,
                "negative": neg,
                "neutral": neu,
            }
        except Exception:
            return {"sentiment": "neutral", "count": 0, "positive": 0, "negative": 0, "neutral": 0}

    def _momentum_for_symbol(ticker: str) -> dict:
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if hist is None or hist.empty or "Close" not in hist:
                return {"momentum": 0.0, "start_price": None, "end_price": None}
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                return {"momentum": 0.0, "start_price": None, "end_price": None}
            start = float(closes.iloc[0])
            end = float(closes.iloc[-1])
            mom = (end / start - 1.0) if start else 0.0
            return {"momentum": mom, "start_price": start, "end_price": end}
        except Exception:
            return {"momentum": 0.0, "start_price": None, "end_price": None}

    use_fh = fh.is_configured()

    results = []
    for sym in symbols:
        sent = _news_sentiment_for_ticker(sym)
        if use_fh and sent.get("count", 0) == 0:
            sent = fh.aggregate_sentiment_company_news(sym, days=14)
        if use_fh:
            mom = fh.momentum_from_candles(sym, period)
            if mom.get("error"):
                mom = _momentum_for_symbol(sym)
        else:
            mom = _momentum_for_symbol(sym)

        pos = sent.get("positive", 0) or 0
        neg = sent.get("negative", 0) or 0
        count = sent.get("count", 0) or 0

        # sentiment_score in [-1, 1]
        sentiment_score = 0.0
        if count > 0:
            sentiment_score = float(pos - neg) / float(count)

        momentum = float(mom.get("momentum", 0.0) or 0.0)

        if sentiment_score > 0 and momentum > 0:
            signal = "BULLISH"
        elif sentiment_score < 0 and momentum < 0:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        # Confidence is a heuristic blend of sentiment strength + absolute momentum.
        abs_sent = min(abs(sentiment_score), 1.0)
        abs_mom = min(abs(momentum) * 5.0, 1.0)  # scale momentum into [0,1]
        confidence = round(0.5 * abs_sent + 0.5 * abs_mom, 3)

        results.append(
            {
                "symbol": sym,
                "signal": signal,
                "confidence": confidence,
                "sentiment": sent.get("sentiment", "neutral"),
                "sentiment_score": round(sentiment_score, 4),
                "momentum": round(momentum, 6),
                "sentiment_counts": {
                    "positive": pos,
                    "negative": neg,
                    "neutral": sent.get("neutral", 0) or 0,
                    "total": count,
                },
            }
        )

    source = "finnhub_yfinance" if use_fh else "newsapi_alpha_yfinance"
    return Response({"period": period, "results": results, "source": source})


def _sanitize_opt_num(val):
    """JSON-safe: replace NaN/inf with None for REST responses."""
    if val is None:
        return None
    try:
        x = float(val)
        if not math.isfinite(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _options_chain_yfinance(symbol: str, expiry: str) -> dict:
    """Build options chain payload via yfinance (most reliable for US equities).

    Strike matching uses rounded keys — raw float equality often fails between calls/puts DataFrames.
    """
    import yfinance as yf

    t = yf.Ticker(symbol)
    expiries = list(t.options or [])
    if not expiries:
        return {
            "symbol": symbol,
            "expiry": None,
            "expiries": [],
            "data": [],
            "source": "yfinance",
            "error": "No option expiries from Yahoo Finance (wrong symbol, no options, or rate limit).",
        }

    exp = expiry if expiry and expiry in expiries else expiries[0]
    chain = t.option_chain(exp)
    calls = chain.calls
    puts = chain.puts
    if calls is None or puts is None or (calls.empty and puts.empty):
        return {
            "symbol": symbol,
            "expiry": exp,
            "expiries": expiries[:10],
            "data": [],
            "source": "yfinance",
            "error": "Empty calls/puts for this expiry (try another expiry or symbol).",
        }

    calls = calls.copy()
    puts = puts.copy()
    calls["strike_key"] = calls["strike"].astype(float).round(4)
    puts["strike_key"] = puts["strike"].astype(float).round(4)
    strike_keys = sorted(set(calls["strike_key"].tolist()) | set(puts["strike_key"].tolist()))

    rows = []
    for sk in strike_keys:
        ce = calls[calls["strike_key"] == sk]
        pe = puts[puts["strike_key"] == sk]
        ce_row = ce.iloc[0].to_dict() if len(ce) else {}
        pe_row = pe.iloc[0].to_dict() if len(pe) else {}
        if not ce_row and not pe_row:
            continue
        rows.append(
            {
                "strike": float(sk),
                "call": {
                    "bid": _sanitize_opt_num(ce_row.get("bid")),
                    "ask": _sanitize_opt_num(ce_row.get("ask")),
                    "lastPrice": _sanitize_opt_num(ce_row.get("lastPrice")),
                    "impliedVolatility": _sanitize_opt_num(ce_row.get("impliedVolatility")),
                    "openInterest": _sanitize_opt_num(ce_row.get("openInterest")),
                    "volume": _sanitize_opt_num(ce_row.get("volume")),
                },
                "put": {
                    "bid": _sanitize_opt_num(pe_row.get("bid")),
                    "ask": _sanitize_opt_num(pe_row.get("ask")),
                    "lastPrice": _sanitize_opt_num(pe_row.get("lastPrice")),
                    "impliedVolatility": _sanitize_opt_num(pe_row.get("impliedVolatility")),
                    "openInterest": _sanitize_opt_num(pe_row.get("openInterest")),
                    "volume": _sanitize_opt_num(pe_row.get("volume")),
                },
            }
        )

    return {
        "symbol": symbol,
        "expiry": exp,
        "expiries": expiries[:10],
        "data": rows,
        "source": "yfinance",
    }


# ——— Options chain (yfinance / Finnhub) ———
@api_view(["GET"])
def options_chain(request):
    """Options chain via Yahoo Finance and Finnhub."""
    symbol = (request.GET.get("symbol") or "").strip().upper()
    if not symbol:
        symbol = "AAPL"
    expiry = (request.GET.get("expiry") or "").strip()

    cache_key = f"options_chain:v2:{symbol}:{expiry or 'auto'}"
    if request.GET.get("nocache") != "1":
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

    try:
        payload = _options_chain_yfinance(symbol, expiry)
        if payload.get("data"):
            cache.set(cache_key, payload, timeout=120)
            return Response(payload)

        # Finnhub US-only fallback when yfinance returned no rows
        if fh.is_configured():
            sel, expiries, rows, err = fh.option_chain(symbol)
            if not err and rows:
                payload = {
                    "symbol": symbol,
                    "expiry": sel,
                    "expiries": expiries[:10],
                    "data": rows,
                    "source": "finnhub",
                }
                cache.set(cache_key, payload, timeout=120)
                return Response(payload)

        err_msg = payload.get("error") or "No chain data"
        payload = {
            "symbol": symbol,
            "expiry": payload.get("expiry"),
            "expiries": payload.get("expiries") or [],
            "data": [],
            "source": payload.get("source") or "yfinance",
            "error": err_msg,
        }
        cache.set(cache_key, payload, timeout=30)
        return Response(payload)
    except Exception as e:
        payload = {
            "symbol": symbol,
            "expiry": expiry or None,
            "expiries": [],
            "data": [],
            "error": str(e),
        }
        cache.set(cache_key, payload, timeout=30)
        return Response(payload)


def _safe_float(val, default=0.0):
    try:
        out = float(val)
        if not math.isfinite(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def _intraday_decision_from_history(
    symbol: str,
    rows: list[dict],
    hold_minutes: int,
) -> dict:
    if len(rows) < 20:
        return {
            "symbol": symbol,
            "decision": "NO_TRADE",
            "reason": "Not enough recent candles to build signal.",
            "confidence": 0.0,
            "hold_minutes": hold_minutes,
            "entry_price": None,
            "stop_loss": None,
            "target_price": None,
            "expected_move_pct": 0.0,
            "expected_profit_pct": 0.0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    closes = [_safe_float(r.get("close")) for r in rows if r.get("close") is not None]
    highs = [_safe_float(r.get("high")) for r in rows if r.get("high") is not None]
    lows = [_safe_float(r.get("low")) for r in rows if r.get("low") is not None]
    if len(closes) < 20 or len(highs) < 20 or len(lows) < 20:
        return {
            "symbol": symbol,
            "decision": "NO_TRADE",
            "reason": "Invalid candle values for decision model.",
            "confidence": 0.0,
            "hold_minutes": hold_minutes,
            "entry_price": None,
            "stop_loss": None,
            "target_price": None,
            "expected_move_pct": 0.0,
            "expected_profit_pct": 0.0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    close = closes[-1]
    prev_close = closes[-2]
    momentum_5 = ((close / closes[-6]) - 1.0) * 100.0 if len(closes) >= 6 and closes[-6] else 0.0
    sma_9 = sum(closes[-9:]) / 9.0
    sma_20 = sum(closes[-20:]) / 20.0
    trend_score = ((sma_9 - sma_20) / sma_20 * 100.0) if sma_20 else 0.0

    tr_samples = []
    for i in range(max(1, len(rows) - 14), len(rows)):
        c_prev = _safe_float(rows[i - 1].get("close"), _safe_float(rows[i].get("close")))
        hi = _safe_float(rows[i].get("high"))
        lo = _safe_float(rows[i].get("low"))
        tr = max(hi - lo, abs(hi - c_prev), abs(lo - c_prev))
        tr_samples.append(tr)
    atr = (sum(tr_samples) / len(tr_samples)) if tr_samples else max(abs(close - prev_close), 0.0)
    atr = max(atr, close * 0.001) if close else atr

    directional_score = (0.65 * trend_score) + (0.35 * momentum_5)
    abs_score = abs(directional_score)
    if abs_score < 0.08:
        decision = "NO_TRADE"
    elif directional_score > 0:
        decision = "BUY"
    else:
        decision = "SELL"

    confidence = min(0.95, max(0.15, abs_score / 0.8))
    rr = 1.8

    if decision == "BUY":
        stop_loss = close - atr
        target_price = close + (atr * rr)
        expected_move_pct = ((target_price - close) / close * 100.0) if close else 0.0
        reason = "Short-term trend and momentum are aligned upward."
    elif decision == "SELL":
        stop_loss = close + atr
        target_price = close - (atr * rr)
        expected_move_pct = ((close - target_price) / close * 100.0) if close else 0.0
        reason = "Short-term trend and momentum are aligned downward."
    else:
        stop_loss = None
        target_price = None
        expected_move_pct = 0.0
        reason = "Price action is range-bound; momentum/trend are weak."

    return {
        "symbol": symbol,
        "decision": decision,
        "reason": reason,
        "confidence": round(confidence, 3),
        "hold_minutes": hold_minutes,
        "entry_price": round(close, 2) if close else None,
        "stop_loss": round(stop_loss, 2) if stop_loss is not None else None,
        "target_price": round(target_price, 2) if target_price is not None else None,
        "expected_move_pct": round(expected_move_pct, 3),
        "expected_profit_pct": round(expected_move_pct, 3),
        "risk_reward": rr if decision != "NO_TRADE" else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@api_view(["GET"])
def intraday_trade_decision(request):
    """
    Returns a lightweight intraday plan for chart overlay simulation.
    Query: symbol=<symbol>&hold_minutes=15
    """
    symbol = (request.GET.get("symbol") or "^NSEI").strip()
    expiry = (request.GET.get("expiry") or "").strip() or None
    hold_minutes_raw = request.GET.get("hold_minutes", "15")
    try:
        hold_minutes = max(1, min(int(hold_minutes_raw), 240))
    except Exception:
        hold_minutes = 15

    # Reuse existing history endpoint data source logic.
    hist_resp = market_history(request, symbol)
    payload = getattr(hist_resp, "data", {}) or {}
    rows = payload.get("history") or []
    decision_payload = _intraday_decision_from_history(
        symbol=symbol,
        rows=rows,
        hold_minutes=hold_minutes,
    )
    decision_payload["price_source"] = payload.get("source")
    return Response(decision_payload)