"""
Strategy templates and natural-language rule parsing for backtests.
"""
from __future__ import annotations

import re
from typing import Any, Optional

STRATEGY_TEMPLATES: dict[str, dict[str, Any]] = {
    "custom": {
        "id": "custom",
        "name": "Custom rules only",
        "description": "Use only your English rules below (no template defaults). Click “Fix with AI” to align wording.",
        "mode_hint": "equity",
        "requires_news": False,
        "default_rules": [],
        "action": "BUY",
    },
    "news_event_long": {
        "id": "news_event_long",
        "name": "News event — go long",
        "description": "Enter long only on days with relevant company news; exit next day (intraday) or on bearish RSI (delivery).",
        "mode_hint": "equity",
        "requires_news": True,
        "default_rules": [
            {"type": "news_event"},
            {"type": "indicator", "indicator": "rsi", "op": "<", "value": 75},
        ],
        "action": "BUY",
    },
    "rsi_oversold_bounce": {
        "id": "rsi_oversold_bounce",
        "name": "RSI oversold bounce",
        "description": "Buy when RSI is below 35 (oversold); popular mean-reversion setup.",
        "mode_hint": "equity",
        "requires_news": False,
        "default_rules": [{"type": "indicator", "indicator": "rsi", "op": "<", "value": 35}],
        "action": "BUY",
    },
    "rsi_mfi_momentum": {
        "id": "rsi_mfi_momentum",
        "name": "RSI + MFI momentum",
        "description": "Buy when RSI > 50 and MFI < 50.",
        "mode_hint": "equity",
        "requires_news": False,
        "default_rules": [
            {"type": "indicator", "indicator": "rsi", "op": ">", "value": 50},
            {"type": "indicator", "indicator": "mfi", "op": "<", "value": 50},
        ],
        "action": "BUY",
    },
    "bb_vwap_zigzag": {
        "id": "bb_vwap_zigzag",
        "name": "Bollinger + VWAP + Zigzag",
        "description": "Multi-indicator: %B not overbought, price above VWAP, zigzag bullish.",
        "mode_hint": "equity",
        "requires_news": False,
        "default_rules": [
            {"type": "indicator", "indicator": "bb_pct", "op": "<", "value": 80},
            {"type": "indicator", "indicator": "vwap_dist", "op": ">", "value": 0},
            {"type": "indicator", "indicator": "zigzag_trend", "op": ">", "value": 0},
        ],
        "action": "BUY",
    },
    "sentiment_news_combo": {
        "id": "sentiment_news_combo",
        "name": "Positive news + not overbought",
        "description": "Trade only on relevant news days when headline sentiment is positive and RSI < 70.",
        "mode_hint": "equity",
        "requires_news": True,
        "default_rules": [
            {"type": "news_event"},
            {"type": "sentiment", "op": ">", "value": 0},
            {"type": "indicator", "indicator": "rsi", "op": "<", "value": 70},
        ],
        "action": "BUY",
    },
    "iron_condor": {
        "id": "iron_condor",
        "name": "Iron Condor (options)",
        "description": "Neutral options structure — profits when underlying stays in a range.",
        "mode_hint": "options",
        "requires_news": False,
        "options_structure": "iron_condor",
        "default_rules": [{"type": "indicator", "indicator": "rsi", "op": "between", "value": 40, "value2": 60}],
        "action": "SELL_VOL",
    },
    "butterfly": {
        "id": "butterfly",
        "name": "Butterfly spread (options)",
        "description": "Defined-risk neutral strategy centered at ATM.",
        "mode_hint": "options",
        "requires_news": True,
        "options_structure": "butterfly",
        "default_rules": [{"type": "news_event"}],
        "action": "NEUTRAL",
    },
    "long_straddle_news": {
        "id": "long_straddle_news",
        "name": "Long straddle on news",
        "description": "Buy vol on major news — profits from large same-day move.",
        "mode_hint": "options",
        "requires_news": True,
        "options_structure": "long_straddle",
        "default_rules": [{"type": "news_event"}],
        "action": "BUY_VOL",
    },
}

