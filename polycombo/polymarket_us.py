"""Read-only market data from Polymarket US's public gateway (no account, no API key).

Docs: https://docs.polymarket.us/api-reference/introduction
This module never places orders. It only reads prices.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

GATEWAY = "https://gateway.polymarket.us"


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    qs = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None},
                                doseq=True)
    url = f"{GATEWAY}{path}" + (f"?{qs}" if qs else "")
    req = urllib.request.Request(url, headers={"User-Agent": "polycombo/0.2",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _amt(x: Any) -> Optional[float]:
    """Amount objects look like {"value": "0.55", "currency": "USD"}."""
    if isinstance(x, dict):
        x = x.get("value")
    try:
        return float(x) if x not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _sides(m: dict) -> List[dict]:
    out = []
    for s in m.get("marketSides") or []:
        name = (s.get("description") or s.get("identifier") or s.get("title")
                or (s.get("team") or {}).get("name") or "")
        out.append({"name": name, "price": _amt(s.get("price"))})
    return out


def parse_market(m: dict) -> dict:
    return {
        "slug": m.get("slug"),
        "question": m.get("question") or m.get("title"),
        "bid": _amt(m.get("bestBidQuote")),
        "ask": _amt(m.get("bestAskQuote")),
        "sides": _sides(m),
        "active": m.get("active", True) and not m.get("closed", False),
    }


def parse_event(e: dict) -> dict:
    return {
        "title": e.get("title"),
        "slug": e.get("slug"),
        "start": e.get("startTime") or e.get("startDate"),
        "markets": [parse_market(m) for m in e.get("markets") or []],
    }


def search(query: str, limit: int = 10, combo_only: bool = True) -> List[dict]:
    data = _get("/v1/search", {"query": query, "limit": limit,
                               "comboEnabledOnly": "true" if combo_only else None})
    return [parse_event(e) for e in data.get("events", [])]


def league_events(league: str, limit: int = 20) -> List[dict]:
    data = _get(f"/v2/leagues/{urllib.parse.quote(league)}/events", {"limit": limit})
    return [parse_event(e) for e in data.get("events", [])]


def bbo(slug: str) -> dict:
    d = _get(f"/v1/markets/{urllib.parse.quote(slug)}/bbo").get("marketData", {})
    return {
        "slug": d.get("marketSlug", slug),
        "bid": _amt(d.get("bestBid")),
        "ask": _amt(d.get("bestAsk")),
        "last": _amt(d.get("lastTradePx")),
        "state": d.get("state"),
    }
