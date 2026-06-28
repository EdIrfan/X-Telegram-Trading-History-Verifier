#!/usr/bin/env python3
"""
$10,000 backtest of Rose Margin's calls, per docs/backtest_rules.md + findings.

SIZING = RISK-PARITY (bound the $ loss to her wide SLs by shrinking size):
  notional N = risk_budget R / her_SL_distance%   (so hitting her SL loses ~R)
  PnL = N * graded_return   (graded_return already nets 0.5% friction)
  Leverage (3x core / 1x moonshot-alt) only sets margin = N/lev & liquidation,
  NOT PnL -> reported as a deployment diagnostic, not a return knob.

RISK BUDGET R per trade:
  PLAN A "$100" : R=$100 normal / $200 swing ; weekly stop -$300 (3% of 10k)
  PLAN B "$200c5": R=$200 normal / $400 swing ; weekly stop -$500 (5% of 10k)
  2x ("swing") applies ONLY to swing setups on BTC + LARGECAPS. Alts always 1x.

STRATEGY = SEGMENTED (our finding: alpha is in the exit, alt longs need let-it-run):
  shorts & largecap longs -> Method A (mirror her posts)
  alt (non-largecap) longs -> Method C (let it run: wide stop then trail)
Baselines for comparison: ALL-A (mirror-her everything), ALL-B (mechanical).

Run:  .venv/bin/python backtest_rose.py
"""
import json, os, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(__file__)
G = json.load(open(os.path.join(HERE, "data", "graded_rose.json")))["trades"]
CALLS = {c["id"]: c for c in
         json.load(open(os.path.join(HERE, "data", "tg_calls_extracted.json")))["calls"]}

LARGECAPS = {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LTC", "TRX",
             "LINK", "AVAX", "DOT", "BCH"}
SL_FLOOR = 0.03            # don't size insanely off ultra-tight SLs
DEF_SL = {"large": 0.10, "alt": 0.30}   # assumed SL for no-SL (moonshot/zone) sizing
START = 10000.0
HOUR = 3600_000


def to_ms(s):
    s = (s or "")[:16]
    try:
        d = dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
        return int(d.timestamp() * 1000)
    except Exception:
        return None


# ---------- enrich each graded trade with sizing inputs ----------
trades = []
for t in G:
    pm = to_ms(t["post_date"])
    if pm is None:
        continue
    coin = t["coin"]; d = t["dir"]
    is_large = coin in LARGECAPS
    seg = "short" if d == "short" else ("large_long" if is_large else "alt_long")
    method = "C" if seg == "alt_long" else "A"     # segmented strategy
    sl = CALLS.get(t["id"], {}).get("sl")
    entry = t["entry"]
    if sl:
        sl_dist = max(abs(entry - sl) / entry, SL_FLOOR)
    else:
        sl_dist = DEF_SL["large" if is_large else "alt"]
    hold = t.get(f"{method}_hold_h", 0) or 0
    exit_ms = pm + int((t.get("fill_h_after", 0) + hold) * HOUR)
    trades.append({
        "id": t["id"], "coin": coin, "dir": d, "seg": seg, "method": method,
        "swing2x": bool(t.get("swing")) and is_large, "sl_dist": sl_dist,
        "lev": 1 if seg == "alt_long" else 3,
        "ret_seg": t[f"{method}_ret"], "ret_A": t["A_ret"], "ret_B": t["B_ret"],
        "entry_ms": pm, "exit_ms": exit_ms,
    })
trades.sort(key=lambda x: x["entry_ms"])


def isown(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).isocalendar()[:2]


