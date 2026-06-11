"""
TradingView-style indicator, candlestick pattern, and strategy catalogs for UI dropdowns.
"""
from __future__ import annotations

from typing import Any

from quant.strategy_engine import list_templates

# Indicators available in-engine or via extended compute (subset computed in technical_snapshot)
INDICATOR_CATALOG: list[dict[str, Any]] = [
    {"id": "rsi", "name": "RSI", "category": "Momentum", "computed": True},
    {"id": "mfi", "name": "Money Flow Index (MFI)", "category": "Momentum", "computed": True},
    {"id": "macd", "name": "MACD", "category": "Momentum", "computed": True},
    {"id": "macd_signal", "name": "MACD Signal", "category": "Momentum", "computed": True},
    {"id": "macd_hist", "name": "MACD Histogram", "category": "Momentum", "computed": True},
    {"id": "stoch_k", "name": "Stochastic %K", "category": "Momentum", "computed": True},
    {"id": "stoch_d", "name": "Stochastic %D", "category": "Momentum", "computed": True},
    {"id": "cci", "name": "CCI", "category": "Momentum", "computed": True},
    {"id": "williams_r", "name": "Williams %R", "category": "Momentum", "computed": True},
    {"id": "roc", "name": "Rate of Change", "category": "Momentum", "computed": True},
    {"id": "momentum", "name": "Momentum", "category": "Momentum", "computed": True},
    {"id": "adx", "name": "ADX", "category": "Momentum", "computed": True},
    {"id": "plus_di", "name": "+DI", "category": "Momentum", "computed": True},
    {"id": "minus_di", "name": "-DI", "category": "Momentum", "computed": True},
    {"id": "sma_20", "name": "SMA 20", "category": "Trend", "computed": True},
    {"id": "sma_50", "name": "SMA 50", "category": "Trend", "computed": True},
    {"id": "sma_200", "name": "SMA 200", "category": "Trend", "computed": True},
    {"id": "ema_12", "name": "EMA 12", "category": "Trend", "computed": True},
    {"id": "ema_26", "name": "EMA 26", "category": "Trend", "computed": True},
    {"id": "bb_pct", "name": "Bollinger %B", "category": "Volatility", "computed": True},
    {"id": "bb_upper", "name": "Bollinger Upper", "category": "Volatility", "computed": True},
    {"id": "bb_lower", "name": "Bollinger Lower", "category": "Volatility", "computed": True},
    {"id": "atr", "name": "ATR", "category": "Volatility", "computed": True},
    {"id": "atr_pct", "name": "ATR %", "category": "Volatility", "computed": True},
    {"id": "vwap_dist", "name": "VWAP Distance %", "category": "Volume", "computed": True},
    {"id": "obv", "name": "OBV", "category": "Volume", "computed": True},
    {"id": "volume_sma_ratio", "name": "Volume / SMA(20)", "category": "Volume", "computed": True},
    {"id": "zigzag_trend", "name": "Zigzag Trend", "category": "Trend", "computed": True},
    {"id": "return_1d", "name": "1D Return %", "category": "Price Action", "computed": True},
    {"id": "return_5d", "name": "5D Return %", "category": "Price Action", "computed": True},
    {"id": "return_21d", "name": "21D Return %", "category": "Price Action", "computed": True},
    {"id": "high_52w_dist", "name": "Distance from 52W High %", "category": "Price Action", "computed": True},
    {"id": "low_52w_dist", "name": "Distance from 52W Low %", "category": "Price Action", "computed": True},
    {"id": "ichimoku_tenkan", "name": "Ichimoku Tenkan", "category": "Trend", "computed": False},
    {"id": "ichimoku_kijun", "name": "Ichimoku Kijun", "category": "Trend", "computed": False},
    {"id": "parabolic_sar", "name": "Parabolic SAR", "category": "Trend", "computed": False},
    {"id": "supertrend", "name": "SuperTrend", "category": "Trend", "computed": False},
    {"id": "keltner_upper", "name": "Keltner Upper", "category": "Volatility", "computed": False},
    {"id": "keltner_lower", "name": "Keltner Lower", "category": "Volatility", "computed": False},
    {"id": "donchian_upper", "name": "Donchian Upper", "category": "Volatility", "computed": False},
    {"id": "donchian_lower", "name": "Donchian Lower", "category": "Volatility", "computed": False},
    {"id": "pivot_r1", "name": "Pivot R1", "category": "Support/Resistance", "computed": False},
    {"id": "pivot_s1", "name": "Pivot S1", "category": "Support/Resistance", "computed": False},
    {"id": "fib_382", "name": "Fib 38.2%", "category": "Support/Resistance", "computed": False},
    {"id": "fib_618", "name": "Fib 61.8%", "category": "Support/Resistance", "computed": False},
    {"id": "hma", "name": "Hull MA", "category": "Trend", "computed": False},
    {"id": "vwma", "name": "VWMA", "category": "Volume", "computed": False},
    {"id": "cmf", "name": "Chaikin Money Flow", "category": "Volume", "computed": False},
    {"id": "force_index", "name": "Force Index", "category": "Volume", "computed": False},
    {"id": "eom", "name": "Ease of Movement", "category": "Volume", "computed": False},
    {"id": "aroon_up", "name": "Aroon Up", "category": "Momentum", "computed": False},
    {"id": "aroon_down", "name": "Aroon Down", "category": "Momentum", "computed": False},
    {"id": "tsi", "name": "True Strength Index", "category": "Momentum", "computed": False},
    {"id": "ultimate_osc", "name": "Ultimate Oscillator", "category": "Momentum", "computed": False},
    {"id": "elder_ray", "name": "Elder Ray", "category": "Momentum", "computed": False},
]

