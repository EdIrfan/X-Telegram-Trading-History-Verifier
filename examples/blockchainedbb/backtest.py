#!/usr/bin/env python3
"""
FUN BACKTEST: mirror @blockchainedbb's 45 forward calls (Jun-Oct 2025).

Rules (as specified by the user):
  - Start equity: $10,000
  - $100 MARGIN per trade, max 5x leverage  -> $500 notional position
  - Isolated margin: a >=20% adverse move (1/5x) LIQUIDATES the position (-$100)
  - Otherwise exit at the 7-day window close: pnl = $500 * signed price move
  - $300/week circuit breaker: once a calendar week's realized P&L <= -$300,
    skip all remaining trades that week
  - one $100 per call (no DCA / averaging into losers)
  - no fees/funding modelled (would shave a little off)
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, range_high_low

MARGIN, LEV = 100.0, 5.0
NOTIONAL = MARGIN * LEV
STOP_FRAC = 0.50               # force-close at -50% of margin (no liquidations)
STOP_PRICE = STOP_FRAC / LEV   # = 10% adverse price move at 5x
WEEK_STOP = -300.0

calls = json.load(open(os.path.join(os.path.dirname(__file__), "data", "graded_all.json")))["calls"]
calls.sort(key=lambda r: r["dt"])


def btc_uptrend(t):
    """Crude regime proxy: is BTC above its price ~10 days earlier?"""
    now = price_at("BTC", t)
    past = price_at("BTC", t - timedelta(days=10))
    return (now is not None and past is not None and now >= past)


FRICTION = 0.005   # 0.5% off every trade (fees/slippage/funding) — both directions

def run(regime_filter, verbose=False):
    equity, peak, maxdd = 10000.0, 10000.0, 0.0
    wk_pnl, rows = {}, []
    taken = stops = skipped = wins = regime_skip = 0
    for r in calls:
        dt, coin, d = r["dt"], r["coin"], r["dir"]
        start = datetime.fromisoformat(dt + ":00+00:00")
        wk = start.isocalendar()[:2]
        if wk_pnl.get(wk, 0.0) <= WEEK_STOP:
            skipped += 1
            rows.append((dt, coin, d, "— skipped (week -$300 hit)", 0.0, equity)); continue
        if regime_filter:
            up = btc_uptrend(start)
            if (d == "long" and not up) or (d == "short" and up):
                regime_skip += 1
                rows.append((dt, coin, d, "— skipped (regime: wrong-way)", 0.0, equity)); continue
        end = min(start + timedelta(days=7), datetime.now(timezone.utc))
        p0 = price_at(coin, start); lo, hi = range_high_low(coin, start, end); pend = price_at(coin, end)
        move = (pend - p0) / p0
        raw = move if d == "long" else -move
        adv = (p0 - lo) / p0 if d == "long" else (hi - p0) / p0
        stopped = adv >= STOP_PRICE           # hard stop at -50% margin (10% price)
        eff = -STOP_PRICE if stopped else raw
        net = eff - FRICTION                  # 0.5% friction haircut
        pnl = NOTIONAL * net
        if stopped:
            res = f"STOP -50% (adv -{adv*100:.0f}%) net{net*100:+.1f}%"; stops += 1
        else:
            res = f"{raw*100:+5.1f}% net{net*100:+5.1f}% -> {pnl:+6.0f}"
            if pnl > 0: wins += 1
        taken += 1; equity += pnl
        wk_pnl[wk] = wk_pnl.get(wk, 0.0) + pnl
        peak = max(peak, equity); maxdd = max(maxdd, (peak - equity) / peak * 100)
        rows.append((dt, coin, d, res, pnl, equity))
    if verbose:
        print(f"{'DATE':17}{'COIN':5}{'DIR':6}{'RESULT':34}{'P&L':>7}  {'EQUITY':>8}")
        for dt, coin, d, res, pnl, eq in rows:
            print(f"{dt:17}{coin:5}{d:6}{res:34}{pnl:>7.0f}  {eq:>8.0f}")
    return {"end": round(equity), "return_pct": round((equity/10000-1)*100, 1),
            "taken": taken, "wins": wins, "stops": stops,
            "weekly_skips": skipped, "regime_skips": regime_skip,
            "max_drawdown_pct": round(maxdd, 1), "peak": round(peak)}


def validate_prices():
    """Sanity-check Binance data for every trade: real prices, full candle
    coverage, valid OHLC, and flag any single-day move >35% (could be a glitch
    OR a real crash wick — we print so you can eyeball)."""
    from prices import ohlcv
    bad, big = [], []
    seen = set()
    for r in calls:
        coin, dt = r["coin"], r["dt"]
        if (coin, dt) in seen:
            continue
        seen.add((coin, dt))
        start = datetime.fromisoformat(dt + ":00+00:00")
        end = start + timedelta(days=7)
        cs = ohlcv(coin, start, end)
        if not cs:
            bad.append(f"{dt} {coin}: NO CANDLES"); continue
        days = (end - start).days
        if len(cs) < days - 1:
            bad.append(f"{dt} {coin}: only {len(cs)}/{days} candles (gap?)")
        for c in cs:
            o, h, l, cl = float(c[1]), float(c[2]), float(c[3]), float(c[4])
            if min(o, h, l, cl) <= 0 or not (l <= o <= h and l <= cl <= h):
                bad.append(f"{dt} {coin}: bad OHLC {o}/{h}/{l}/{cl}")
            if (h - l) / l > 0.35:
                big.append(f"{dt} {coin}: {(h-l)/l*100:.0f}% intraday range "
                           f"(low {l:g} high {h:g})")
    print(f">>> PRICE-INTEGRITY CHECK over {len(seen)} trade windows")
    print(f"    data errors (gaps/bad OHLC/None): {len(bad)}")
    for b in bad: print("     !", b)
    print(f"    >35% single-day ranges (real crash wicks, not glitches): {len(big)}")
    for b in big: print("     ~", b)
    print()


validate_prices()
print(">>> SCENARIO A: copy ALL her calls\n")
A = run(regime_filter=False, verbose=True)
print(f"\nA) copy-all:        ${A['end']:,}  ({A['return_pct']:+.1f}%)  "
      f"maxDD {A['max_drawdown_pct']}%  peak ${A['peak']:,}  "
      f"stops={A['stops']} wk-skips={A['weekly_skips']}")

B = run(regime_filter=True)
print(f"B) regime-filtered: ${B['end']:,}  ({B['return_pct']:+.1f}%)  "
      f"maxDD {B['max_drawdown_pct']}%  peak ${B['peak']:,}  "
      f"stops={B['stops']} regime-skips={B['regime_skips']}")

json.dump({"rules": {"start": 10000, "margin": MARGIN, "leverage": LEV,
                     "weekly_stop": WEEK_STOP, "stop_loss_pct_of_margin": STOP_FRAC*100,
                     "friction_pct": FRICTION*100},
           "copy_all": A, "regime_filtered": B},
          open(os.path.join(os.path.dirname(__file__), "data", "backtest.json"), "w"), indent=2)
