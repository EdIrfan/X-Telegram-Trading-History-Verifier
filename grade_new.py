#!/usr/bin/env python3
"""
Grade the Nov 2025–Mar 2026 forward calls (the crash period) and extend the
$10k backtest through them. Same rules as backtest.py.
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, range_high_low

HORIZON = 7
THRESH = {"BTC":1.5,"ETH":2.0,"BNB":2.0,"SOL":2.5,"XRP":2.5,"DOGE":3.0}
MARGIN, LEV = 100.0, 5.0; NOTIONAL = MARGIN*LEV
STOP_FRAC = 0.50; STOP_PRICE = STOP_FRAC/LEV; FRICTION = 0.005; WEEK_STOP = -300.0

# New forward calls graded from data/sample2.json (text + charts).
NEW = [
 ("2025-11-06T17:52","BTC","long", [115000,120000],"expect 115-120k first"),
 ("2025-11-07T13:15","BTC","long", [],            "scaling into long"),
 ("2025-11-10T13:57","BTC","short",[100000],      "short 107-109k -> 100k"),
 ("2025-11-11T15:41","BTC","long", [],            "accumulate long <103k"),
 ("2025-11-17T19:18","BTC","long", [],            "long with tight SL"),
 ("2025-11-21T14:28","BTC","short",[80000],       "shorting to 80-81k"),
 ("2025-11-28T14:37","BTC","short",[87000],       "short to 87k if 90-91k lost"),
 ("2025-12-15T14:21","BTC","short",[87000],       "weekly bearish, target 87k"),
 ("2026-02-10T13:16","BTC","short",[65000],       "below 68.5k -> 64-66k"),
 ("2026-02-13T16:14","ETH","short",[2222],        "TP1 2150-2222"),
 ("2026-02-18T13:26","BTC","short",[],            "shorting, below 200EMA"),
 ("2026-03-02T16:29","BTC","short",[],            "short after structure breaks"),
 ("2026-03-04T12:41","BTC","short",[],            "short below 68.3k"),
 ("2026-03-18T14:39","ETH","short",[],            "about to enter ETH short"),
 ("2026-03-19T16:20","BTC","short",[67500],       "short 69.5-69.9k -> 67.5k"),
 ("2026-03-22T21:23","BTC","short",[],            "short again Monday"),
 ("2026-03-23T13:35","BTC","short",[],            "second short this week"),
 ("2026-03-27T20:38","BTC","short",[62500],       "entry 67.5-68.3k exit 62.5k"),
]

def grade(coin, dt, d, tg):
    thr = THRESH.get(coin, 2.5)
    start = datetime.fromisoformat(dt+":00+00:00")
    end = min(start+timedelta(days=HORIZON), datetime.now(timezone.utc))
    p0 = price_at(coin, start); lo, hi = range_high_low(coin, start, end); pend = price_at(coin, end)
    if not p0 or not pend: return None
    move = (pend-p0)/p0
    fav = (hi-p0)/p0*100 if d=="long" else (p0-lo)/p0*100
    adv = (p0-lo)/p0*100 if d=="long" else (hi-p0)/p0*100
    near = [t for t in tg if 0.3*p0<=t<=3*p0]
    th = False
    if near:
        t = max(near) if d=="long" else min(near)
        th = (d=="long" and hi>=t) or (d=="short" and lo<=t)
    sm = move*100 if d=="long" else -move*100
    close = "CORRECT" if (sm>=thr or th) else "INCORRECT"
    exc = "CORRECT" if fav>=thr else "INCORRECT"
    return {"dt":dt,"coin":coin,"dir":d,"close":close,"exc":exc,
            "fav":round(fav,1),"adv":round(adv,1)}

new_rows = [grade(c, dt, d, tg) for dt, c, d, tg, _ in NEW]
new_rows = [r for r in new_rows if r]

print("=== NEW forward calls Nov2025-Mar2026 (the crash) ===")
print(f"{'DT':17}{'COIN':5}{'DIR':6}{'CLOSE':9}{'EXC':9} fav/adv")
for r in new_rows:
    print(f"{r['dt']:17}{r['coin']:5}{r['dir']:6}{r['close']:9}{r['exc']:9} +{r['fav']}/-{r['adv']}")
nc = sum(r["close"]=="CORRECT" for r in new_rows); nw = sum(r["close"]=="INCORRECT" for r in new_rows)
print(f"\nNEW calls close-based: {nc}/{nc+nw} = {nc/(nc+nw)*100:.0f}%")
shorts = [r for r in new_rows if r["dir"]=="short"]
sc = sum(r["close"]=="CORRECT" for r in shorts)
print(f"  of which SHORTS: {sc}/{len(shorts)} = {sc/len(shorts)*100:.0f}% correct")

# Merge with old 45 and run the full backtest Jun2025 -> Mar2026
old = json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_all.json")))["calls"]
allc = [{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in old] + \
       [{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in new_rows]
allc.sort(key=lambda r:r["dt"])

equity=peak=10000.0; maxdd=0.0; wk={}; taken=stops=wins=skip=0
for r in allc:
    start=datetime.fromisoformat(r["dt"]+":00+00:00"); k=start.isocalendar()[:2]
    if wk.get(k,0)<=WEEK_STOP: skip+=1; continue
    end=min(start+timedelta(days=HORIZON),datetime.now(timezone.utc))
    p0=price_at(r["coin"],start); lo,hi=range_high_low(r["coin"],start,end); pend=price_at(r["coin"],end)
    if not p0 or not pend: continue
    move=(pend-p0)/p0; raw=move if r["dir"]=="long" else -move
    adv=(p0-lo)/p0 if r["dir"]=="long" else (hi-p0)/p0
    stopped=adv>=STOP_PRICE
    net=(-STOP_PRICE if stopped else raw)-FRICTION
    pnl=NOTIONAL*net; taken+=1
    if stopped: stops+=1
    elif pnl>0: wins+=1
    equity+=pnl; wk[k]=wk.get(k,0)+pnl
    peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak*100)
print("\n=== FULL BACKTEST  Jun 2025 -> Mar 2026 (63 calls) ===")
print(f"START $10,000 -> END ${equity:,.0f}  ({(equity/10000-1)*100:+.1f}%)")
print(f"trades={taken} wins={wins} stops={stops} wk-skips={skip}  maxDD {maxdd:.1f}%  peak ${peak:,.0f}")
json.dump({"new_calls":new_rows,"full_backtest":{"end":round(equity),
           "return_pct":round((equity/10000-1)*100,1),"taken":taken,"wins":wins,
           "stops":stops,"max_drawdown_pct":round(maxdd,1),"peak":round(peak)}},
          open(os.path.join(os.path.dirname(__file__),"data","graded_full.json"),"w"),indent=2)
