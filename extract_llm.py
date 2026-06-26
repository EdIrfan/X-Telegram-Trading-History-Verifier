#!/usr/bin/env python3
"""
LLM-based extraction + verification of @blockchainedbb's crypto calls.

For each candidate post (mentions a coin OR has a chart image), Claude reads the
TEXT and the CHART IMAGE and returns a structured call. We then verify each real
directional call against Binance OHLCV (TradingView-matching) over a 7-day window
and compute an accuracy rate.

Why LLM instead of regex: her calls are conversational (sarcasm, rhetorical
questions), distinguish opening vs closing trades, and put precise levels inside
chart screenshots that text parsing can't read.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python extract_llm.py --horizon 7 [--model claude-opus-4-8] [--limit N]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import anthropic

from prices import price_at, range_high_low

DATA = os.path.join(os.path.dirname(__file__), "data")
COIN_HINT = ("btc", "bitcoin", "eth", "ethereum", "sol", "solana", "xrp", "ripple",
             "doge", "bnb", "ada", "avax", "link", "sui", "$")

SYSTEM = """You analyze a crypto trader's social-media post (text + optional chart \
image) and extract any actionable price call as STRICT JSON.

A "trade call" is a NEW, falsifiable directional view on a specific coin: a long/buy \
or short/sell, a bullish/bearish bias, a buy/sell zone, or a price target. \
NOT trade calls: pure promotion (Discord/giveaways), education/commentary with no \
bias, screenshots of past PnL, or posts that ONLY close/update an existing position.

Rules:
- Read the CHART IMAGE too — entries/targets/levels are often only on the chart.
- Interpret tone: rhetorical questions ("does that look bearish?") usually mean the \
OPPOSITE; "closed my short" is NOT a new short.
- direction is the trader's view going forward: "long" (expects up) or "short" \
(expects down), else "neutral".
- Numbers: express like 110000 (not "110k"). Use null when absent.
- If several coins, pick the primary one the call is about."""

SCHEMA = {
    "type": "object",
    "properties": {
        "is_trade_call": {"type": "boolean"},
        "is_close_or_update": {"type": "boolean"},
        "coin": {"type": ["string", "null"]},
        "direction": {"type": ["string", "null"],
                      "enum": ["long", "short", "neutral", None]},
        "entry": {"type": ["number", "null"]},
        "targets": {"type": "array", "items": {"type": "number"}},
        "stop": {"type": ["number", "null"]},
        "timeframe_days": {"type": ["integer", "null"]},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    },
    "required": ["is_trade_call", "is_close_or_update", "coin", "direction",
                 "entry", "targets", "stop", "timeframe_days", "confidence",
                 "rationale"],
    "additionalProperties": False,
}


def is_candidate(p):
    t = (p.get("text") or "").lower()
    return bool(p.get("images")) or any(h in t for h in COIN_HINT)


def extract_one(client, model, post):
    content = []
    for img in (post.get("images") or [])[:2]:  # at most 2 chart images
        content.append({"type": "image", "source": {"type": "url", "url": img}})
    content.append({"type": "text",
                    "text": f"Post text:\n{post.get('text','')[:1500]}"})
    resp = client.messages.create(
        model=model, max_tokens=700, system=SYSTEM,
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    txt = next(b.text for b in resp.content if b.type == "text")
    return json.loads(txt)


def verify(coin, post_dt, direction, targets, horizon):
    start = datetime.fromisoformat(post_dt.replace("Z", "+00:00"))
    end = min(start + timedelta(days=horizon), datetime.now(timezone.utc))
    if end <= start + timedelta(hours=12):
        return "UNVERIFIABLE", {}, "too recent"
    try:
        p0 = price_at(coin, start)
        lo, hi = range_high_low(coin, start, end)
        pend = price_at(coin, end)
    except Exception as e:
        return "UNVERIFIABLE", {}, f"no price data ({e})"
    if not p0 or not pend:
        return "UNVERIFIABLE", {}, "coin not on Binance"
    move = (pend - p0) / p0 * 100
    d = {"entry": round(p0, 4), "low": round(lo, 4), "high": round(hi, 4),
         "exit": round(pend, 4), "move_pct": round(move, 2)}
    near = [t for t in (targets or []) if 0.3 * p0 <= t <= 3 * p0]
    if near and direction in ("long", "short"):
        tgt = max(near) if direction == "long" else min(near)
        d["target"] = tgt
        if (direction == "long" and hi >= tgt) or (direction == "short" and lo <= tgt):
            return "CORRECT", d, f"target {tgt:g} hit in {horizon}d"
    if direction == "long":
        return ("CORRECT" if move >= 3 else "INCORRECT"), d, f"{move:+.1f}% in {horizon}d"
    if direction == "short":
        return ("CORRECT" if move <= -3 else "INCORRECT"), d, f"{move:+.1f}% in {horizon}d"
    return "UNVERIFIABLE", d, "no direction"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--limit", type=int, default=0, help="cap candidates (testing)")
    ap.add_argument("--resume", action="store_true", help="skip already-extracted")
    a = ap.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    posts = json.load(open(os.path.join(DATA, "posts.json")))["posts"]
    cands = [p for p in posts if is_candidate(p)]
    if a.limit:
        cands = cands[:a.limit]
    print(f"candidates={len(cands)} model={a.model}", flush=True)

    out_path = os.path.join(DATA, "calls_llm.json")
    done = {}
    if a.resume and os.path.exists(out_path):
        done = {r["permalink"]: r for r in json.load(open(out_path))["rows"]}

    rows = list(done.values())
    for i, p in enumerate(cands):
        key = p.get("permalink") or p.get("datetime")
        if key in done:
            continue
        try:
            ext = extract_one(client, a.model, p)
        except Exception as e:
            print(f"  [{i}] extract error: {e}", flush=True)
            continue
        verdict, detail, why = "SKIP", {}, "not a trade call"
        if ext.get("is_trade_call") and not ext.get("is_close_or_update") \
                and ext.get("coin") and ext.get("direction") in ("long", "short"):
            verdict, detail, why = verify(
                ext["coin"], p["datetime"], ext["direction"],
                ext.get("targets"), ext["timeframe_days"] or a.horizon)
        rows.append({"datetime": p["datetime"], "permalink": key,
                     "text": (p.get("text") or "")[:200],
                     "has_image": bool(p.get("images")),
                     "extracted": ext, "verdict": verdict,
                     "detail": detail, "why": why})
        if i % 20 == 0:
            json.dump({"rows": rows}, open(out_path, "w"), indent=2)
            print(f"  [{i}/{len(cands)}] {verdict:12} {ext.get('coin')} "
                  f"{ext.get('direction')}", flush=True)

    json.dump({"model": a.model, "horizon": a.horizon, "rows": rows},
              open(out_path, "w"), indent=2)
    c = sum(r["verdict"] == "CORRECT" for r in rows)
    w = sum(r["verdict"] == "INCORRECT" for r in rows)
    u = sum(r["verdict"] == "UNVERIFIABLE" for r in rows)
    s = sum(r["verdict"] == "SKIP" for r in rows)
    acc = c / (c + w) * 100 if (c + w) else 0
    print(f"\nscored={c+w} correct={c} incorrect={w} unverifiable={u} "
          f"not-a-call={s}\nACCURACY = {acc:.1f}%  (horizon={a.horizon}d)", flush=True)


if __name__ == "__main__":
    main()
