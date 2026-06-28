#!/usr/bin/env python3
"""
Historical crypto price lookups that match what TradingView shows.

TradingView has no free public historical API, but its default crypto charts
are fed by exchange data. We use Binance public klines (the same source behind
most "BINANCE:BTCUSDT" TradingView charts), so prices line up with the charts.

    from prices import ohlcv, price_at, range_high_low
    price_at("BTC", "2025-06-15T12:00:00Z")        # closest daily close
    range_high_low("SOL", "2025-06-01", "2025-07-01")
"""
import datetime as dt
import json
import os
import requests

BINANCE = "https://api.binance.com/api/v3/klines"          # spot
FAPI = "https://fapi.binance.com/fapi/v1/klines"           # USDT-M futures
# cache under <repo>/data/price_cache (this file lives in <repo>/scripts/)
_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "price_cache")
_MEM = {}
_MARKET = {}   # pair -> "spot"/"futures" that returned data (memoized)


def _cache_get(key):
    if key in _MEM:
        return _MEM[key]
    fp = os.path.join(_CACHE_DIR, key + ".json")
    if os.path.exists(fp):
        try:
            v = json.load(open(fp))
            _MEM[key] = v
            return v
        except Exception:
            return None
    return None


def _cache_put(key, val):
    _MEM[key] = val
    os.makedirs(_CACHE_DIR, exist_ok=True)
    try:
        json.dump(val, open(os.path.join(_CACHE_DIR, key + ".json"), "w"))
    except Exception:
        pass


def _to_ms(when) -> int:
    if isinstance(when, (int, float)):
        return int(when)
    if isinstance(when, str):
        when = when.replace("Z", "+00:00")
        d = dt.datetime.fromisoformat(when)
    else:
        d = when
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * 1000)


def ohlcv(symbol: str, start, end, interval: str = "1d", market: str = "spot"):
    """Return list of [openTime, open, high, low, close, volume, ...] candles.

    market="spot" hits api.binance.com; market="futures" hits fapi (USDT-M perp).
    """
    pair = symbol.upper()
    if not pair.endswith("USDT"):
        pair = pair + "USDT"
    base = BINANCE if market == "spot" else FAPI
    s_ms, e_ms = _to_ms(start), _to_ms(end)
    ckey = f"{pair}_{interval}_{s_ms}_{e_ms}" + ("" if market == "spot" else "_fut")
    cached = _cache_get(ckey)
    if cached is not None:
        return cached
    out, cur, end_ms = [], s_ms, e_ms
    while cur < end_ms:
        r = requests.get(base, params={
            "symbol": pair, "interval": interval,
            "startTime": cur, "endTime": end_ms, "limit": 1000,
        }, timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out.extend(batch)
        cur = batch[-1][0] + 1
        if len(batch) < 1000:
            break
    # only cache fully-elapsed windows (don't cache the still-forming present)
    if e_ms < (_to_ms(dt.datetime.now(dt.timezone.utc)) - 2 * 86400_000):
        _cache_put(ckey, out)
    return out


def ohlcv_auto(symbol: str, start, end, interval: str = "1d"):
    """ohlcv that tries SPOT then FUTURES. Returns (candles, market_used|None).

    For perp-only symbols (CLUSDT oil, delisted alts) spot 400s -> fall back to
    fapi. Remembers which market worked per pair so we don't re-probe spot."""
    pair = symbol.upper()
    if not pair.endswith("USDT"):
        pair = pair + "USDT"
    order = [_MARKET[pair]] if pair in _MARKET else ["spot", "futures"]
    for mkt in order:
        try:
            data = ohlcv(symbol, start, end, interval, market=mkt)
        except Exception:
            data = []
        if data:
            _MARKET[pair] = mkt
            return data, mkt
    return [], None


def price_at(symbol: str, when, interval: str = "1d"):
    """Close price of the candle containing `when`."""
    t = _to_ms(when)
    candles = ohlcv(symbol, t - 86400_000, t + 86400_000, interval)
    best = min(candles, key=lambda c: abs(c[0] - t), default=None)
    return float(best[4]) if best else None


def range_high_low(symbol: str, start, end, interval: str = "1d"):
    """(min_low, max_high) over the window — for checking if a target was hit."""
    candles = ohlcv(symbol, start, end, interval)
    if not candles:
        return None, None
    return (min(float(c[3]) for c in candles),
            max(float(c[2]) for c in candles))


if __name__ == "__main__":
    print("BTC close ~2025-06-15:", price_at("BTC", "2025-06-15T12:00:00Z"))
    print("SOL range Jun-2025:", range_high_low("SOL", "2025-06-01", "2025-07-01"))
