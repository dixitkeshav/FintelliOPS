"""
Run from backend/: python3 -m quant.backtest_smoke_test
Smoke-tests all templates + sample custom rules on RELIANCE, NIFTY50, SENSEX.
"""
from __future__ import annotations

import json
import os
import sys

# Django env optional — set if .env loaded
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except ImportError:
    pass

from quant.event_backtest import run_event_backtest
from quant.strategy_engine import STRATEGY_TEMPLATES, list_templates

SYMBOLS = ["RELIANCE", "NIFTY50", "SENSEX"]
CUSTOM_RULES = [
    "Buy when RSI is greater than thirty and MFI is less than fifty",
    "Buy when Bollinger Band is greater than twenty on news days",
    "Buy when price is above VWAP and zigzag is bullish",
]

EQUITY_TEMPLATES = [t["id"] for t in list_templates() if t.get("mode_hint") != "options"]
OPTIONS_TEMPLATES = [t["id"] for t in list_templates() if t.get("mode_hint") == "options"]


def _run(label: str, **kwargs) -> dict:
    try:
        out = run_event_backtest(**kwargs)
    except Exception as e:
        return {"label": label, "error": str(e), "trades": 0, "return_pct": None, "period": {}}
    err = out.get("error")
    n = (out.get("summary") or {}).get("total_trades", 0)
    ret = (out.get("summary") or {}).get("total_return_pct")
    period = out.get("period") or {}
    return {"label": label, "error": err, "trades": n, "return_pct": ret, "period": period}


def main() -> None:
    results = []
    days = 126
    only_news = False  # more trades for smoke test

    for sym in SYMBOLS:
        for tid in EQUITY_TEMPLATES:
            if tid == "custom":
                continue
            r = _run(
                f"{sym} | {tid} | delivery",
                ticker=sym,
                mode="equity_delivery",
                template_id=tid,
                only_news_events=only_news,
                days=days,
                custom_only=False,
            )
            results.append(r)

        for prompt in CUSTOM_RULES:
            r = _run(
                f"{sym} | custom | {prompt[:40]}",
                ticker=sym,
                mode="equity_delivery",
                template_id="custom",
                strategy_prompt=prompt,
                only_news_events=only_news,
                days=days,
                custom_only=True,
            )
            results.append(r)

        for tid in OPTIONS_TEMPLATES[:2]:
            r = _run(
                f"{sym} | {tid} | options",
                ticker=sym,
                mode="options",
                template_id=tid,
                only_news_events=only_news,
                days=days,
            )
            results.append(r)

    ok = [x for x in results if not x.get("error")]
    fail = [x for x in results if x.get("error")]
    print(f"\n=== Backtest smoke test ({len(results)} runs) ===")
    print(f"OK: {len(ok)}  Failed: {len(fail)}\n")
    for x in results[:15]:
        print(
            f"  {x['label']}: trades={x.get('trades')} return={x.get('return_pct')}% "
            f"err={x.get('error') or '-'}"
        )
    if len(results) > 15:
        print(f"  ... and {len(results) - 15} more")
    if fail:
        print("\nFailures:")
        for x in fail[:10]:
            print(f"  {x['label']}: {x['error']}")
    print("\n" + json.dumps({"sample_ok": ok[0] if ok else None}, indent=2)[:800])


if __name__ == "__main__":
    main()