CANDLESTICK_PATTERNS: list[dict[str, Any]] = [
    {"id": "doji", "name": "Doji", "category": "Single"},
    {"id": "hammer", "name": "Hammer", "category": "Single"},
    {"id": "inverted_hammer", "name": "Inverted Hammer", "category": "Single"},
    {"id": "shooting_star", "name": "Shooting Star", "category": "Single"},
    {"id": "hanging_man", "name": "Hanging Man", "category": "Single"},
    {"id": "marubozu_bull", "name": "Bullish Marubozu", "category": "Single"},
    {"id": "marubozu_bear", "name": "Bearish Marubozu", "category": "Single"},
    {"id": "spinning_top", "name": "Spinning Top", "category": "Single"},
    {"id": "engulfing_bull", "name": "Bullish Engulfing", "category": "Double"},
    {"id": "engulfing_bear", "name": "Bearish Engulfing", "category": "Double"},
    {"id": "harami_bull", "name": "Bullish Harami", "category": "Double"},
    {"id": "harami_bear", "name": "Bearish Harami", "category": "Double"},
    {"id": "piercing", "name": "Piercing Line", "category": "Double"},
    {"id": "dark_cloud", "name": "Dark Cloud Cover", "category": "Double"},
    {"id": "tweezer_top", "name": "Tweezer Top", "category": "Double"},
    {"id": "tweezer_bottom", "name": "Tweezer Bottom", "category": "Double"},
    {"id": "morning_star", "name": "Morning Star", "category": "Triple"},
    {"id": "evening_star", "name": "Evening Star", "category": "Triple"},
    {"id": "three_white_soldiers", "name": "Three White Soldiers", "category": "Triple"},
    {"id": "three_black_crows", "name": "Three Black Crows", "category": "Triple"},
    {"id": "three_inside_up", "name": "Three Inside Up", "category": "Triple"},
    {"id": "three_inside_down", "name": "Three Inside Down", "category": "Triple"},
    {"id": "rising_three", "name": "Rising Three Methods", "category": "Continuation"},
    {"id": "falling_three", "name": "Falling Three Methods", "category": "Continuation"},
    {"id": "abandoned_baby_bull", "name": "Bullish Abandoned Baby", "category": "Triple"},
    {"id": "abandoned_baby_bear", "name": "Bearish Abandoned Baby", "category": "Triple"},
]


def get_full_catalog() -> dict[str, Any]:
    strategies = list_templates()
    return {
        "indicators": INDICATOR_CATALOG,
        "candlestick_patterns": CANDLESTICK_PATTERNS,
        "strategies": strategies,
        "indicator_count": len(INDICATOR_CATALOG),
        "pattern_count": len(CANDLESTICK_PATTERNS),
        "strategy_count": len(strategies),
    }
