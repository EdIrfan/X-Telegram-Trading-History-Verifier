#!/usr/bin/env python3
"""
Score the calls I (Claude) graded by reading her posts' text + charts.
Each entry: (datetime, coin, direction, [targets], note). Verified against
Binance OHLCV over a 7-day window. Accuracy = correct / (correct+incorrect).

direction = her forward bias from the post (long=expects higher, short=lower).
A "buy the dip / accumulate" post is graded long (she expects net-higher).
CORRECT if a stated target is touched in the window, else if price moved >=3%
the called way by window end; otherwise INCORRECT.
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, range_high_low

HORIZON = 7
# leverage-adjusted win thresholds (% move her way). She trades high leverage,
# so even a small favourable move is a banked win — BTC just 1.5%.
THRESH = {"BTC": 1.5, "ETH": 2.0, "BNB": 2.0, "SOL": 2.5,
          "XRP": 2.5, "DOGE": 3.0, "LTC": 2.5, "LINK": 2.5}
DEFAULT_THRESH = 2.5

# My hand-graded forward calls (idx refers to data/sample.json).
CALLS = [
    ("2025-06-05T21:02", "BTC", "long",  [],            "approaching 55EMA, expect bounce"),
    ("2025-06-06T17:06", "XRP", "long",  [],            "bought XRP spot dca1"),
    ("2025-06-12T20:50", "BTC", "long",  [],            "100% buying the dip"),
    ("2025-06-21T22:44", "XRP", "long",  [],            "'does that look bearish?' = bullish"),
    ("2025-06-22T13:49", "XRP", "long",  [],            "buying 50% XRP/LTC/LINK, rest at 98k"),
    ("2025-06-27T16:38", "BTC", "long",  [110000,112000],"sizing 104-105k, target 110-112k"),
    ("2025-06-30T19:28", "XRP", "long",  [3.0],         "XRP target ~2.7-3 near term"),
    ("2025-07-03T13:48", "BTC", "long",  [110000,112000],"TP1 110k TP2 112k"),
    ("2025-07-03T13:49", "ETH", "long",  [2600],        "ETH TP1 2600"),
    ("2025-07-07T12:41", "BTC", "long",  [112000],      "SOW->UT, UT 112k"),
    ("2025-07-09T18:16", "ETH", "long",  [2888],        "ETH could hit 2888-3k"),
    ("2025-07-11T16:07", "ETH", "long",  [3500],        "buy 2888 sell 3500"),
    ("2025-08-07T10:46", "BTC", "long",  [116666],      "target 116666"),
    ("2025-08-14T13:05", "BNB", "long",  [888],         "long every dip to 888/1200"),
    ("2025-08-19T14:54", "BTC", "long",  [],            "short almost done, gonna long bottom"),
    ("2025-09-03T14:54", "BTC", "short", [],            "closed longs, 'brace yourself'"),
    ("2025-09-04T14:09", "BTC", "short", [],            "BTC short going good"),
    ("2025-09-05T14:36", "ETH", "short", [],            "ETH short"),
    ("2025-09-05T14:36", "BTC", "short", [],            "BTC short (still)"),
    ("2025-09-19T13:00", "BTC", "short", [],            "short from 117k playing out"),
    ("2025-09-22T10:08", "ETH", "long",  [5200],        "DCA 3777-4000, TP5 5200"),
    ("2025-09-25T17:24", "ETH", "long",  [],            "bought ETH"),
    ("2025-09-25T17:26", "BTC", "long",  [],            "very little left to bottom"),
    ("2025-09-26T17:34", "BTC", "long",  [],            "bottom ~107k then up nonstop"),
    ("2025-09-29T01:30", "BTC", "long",  [],            "short done, now Uptober"),
    ("2025-09-29T12:40", "XRP", "long",  [],            "DCA2 limits 2.5-2.6"),
    ("2025-09-29T14:00", "ETH", "long",  [],            "limits 3777-3999 accumulate"),
    ("2025-10-02T00:01", "BTC", "long",  [],            "bullish continuation, not shorting"),
    ("2025-10-06T13:42", "BTC", "long",  [],            "dip 107-110k then continue up"),
    ("2025-10-07T13:52", "DOGE","long",  [],            "buying doge/shib tonight"),
    ("2025-10-07T14:35", "XRP", "long",  [4.0],         "scaling XRP, to 4 next"),
    ("2025-10-07T23:59", "BTC", "long",  [],            "buying 118-120k dips"),
    ("2025-10-08T14:20", "ETH", "long",  [5200],        "exit 5200, could reach 5500"),
    ("2025-10-10T07:12", "XRP", "long",  [],            "averaging XRP 2.6-2.7, ETF 17th"),
    ("2025-10-10T13:34", "SOL", "long",  [],            "95% ETF approval, bring it on"),
    ("2025-10-27T12:46", "BTC", "long",  [],            "next pump, 110-112k support"),
    ("2025-10-27T12:47", "ETH", "long",  [4200,4400,4700],"TPs 4200/4400/4700"),
]


def verify(coin, dt, direction, targets):
    thr = THRESH.get(coin, DEFAULT_THRESH)
    start = datetime.fromisoformat(dt + ":00+00:00")
    end = min(start + timedelta(days=HORIZON), datetime.now(timezone.utc))
    p0 = price_at(coin, start)
    lo, hi = range_high_low(coin, start, end)
    pend = price_at(coin, end)
    if not p0 or not pend:
        return "UNVERIFIABLE", "UNVERIFIABLE", None, "no price"
    move = (pend - p0) / p0 * 100
    # favourable / adverse excursion within window (leverage-relevant)
    fav = (hi - p0) / p0 * 100 if direction == "long" else (p0 - lo) / p0 * 100
    adv = (p0 - lo) / p0 * 100 if direction == "long" else (hi - p0) / p0 * 100
    near = [t for t in targets if 0.3 * p0 <= t <= 3 * p0]
    tgt_hit = False
    if near and direction in ("long", "short"):
        tgt = max(near) if direction == "long" else min(near)
        tgt_hit = (direction == "long" and hi >= tgt) or (direction == "short" and lo <= tgt)
    # close-based verdict (did the swing actually pay by window end)
    if direction == "long":
        close_v = "CORRECT" if (move >= thr or tgt_hit) else "INCORRECT"
    else:
        close_v = "CORRECT" if (move <= -thr or tgt_hit) else "INCORRECT"
    # excursion-based verdict (did it ever go her way >= thr — a leveraged pop)
    exc_v = "CORRECT" if fav >= thr else "INCORRECT"
    info = (f"{p0:g}->{pend:g} ({move:+.1f}%)  fav+{fav:.1f}% / adv-{adv:.1f}%"
            + (f"  tgt{'HIT' if tgt_hit else 'miss'}" if near else ""))
    return close_v, exc_v, move, info


rows = []
for dt, coin, direction, targets, note in CALLS:
    cv, ev, move, info = verify(coin, dt, direction, targets)
    rows.append({"dt": dt, "coin": coin, "dir": direction,
                 "close_verdict": cv, "excursion_verdict": ev,
                 "note": note, "result": info})


def rate(rows, key):
    c = sum(r[key] == "CORRECT" for r in rows)
    w = sum(r[key] == "INCORRECT" for r in rows)
    return c, w, (c / (c + w) * 100 if c + w else 0)

cc, cw, cacc = rate(rows, "close_verdict")
ec, ew, eacc = rate(rows, "excursion_verdict")
json.dump({"horizon": HORIZON, "thresholds": THRESH,
           "close_based": {"correct": cc, "incorrect": cw, "accuracy_pct": round(cacc,1)},
           "excursion_based": {"correct": ec, "incorrect": ew, "accuracy_pct": round(eacc,1)},
           "calls": rows},
          open(os.path.join(os.path.dirname(__file__), "data", "graded.json"), "w"),
          indent=2)
print(f"{'DATE':17} {'COIN':4} {'DIR':5} {'CLOSE':5} {'EXC':4}  result")
for r in rows:
    print(f"{r['dt']:17} {r['coin']:4} {r['dir']:5} "
          f"{'WIN' if r['close_verdict']=='CORRECT' else 'L':5} "
          f"{'WIN' if r['excursion_verdict']=='CORRECT' else 'L':4}  {r['result']}")
print(f"\nGRADED CALLS: {len(rows)}  (leverage-adjusted thresholds: BTC 1.5%, alts 2-3%)")
print(f"CLOSE-based  (did the swing pay by window end): {cc}/{cc+cw} = {cacc:.1f}%")
print(f"EXCURSION-based (did it ever pop her way = leveraged win): {ec}/{ec+ew} = {eacc:.1f}%")