_OP_MAP = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: abs(a - b) < 1e-6,
    "between": lambda a, b, c: b <= a <= c,
    "near": lambda a, b, c: abs(a - b) <= c,
}

_WORD_NUMS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "ten": 10,
    "fifteen": 15,
    "twenty": 20,
    "twenty-five": 25,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
}


def _word_to_num(token: str) -> Optional[float]:
    t = token.strip().lower()
    if t in _WORD_NUMS:
        return float(_WORD_NUMS[t])
    try:
        return float(t)
    except ValueError:
        return None


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "mode_hint": t.get("mode_hint", "equity"),
            "requires_news": t.get("requires_news", False),
            "options_structure": t.get("options_structure"),
        }
        for t in STRATEGY_TEMPLATES.values()
    ]


def get_template(template_id: str) -> Optional[dict[str, Any]]:
    return STRATEGY_TEMPLATES.get(template_id)


def parse_strategy_prompt(prompt: str) -> list[dict[str, Any]]:
    text = (prompt or "").strip().lower()
    if not text:
        return []

    rules: list[dict[str, Any]] = []
    if re.search(r"\bnews\b|\bheadline\b|\bevent\b", text):
        rules.append({"type": "news_event"})

    def add_ind(ind: str, op: str, val: float, val2: Optional[float] = None):
        r: dict[str, Any] = {"type": "indicator", "indicator": ind, "op": op, "value": val}
        if val2 is not None:
            r["value2"] = val2
        rules.append(r)

    # RSI / MFI / MACD
    for pat, ind, op in [
        (r"rsi\s*(?:is\s*)?(?:greater than|above|over|>)\s*([\w-]+)", "rsi", ">"),
        (r"rsi\s*(?:is\s*)?(?:less than|below|under|<)\s*([\w-]+)", "rsi", "<"),
        (r"mfi\s*(?:is\s*)?(?:greater than|above|>)\s*([\w-]+)", "mfi", ">"),
        (r"mfi\s*(?:is\s*)?(?:less than|below|<)\s*([\w-]+)", "mfi", "<"),
    ]:
        for m in re.finditer(pat, text):
            v = _word_to_num(m.group(1))
            if v is not None:
                add_ind(ind, op, v)

    # Bollinger
    for m in re.finditer(
        r"bollinger(?:\s*band)?(?:\s*%?b|\s*score)?\s*(?:is\s*)?(?:greater than|above|>)\s*([\w-]+)",
        text,
    ):
        v = _word_to_num(m.group(1))
        if v is not None:
            add_ind("bb_pct", ">", v)
    for m in re.finditer(
        r"bollinger(?:\s*band)?(?:\s*%?b|\s*score)?\s*(?:is\s*)?(?:less than|below|<)\s*([\w-]+)",
        text,
    ):
        v = _word_to_num(m.group(1))
        if v is not None:
            add_ind("bb_pct", "<", v)
    for m in re.finditer(r"bollinger.*?between\s*([\w-]+)\s*(?:and|to)\s*([\w-]+)", text):
        a, b = _word_to_num(m.group(1)), _word_to_num(m.group(2))
        if a is not None and b is not None:
            add_ind("bb_pct", "between", min(a, b), max(a, b))

    # VWAP
    for m in re.finditer(r"vwap\s*(?:is\s*)?(?:around|near|about)\s*([\w-]+)", text):
        v = _word_to_num(m.group(1))
        if v is not None:
            add_ind("vwap_dist", "near", v, 3.0)
    for m in re.finditer(r"(?:above|over)\s*vwap|vwap\s*(?:above|over)", text):
        add_ind("vwap_dist", ">", 0)
    for m in re.finditer(r"(?:below|under)\s*vwap|vwap\s*(?:below|under)", text):
        add_ind("vwap_dist", "<", 0)

    # Zigzag
    if re.search(r"zig\s*zag.*bullish|bullish.*zig\s*zag", text):
        add_ind("zigzag_trend", ">", 0)
    if re.search(r"zig\s*zag.*bearish|bearish.*zig\s*zag", text):
        add_ind("zigzag_trend", "<", 0)

    if re.search(r"macd\s*(?:is\s*)?(?:positive|above\s*0)", text):
        add_ind("macd_hist", ">", 0)
    if re.search(r"macd\s*(?:is\s*)?(?:negative|below\s*0)", text):
        add_ind("macd_hist", "<", 0)

    if re.search(r"sentiment\s*(?:is\s*)?(?:positive|bullish)", text):
        rules.append({"type": "sentiment", "op": ">", "value": 0})
    if re.search(r"sentiment\s*(?:is\s*)?(?:negative|bearish)", text):
        rules.append({"type": "sentiment", "op": "<", "value": 0})

    return rules