def run(R_norm, R_swing, wk_stop, ret_key, include_alt=True):
    """Event-driven & FUNDABLE: reserve margin at entry (skip if can't fund or
    weekly-stopped), free + realize PnL at exit, stop at ruin (equity<=0).
    include_alt=False -> trade only shorts + largecap longs (the fairly-gradeable core)."""
    OPEN, CLOSE = 1, 0  # process closes before opens at same ts (free margin first)
    ev = []
    for i, t in enumerate(trades):
        ev.append((t["entry_ms"], OPEN, i))
        ev.append((max(t["exit_ms"], t["entry_ms"] + HOUR), CLOSE, i))
    ev.sort(key=lambda e: (e[0], e[1]))
    eq = peak = START; maxdd = 0.0; deployed = 0.0; pkmar = 0.0
    wkreal = defaultdict(float); opened = {}
    taken = wins = wkskip = unfund = 0; blown = False
    for ts, typ, i in ev:
        t = trades[i]
        if typ == OPEN:
            if blown or (not include_alt and t["seg"] == "alt_long"):
                continue
            if wkreal[isown(ts)] <= -wk_stop:
                wkskip += 1; continue
            R = R_swing if t["swing2x"] else R_norm
            N = R / t["sl_dist"]; margin = N / t["lev"]
            if deployed + margin > eq:        # can't fund -> realistic concurrency cap
                unfund += 1; continue
            deployed += margin; pkmar = max(pkmar, deployed)
            opened[i] = (N, margin)
        else:
            if i not in opened:
                continue
            N, margin = opened.pop(i)
            deployed -= margin
            pnl = N * t[ret_key]
            eq += pnl; taken += 1; wins += pnl > 0
            wkreal[isown(ts)] += pnl
            peak = max(peak, eq); maxdd = max(maxdd, (peak - eq) / peak * 100)
            if eq <= 0:
                blown = True; eq = 0.0
    return {"end": round(eq), "ret_%": round((eq / START - 1) * 100, 1),
            "maxDD_%": round(maxdd, 1), "taken": taken, "win_%":
            round(wins / taken * 100) if taken else 0, "wk_skip": wkskip,
            "unfunded": unfund, "blown": blown, "peak_margin": round(pkmar)}


PLANS = [("A $100  (R100/200, wk-300)", 100, 200, 300),
         ("B $200c5 (R200/400, wk-500)", 200, 400, 500)]

print(f"{'plan':30} {'strategy':10} {'end$':>8} {'ret%':>7} {'maxDD':>6} "
      f"{'trades':>7} {'win%':>5} {'wkskip':>6} {'unfund':>6} {'pkMargin':>9} blown")
results = {}
for pname, Rn, Rs, ws in PLANS:
    for label, key, ialt in [("SEGMENTED", "ret_seg", True), ("CORE-only", "ret_seg", False),
                             ("all-A", "ret_A", True), ("all-B", "ret_B", True)]:
        r = run(Rn, Rs, ws, key, include_alt=ialt)
        results[f"{pname} | {label}"] = r
        print(f"{pname:30} {label:10} {r['end']:>8,} {r['ret_%']:>+7} {r['maxDD_%']:>5}% "
              f"{r['taken']:>7} {r['win_%']:>4}% {r['wk_skip']:>6} {r['unfunded']:>6} "
              f"${r['peak_margin']:>8,} {'BLOWN' if r['blown'] else ''}")

# reference: FLAT $1,000 notional/trade (no risk-parity, no caps) -> the RAW edge,
# to separate signal quality from the sizing-amplification effect.
print("\nReference — FLAT $1,000 notional/trade, no risk-parity, no weekly stop:")
for label, key in [("segmented", "ret_seg"), ("all-A (mirror her)", "ret_A"),
                   ("all-B (mechanical)", "ret_B")]:
    s = sum(1000 * t[key] for t in trades)
    print(f"  {label:20} sum PnL ${round(s):>+7,}  ({round(s/START*100):+}% of $10k)")

# segment contribution (Plan A, segmented) — where does PnL come from?
print("\nSegment PnL contribution (Plan A risk, segmented exits):")
seg_pnl = defaultdict(lambda: [0.0, 0])
for t in trades:
    R = 200 if t["swing2x"] else 100
    seg_pnl[t["seg"]][0] += (R / t["sl_dist"]) * t["ret_seg"]
    seg_pnl[t["seg"]][1] += 1
for s, (p, n) in sorted(seg_pnl.items(), key=lambda x: x[1][0]):
    print(f"  {s:11} n={n:3}  PnL ${round(p):>+7,}")

json.dump({"results": results,
           "note": "risk-parity sizing; PnL=N*graded_ret; see docs/backtest_rules.md"},
          open(os.path.join(HERE, "data", "backtest_rose.json"), "w"), indent=1)
print("\n-> data/backtest_rose.json")
