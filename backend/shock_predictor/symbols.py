"""
Ticker universe for shock monitoring — curated NSE lists.
"""
from __future__ import annotations

from typing import Any

# Curated NSE large / mid / small (representative liquid names)
LARGE_CAP = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN",
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
]
MID_CAP = [
    "PIDILITIND", "DIXON", "POLYCAB", "PERSISTENT", "COFORGE", "MPHASIS", "AUROPHARMA",
    "GODREJCP", "INDHOTEL", "BANKBARODA", "CANBK", "NHPC", "IRCTC", "BEL",
]
SMALL_CAP = [
    "IRCON", "RVNL", "HFCL", "SUZLON", "YESBANK", "IDEA", "PNB", "NMDC", "SAIL", "BHEL",
]

INDICES = [
    {"symbol": "NIFTY", "yf": "^NSEI", "type": "index"},
    {"symbol": "BANKNIFTY", "yf": "^NSEBANK", "type": "index"},
    {"symbol": "SENSEX", "yf": "^BSESN", "type": "index"},
]


def get_universe(group: str = "all") -> dict[str, Any]:
    g = (group or "all").lower()
    payload = {
        "indices": INDICES,
        "large_cap": LARGE_CAP,
        "mid_cap": MID_CAP,
        "small_cap": SMALL_CAP,
        "source": "curated",
    }
    if g == "large_cap":
        payload["symbols"] = LARGE_CAP
    elif g == "mid_cap":
        payload["symbols"] = MID_CAP
    elif g == "small_cap":
        payload["symbols"] = SMALL_CAP
    elif g == "indices":
        payload["symbols"] = [x["symbol"] for x in INDICES]
    else:
        payload["symbols"] = list(dict.fromkeys(LARGE_CAP + MID_CAP + SMALL_CAP))
    payload["count"] = len(payload["symbols"])
    return payload
