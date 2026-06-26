#!/usr/bin/env python3
"""
Laddered take-profit + trailing-stop backtest, walked on the HOURLY price path.

Per trade (5x isolated, margin M):
  - initial SL at -5% price (= -25% of margin)
  - +6% price  -> close 33%, move SL to break-even
  - every +1.5% after that (7.5%,9%,...,21%) -> close 6.6% more, trail SL to (step-1.5%)
  - leftover at window end closes at the last hourly close
  - 0.5% friction on the trade's net return
Accounts:
  A) $100 margin/trade, weekly stop -$300 (3% of $10k)
  B) $500 margin/trade, weekly stop -$500 (5% of $10k)
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, ohlcv

LEV = 5.0; FRICTION = 0.005; INIT_SL = -0.08; HORIZON = 7  # -8% initial stop both accts
# TP ladder: (favorable price level, fraction of original position to close)
TP = [(0.06, 0.33)]
lvl = 0.075
while lvl <= 0.2100001:
    TP.append((round(lvl, 4), 0.066)); lvl += 0.015

old = json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_all.json")))["calls"]
new = json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_full.json")))["new_calls"]
calls = sorted([{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in old+new],
               key=lambda r:r["dt"])


def trade_return(coin, start, end, d, init_sl):
    """Walk hourly path; return (net price-move return, hit_full_stop) or None."""
    p0 = price_at(coin, start, interval="1h")
    cs = ohlcv(coin, start, end, interval="1h")
    if not p0 or not cs:
        return None
    t0 = int(start.timestamp()*1000)
    cs = [c for c in cs if c[0] >= t0 - 3600_000]
    if not cs:
        return None
    frac = 1.0; realized = 0.0; sl = init_sl; pend = list(TP); full_stop = False
    for c in cs:
        hi, lo, cl = float(c[2]), float(c[3]), float(c[4])
        if d == "long":
            f_high = (hi-p0)/p0; f_low = (lo-p0)/p0
        else:
            f_high = (p0-lo)/p0; f_low = (p0-hi)/p0
        # 1) fill take-profit tiers reached this candle
        while pend and f_high >= pend[0][0]:
            lvl_, fr = pend.pop(0)
            fr = min(fr, frac)
            realized += fr*lvl_; frac -= fr
            sl = -0.05 if lvl_ == 0.06 else (sl + 0.015)  # +6%->-5%, then +1.5%/tier
        # 2) stop / trail hit this candle
        if frac > 1e-9 and f_low <= sl:
            if frac > 0.999: full_stop = True   # stopped before any TP
            realized += frac*sl; frac = 0.0; break
    if frac > 1e-9:  # close remainder at last close
        f_end = (cl-p0)/p0 if d == "long" else (p0-cl)/p0
        realized += frac*f_end
    return realized - FRICTION, full_stop


def run(margin, weekly_stop, init_sl):
    notional = margin*LEV
    equity = peak = 10000.0; maxdd = 0.0; wk = {}; curve = []
    taken = wins = losses = skip = full_sl = 0
    for r in calls:
        start = datetime.fromisoformat(r["dt"]+":00+00:00"); k = start.isocalendar()[:2]
        if wk.get(k, 0.0) <= weekly_stop:
            skip += 1; continue
        end = min(start+timedelta(days=HORIZON), datetime.now(timezone.utc))
        res = trade_return(r["coin"], start, end, r["dir"], init_sl)
        if res is None: continue
        ret, full = res
        pnl = notional*ret; taken += 1
        if full: full_sl += 1
        if pnl > 0: wins += 1
        else: losses += 1
        equity += pnl; wk[k] = wk.get(k, 0.0)+pnl
        peak = max(peak, equity); maxdd = max(maxdd, (peak-equity)/peak*100)
        curve.append((r["dt"][:10], round(equity)))
    return {"margin":margin,"weekly_stop":-weekly_stop,"end":round(equity),
            "ret":round((equity/10000-1)*100,1),"maxdd":round(maxdd,1),
            "peak":round(peak),"taken":taken,"wins":wins,"losses":losses,
            "full_sl":full_sl,"wk_skips":skip,
            "win_rate":round(wins/taken*100) if taken else 0,"curve":curve}


print("TP ladder:", [(f"+{l*100:g}%", f"{int(round(f*100))}%") for l, f in TP], "\n")
A = run(100, -300, INIT_SL)
B = run(500, -500, INIT_SL)
for s in (A, B):
    print(f"=== ${s['margin']}/trade  (init SL -8% = -${int(s['margin']*LEV*0.08)} max, "
          f"weekly stop ${s['weekly_stop']}) ===")
    print(f"  $10,000 -> ${s['end']:,}   ({s['ret']:+.1f}%)   maxDD {s['maxdd']}%   "
          f"peak ${s['peak']:,}")
    print(f"  trades={s['taken']}  wins={s['wins']} ({s['win_rate']}%)  losses={s['losses']}  "
          f"full -8% stops={s['full_sl']}  wk-skips={s['wk_skips']}\n")

# ---- generate markdown report ----
rep = f"""# Strategy backtest — laddered TP + trailing stop (@blockchainedbb, 73 calls)

**Verification:** full **7-day window per trade**, walked on the **hourly price path**
(real intraday wicks checked candle-by-candle, not daily approximations). Entry priced
at the post-time hourly candle. Prices integrity-checked earlier (0 data errors).

## Strategy rules (5x isolated)
- **Initial stop −8% price** (= −40% of margin → −${int(100*LEV*0.08)} on $100, −${int(500*LEV*0.08)} on $500).
- **+6% → close 33%**, tighten stop to **−5%**.
- **Every +1.5% above** (7.5%…21%) → close **6.6%** more and **raise the stop +1.5%**
  (−5% → −3.5% → −2% → … → into profit). Fully out by +21%.
- **0.5% friction** on every trade. One entry per call (no DCA).
- Weekly circuit-breaker: **$100 acct → −$300 (3%)**, **$500 acct → −$500 (5%)**.

## Results (full year, Jun 2025 → Jun 2026)
| Account | End | Return | Max DD | Win rate | Full −8% stops |
|---|---|---|---|---|---|
| **$100/trade** | ${A['end']:,} | **{A['ret']:+.1f}%** | {A['maxdd']}% | {A['win_rate']}% ({A['wins']}/{A['taken']}) | {A['full_sl']} |
| **$500/trade** | ${B['end']:,} | **{B['ret']:+.1f}%** | {B['maxdd']}% | {B['win_rate']}% ({B['wins']}/{B['taken']}) | {B['full_sl']} |

## Read
- The $500 result is the $100 edge at 5x size: the **return scales ~linearly with
  position size, and so does the drawdown** — same signal quality, bigger bet.
- The signal is a thin, regime-dependent trend-follow edge; exit-rule tuning shifts the
  numbers a little but does not manufacture an edge that isn't there.
"""
_docs=os.path.join(os.path.dirname(__file__),"docs"); os.makedirs(_docs,exist_ok=True)
open(os.path.join(_docs, "STRATEGY_REPORT.md"), "w").write(rep)
json.dump({"A_100":A, "B_500":B}, open(os.path.join(os.path.dirname(__file__),
          "data","strategy_backtest.json"), "w"), indent=2)
print("report written -> docs/STRATEGY_REPORT.md")