def resolve_rules(
    template_id: Optional[str],
    custom_prompt: Optional[str],
    *,
    custom_only: bool = False,
    compiled_rules: Optional[list[dict]] = None,
    compiled_meta: Optional[dict] = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (template_meta, rules_list)."""
    prompt = (custom_prompt or "").strip()
    use_custom_only = custom_only or template_id == "custom" or bool(prompt and custom_only)

    if compiled_rules:
        meta = compiled_meta or {
            "id": template_id or "custom",
            "name": "AI-compiled strategy",
            "description": prompt or "Compiled by Groq",
        }
        if template_id and template_id in STRATEGY_TEMPLATES and not use_custom_only:
            tpl = STRATEGY_TEMPLATES[template_id]
            merged = list(tpl.get("default_rules") or []) + list(compiled_rules)
            out = dict(tpl)
            if compiled_meta:
                out.update({k: compiled_meta.get(k) for k in ("action", "options_structure", "risk_reward") if compiled_meta.get(k)})
            return out, merged
        return meta, list(compiled_rules)

    if use_custom_only or (template_id == "custom"):
        rules = parse_strategy_prompt(prompt)
        meta = {
            "id": "custom",
            "name": "Custom (natural language)",
            "description": prompt or "User-defined rules",
            "mode_hint": "equity",
            "action": "BUY",
        }
        if template_id and template_id in STRATEGY_TEMPLATES:
            tpl = STRATEGY_TEMPLATES[template_id]
            meta["mode_hint"] = tpl.get("mode_hint", "equity")
            if tpl.get("options_structure"):
                meta["options_structure"] = tpl["options_structure"]
        return meta, rules

    if template_id and template_id in STRATEGY_TEMPLATES:
        tpl = STRATEGY_TEMPLATES[template_id]
        rules = list(tpl.get("default_rules") or [])
        if prompt:
            rules.extend(parse_strategy_prompt(prompt))
        return tpl, rules

    rules = parse_strategy_prompt(prompt)
    meta = {
        "id": "custom",
        "name": "Custom (natural language)",
        "description": prompt or "User-defined rules",
        "mode_hint": "equity",
    }
    return meta, rules


def _eval_indicator(rule: dict, row: dict, sentiment_score: float, has_news: bool) -> bool:
    rtype = rule.get("type")
    if rtype == "news_event":
        return has_news
    if rtype == "sentiment":
        op = rule.get("op", ">")
        val = float(rule.get("value", 0))
        fn = _OP_MAP.get(op)
        return bool(fn(sentiment_score, val)) if fn else False
    if rtype != "indicator":
        return True

    ind = rule.get("indicator", "")
    op = rule.get("op", ">")
    val = float(rule.get("value", 0))
    val2 = rule.get("value2")
    raw = row.get(ind)
    if raw is None or (isinstance(raw, float) and raw != raw):
        return False
    x = float(raw)
    if op == "between" and val2 is not None:
        return bool(_OP_MAP["between"](x, val, float(val2)))
    if op == "near":
        half = float(val2 if val2 is not None else 5.0)
        return bool(_OP_MAP["near"](x, val, half))
    fn = _OP_MAP.get(op)
    return bool(fn(x, val)) if fn else False


def rules_pass(
    rules: list[dict],
    row: dict,
    sentiment_score: float,
    has_news: bool,
) -> bool:
    if not rules:
        return has_news
    return all(_eval_indicator(r, row, sentiment_score, has_news) for r in rules)
