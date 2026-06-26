#!/usr/bin/env python3
"""
Turn scraped posts into scored crypto price-calls.

Pipeline:
  1. classify each post -> PROMO / EDUCATIONAL / CALL_CANDIDATE / OTHER
  2. for CALL_CANDIDATE, extract (coins, direction, price levels, timeframe)
  3. verify each call against Binance OHLCV (TradingView-matching) and score
  4. write data/report.json + a printed summary

ACCURACY RUBRIC (transparent + falsifiable):
  A post is a *verifiable call* if it names a coin AND expresses a direction
  (long/short/buy/sell/bullish/bearish/bottom/top) and/or a price target.
  Verification window = post time -> +HORIZON days (default 14), capped at today.
    - directional CORRECT if price moved >= MOVE_THRESHOLD% the called way
      (close at window end vs price at post), OR a stated target was touched.
    - target-hit CORRECT if range high/low over window reaches the target.
    - otherwise INCORRECT.
  Posts with no coin, no direction, or pure promo are EXCLUDED (not scored).
  accuracy = CORRECT / (CORRECT + INCORRECT)
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from prices import price_at, range_high_low

DATA = os.path.join(os.path.dirname(__file__), "data")
HORIZON_DAYS = 14
MOVE_THRESHOLD = 3.0  # % move needed to count a directional call right

COINS = {
    "BTC": ["btc", "bitcoin", "$btc"], "ETH": ["eth", "ethereum", "$eth"],
    "SOL": ["sol", "solana", "$sol"], "XRP": ["xrp", "$xrp", "ripple"],
    "DOGE": ["doge", "$doge"], "BNB": ["bnb", "$bnb"], "ADA": ["ada", "$ada"],
    "AVAX": ["avax", "$avax"], "LINK": ["link", "$link"], "SUI": ["sui", "$sui"],
}
PROMO = re.compile(r"discord|telegram|t\.me/|giveaway|impersonat|scam|"
                   r"link in (1st )?comment|dm you first|join", re.I)
LONG = re.compile(r"\b(long|buy|buying|bought|bullish|accumulat|bottom|"
                  r"breakout|moon|up only|reclaim|bounce)\b", re.I)
SHORT = re.compile(r"\b(short|shorting|sell|selling|sold|bearish|top|"
                   r"dump|breakdown|rejection|take profit|exit)\b", re.I)
# price tokens like 110k, $55-58k, 0.42, 2,350
PRICE = re.compile(r"\$?\d[\d,]*\.?\d*\s*[kK]?(?:\s*-\s*\$?\d[\d,]*\.?\d*\s*[kK]?)?")


def _num(tok: str):
    tok = tok.replace("$", "").replace(",", "").strip()
    mult = 1000 if tok.lower().endswith("k") else 1
    tok = tok.lower().rstrip("k").strip()
    try:
        return float(tok) * mult
    except ValueError:
        return None


def find_coins(text: str):
    t = f" {text.lower()} "
    found = []
    for sym, aliases in COINS.items():
        if any(re.search(rf"(?<![a-z]){re.escape(a)}(?![a-z])", t) for a in aliases):
            found.append(sym)
    return found


def classify(text: str):
    if not text or len(text.strip()) < 4:
        return "OTHER"
    coins = find_coins(text)
    has_dir = bool(LONG.search(text) or SHORT.search(text))
    has_price = bool(PRICE.search(text))
    if PROMO.search(text) and not (coins and (has_dir or has_price)):
        return "PROMO"
    if coins and (has_dir or has_price):
        return "CALL_CANDIDATE"
    return "OTHER"


def extract(text: str):
    coins = find_coins(text)
    nlong, nshort = len(LONG.findall(text)), len(SHORT.findall(text))
    direction = "long" if nlong > nshort else "short" if nshort > nlong else "neutral"
    levels = []
    for m in PRICE.finditer(text):
        for part in re.split(r"-", m.group()):
            v = _num(part)
            if v and v > 0.01:
                levels.append(v)
    return {"coins": coins, "direction": direction, "levels": sorted(set(levels))}


def verify(coin, post_dt, direction, levels, horizon=HORIZON_DAYS):
    """Return (verdict, detail). verdict in CORRECT/INCORRECT/UNVERIFIABLE."""
    start = datetime.fromisoformat(post_dt.replace("Z", "+00:00"))
    end = min(start + timedelta(days=horizon), datetime.now(timezone.utc))
    if end <= start + timedelta(hours=12):
        return "UNVERIFIABLE", "too recent to verify"
    try:
        p0 = price_at(coin, start)
        lo, hi = range_high_low(coin, start, end)
        pend = price_at(coin, end)
    except Exception as e:
        return "UNVERIFIABLE", f"price fetch failed: {e}"
    if p0 is None or pend is None:
        return "UNVERIFIABLE", "no price data"
    detail = {"entry": p0, "window_low": lo, "window_high": hi, "exit": pend}
    # target-hit check
    nearby = [l for l in levels if 0.3 * p0 <= l <= 3 * p0]
    if nearby and direction in ("long", "short"):
        tgt = max(nearby) if direction == "long" else min(nearby)
        hit = (direction == "long" and hi >= tgt) or \
              (direction == "short" and lo <= tgt)
        detail["target"] = tgt
        if hit:
            return "CORRECT", detail
    # directional check
    move = (pend - p0) / p0 * 100
    detail["move_pct"] = round(move, 2)
    if direction == "long":
        return ("CORRECT" if move >= MOVE_THRESHOLD else "INCORRECT"), detail
    if direction == "short":
        return ("CORRECT" if move <= -MOVE_THRESHOLD else "INCORRECT"), detail
    return "UNVERIFIABLE", detail


def main():
    posts = json.load(open(os.path.join(DATA, "posts.json")))["posts"]
    rows, counts = [], {"PROMO": 0, "OTHER": 0, "CALL_CANDIDATE": 0}
    for p in posts:
        cls = classify(p.get("text", ""))
        counts[cls] = counts.get(cls, 0) + 1
        if cls != "CALL_CANDIDATE":
            continue
        info = extract(p["text"])
        for coin in info["coins"]:
            verdict, detail = verify(coin, p["datetime"], info["direction"],
                                     info["levels"])
            rows.append({"datetime": p["datetime"], "permalink": p.get("permalink"),
                         "coin": coin, "direction": info["direction"],
                         "levels": info["levels"], "verdict": verdict,
                         "detail": detail, "text": p["text"][:200],
                         "has_images": bool(p.get("images"))})
    correct = sum(r["verdict"] == "CORRECT" for r in rows)
    incorrect = sum(r["verdict"] == "INCORRECT" for r in rows)
    unver = sum(r["verdict"] == "UNVERIFIABLE" for r in rows)
    denom = correct + incorrect
    acc = (correct / denom * 100) if denom else 0.0
    report = {"generated": datetime.utcnow().isoformat(),
              "total_posts": len(posts), "post_classes": counts,
              "scored_calls": len(rows), "correct": correct,
              "incorrect": incorrect, "unverifiable": unver,
              "accuracy_pct": round(acc, 1), "horizon_days": HORIZON_DAYS,
              "move_threshold_pct": MOVE_THRESHOLD, "calls": rows}
    json.dump(report, open(os.path.join(DATA, "report.json"), "w"), indent=2)
    print(f"posts={len(posts)} classes={counts}")
    print(f"scored_calls={len(rows)} correct={correct} incorrect={incorrect} "
          f"unverifiable={unver}")
    print(f"ACCURACY = {acc:.1f}%  (CORRECT/(CORRECT+INCORRECT)), "
          f"horizon={HORIZON_DAYS}d, threshold={MOVE_THRESHOLD}%")


if __name__ == "__main__":
    main()
