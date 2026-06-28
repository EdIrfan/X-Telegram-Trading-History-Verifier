#!/usr/bin/env python3
"""
De-bias the alt-long verdict: re-grade her alt longs from her FIRST entry.

Problem: our chart setups are often her LATE re-entries (we hold LAB at $17 after
its pump). Her "x5 from first entry" winners' early entries are text-only (not
charted) -> missing -> alt longs look worse than reality.

Fix (survivorship-controlled): take the SAME alt coins we already graded, find each
coin's EARLIEST telegram mention = her first call, re-price on Binance, and grade
let-it-run from there: -50% catastrophic stop (captures the ->0/delisted losers),
activate trail at +20%, 25% trailing stop, 180-day window. 0.5% friction.

Run:  .venv/bin/python debias_alt_firstentry.py
"""
import json, os, re, datetime as dt
from prices import ohlcv_auto

HERE = os.path.dirname(__file__)
LARGECAPS = {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LTC", "TRX",
             "LINK", "AVAX", "DOT", "BCH"}
DAY = 86400_000
NOW = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
CAT_STOP, ACT, TRAIL, FRIC = -0.50, 0.20, 0.25, 0.005
WINDOW = 365 * DAY    # her moonshot pumps can come months later; give a full year

posts = json.load(open(os.path.join(HERE, "data", "telegram_rose.json")))["posts"]
graded = json.load(open(os.path.join(HERE, "data", "graded_rose.json")))["trades"]
calls = {c["id"]: c for c in
         json.load(open(os.path.join(HERE, "data", "tg_calls_extracted.json")))["calls"]}


def to_ms(s):
    try:
        return int(dt.datetime.fromisoformat((s or "")[:19]).replace(
            tzinfo=dt.timezone.utc).timestamp() * 1000)
    except Exception:
        return None


# unique alt-long coins we already graded (the controlled universe) + their binance_sym
alt = {}
for t in graded:
    if t["dir"] == "long" and t["coin"] not in LARGECAPS:
        alt.setdefault(t["coin"], t["sym"])

# earliest telegram mention (#COIN, case-insensitive) per alt coin = her first call
first = {}
for p in sorted(posts, key=lambda x: x["id"]):
    txt = p.get("text") or ""
    ms = to_ms(p.get("date"))
    if ms is None:
        continue
    for c in set(m.upper() for m in re.findall(r"#([A-Za-z][A-Za-z0-9]{1,14})", txt)):
        if c in alt and c not in first:
            first[c] = (p["id"], ms, " ".join(txt.split())[:70])


def letrun(sym, start_ms):
    rows, mkt = ohlcv_auto(sym, start_ms - DAY, min(start_ms + WINDOW, NOW) + DAY, "1h")
    rows = [(c[0], float(c[2]), float(c[3]), float(c[4])) for c in rows
            if c[0] >= start_ms]
    if not rows:
        return None
    entry = rows[0][3]            # first available close at/after first mention
    last = rows[-1][3]
    # two exit policies sharing the same trail (activate at +ACT, trail TRAIL off peak):
    #  cat  = with a -50% catastrophic stop (you'd bail a dying alt)
    #  hold = NO downside stop (her buy&hold/DCA style; rides to ~0 if it dies)
    def ride(use_cat):
        pk = entry; act = False; ex = last
        for ot, h, l, cl in rows:
            pk = max(pk, h)
            if not act and pk >= entry * (1 + ACT):
                act = True
            if act and l <= pk * (1 - TRAIL):
                ex = pk * (1 - TRAIL); break
            if (not act) and use_cat and l <= entry * (1 + CAT_STOP):
                ex = entry * (1 + CAT_STOP); break
        return ex / entry - 1 - FRIC
    mfe = max(h / entry - 1 for _, h, _, _ in rows)
    return entry, ride(True), ride(False), mfe


# late-entry (our graded) realized per coin, for comparison (Method C)
late = {}
for t in graded:
    if t["dir"] == "long" and t["coin"] not in LARGECAPS:
        late.setdefault(t["coin"], []).append(t["C_ret"])

rows_out = []
for coin, sym in sorted(alt.items()):
    if coin not in first:
        continue
    fid, fms, ftxt = first[coin]
    r = letrun(sym, fms)
    if r is None:
        continue
    entry, ret_cat, ret_hold, mfe = r
    lateavg = sum(late[coin]) / len(late[coin])
    rows_out.append({"coin": coin, "first_id": fid,
                     "first_date": dt.datetime.fromtimestamp(fms/1000, dt.timezone.utc).strftime("%Y-%m-%d"),
                     "ret_cat": round(ret_cat, 3), "ret_hold": round(ret_hold, 3),
                     "peak_mult": round(mfe + 1, 2), "late_C_avg": round(lateavg, 3),
                     "txt": ftxt})

rows_out.sort(key=lambda r: -r["peak_mult"])
print(f"{'coin':10}{'firstdate':11}{'peakX':>7}{'ret_cat':>8}{'ret_hold':>9}{'lateC':>8}   first-msg")
for r in rows_out:
    print(f"{r['coin']:10}{r['first_date']:11}{r['peak_mult']:>6.1f}x{r['ret_cat']*100:>+7.0f}%"
          f"{r['ret_hold']*100:>+8.0f}%{r['late_C_avg']*100:>+7.0f}%   {r['txt'][:42]}")

n = len(rows_out)
import statistics as st
cat = [r["ret_cat"] for r in rows_out]; hold = [r["ret_hold"] for r in rows_out]
print(f"\nALT coins re-graded from FIRST entry (365d window): n={n}")
print(f"  PEAK reached from first entry — >=1.5x: {sum(1 for r in rows_out if r['peak_mult']>=1.5)}"
      f"  >=2x: {sum(1 for r in rows_out if r['peak_mult']>=2)}"
      f"  >=3x: {sum(1 for r in rows_out if r['peak_mult']>=3)}"
      f"  >=5x: {sum(1 for r in rows_out if r['peak_mult']>=5)}")
print(f"  let-it-run w/ -50% stop : mean {st.mean(cat)*100:+.0f}%  median {st.median(cat)*100:+.0f}%  win {sum(1 for x in cat if x>0)/n*100:.0f}%")
print(f"  hold-through (no stop)  : mean {st.mean(hold)*100:+.0f}%  median {st.median(hold)*100:+.0f}%  win {sum(1 for x in hold if x>0)/n*100:.0f}%")
json.dump(rows_out, open(os.path.join(HERE, "data", "debias_alt.json"), "w"), indent=1)
print("-> data/debias_alt.json")
