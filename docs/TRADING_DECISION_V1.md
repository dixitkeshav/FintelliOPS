# Trading Decision V1

This V1 adds a lightweight intraday decision flow and chart-based paper-trade tracing for the Markets page.

## What it does

- Click any market symbol card to expand a detailed view.
- Fetch an intraday decision (`BUY`, `SELL`, `NO_TRADE`) from backend.
- Show entry, stop-loss, target, hold duration, confidence, and expected profit.
- Start a paper trade and track it live against current market price.
- Draw entry/SL/TP levels directly on the chart.
- Auto-close trade on:
  - target hit
  - SL hit
  - hold-time expiry
- Apply basic trailing logic: once trade reaches +0.5%, SL moves to entry.

## Backend API

### `GET /api/trade/decision/`

Query params:

- `symbol` (default: `^NSEI`)
- `hold_minutes` (1-240, default: `15`)

Response (example):

```json
{
  "symbol": "^NSEI",
  "decision": "BUY",
  "reason": "Short-term trend and momentum are aligned upward.",
  "confidence": 0.62,
  "hold_minutes": 15,
  "entry_price": 23791.3,
  "stop_loss": 23742.6,
  "target_price": 23878.9,
  "expected_move_pct": 0.368,
  "expected_profit_pct": 0.368,
  "risk_reward": 1.8,
  "generated_at": "2026-05-29T00:00:00+00:00",
  "price_source": "finnhub"
}
```

## Frontend behavior

- Uses live ticker feed for current price.
- Uses market history API for chart candles/line data.
- Decision refresh is manual via **Refresh Decision** button.
- Trade status/events are tracked in local client state (paper mode only).

## Notes

- This is a deterministic heuristic model for fast iteration (not ML execution advice).
- Designed as a clean foundation for future:
  - options-specific signals
  - broker execution hooks
  - multi-trade journal persistence
