#!/usr/bin/env python3
"""
PRECISE re-check of the backtest using HOURLY candles anchored at the exact post
time — so the stop-loss (-50% margin = 10% adverse price move at 5x) is tested
against intraday wicks that occurred AFTER entry, not daily approximations.

Compares daily vs hourly so we can see if any wick stop-outs were missed/extra.
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, ohlcv

MARGIN, LEV = 100.0, 5.0; NOTIONAL = MARGIN*LEV
STOP_FRAC = 0.50; STOP_PRICE = STOP_FRAC/LEV; FRICTION = 0.005; WEEK_STOP = -300.0
HORIZON = 7

old = json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_all.json")))["calls"]
new = json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_full.json")))["new_calls"]
calls = sorted([{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in old+new],
               key=lambda r:r["dt"])


def hourly_path(coin, start, end, d):
    """Entry at the 1h candle of the post time; adverse/favorable from the
    hourly highs/lows AFTER entry (true intraday wick check)."""
    p0 = price_at(coin, start, interval="1h")
    cs = ohlcv(coin, start, end, interval="1h")
    if not p0 or not cs:
        return None
    # only candles at/after the post hour
    t0 = int(start.timestamp()*1000)
    cs = [c for c in cs if c[0] >= t0 - 3600_000]
    if not cs:
        return None
    lo = min(float(c[3]) for c in cs); hi = max(float(c[2]) for c in cs)
    pend = float(cs[-1][4])
    adv = (p0-lo)/p0 if d=="long" else (hi-p0)/p0
    move = (pend-p0)/p0
    return p0, adv, move


def run(interval):
    equity=peak=10000.0; maxdd=0.0; wk={}; taken=stops=wins=skip=0; details=[]
    for r in calls:
        start=datetime.fromisoformat(r["dt"]+":00+00:00"); k=start.isocalendar()[:2]
        if wk.get(k,0)<=WEEK_STOP: skip+=1; continue
        end=min(start+timedelta(days=HORIZON), datetime.now(timezone.utc))
        if interval=="1h":
            res=hourly_path(r["coin"], start, end, r["dir"])
            if not res: continue
            p0, adv, move = res
        else:
            from prices import range_high_low
            p0=price_at(r["coin"],start); lo,hi=range_high_low(r["coin"],start,end)
            pend=price_at(r["coin"],end)
            if not p0 or not pend: continue
            adv=(p0-lo)/p0 if r["dir"]=="long" else (hi-p0)/p0
            move=(pend-p0)/p0
        raw = move if r["dir"]=="long" else -move
        stopped = adv >= STOP_PRICE
        net=(-STOP_PRICE if stopped else raw)-FRICTION
        pnl=NOTIONAL*net; taken+=1
        if stopped: stops+=1; details.append((r["dt"],r["coin"],r["dir"],f"STOP adv-{adv*100:.0f}%"))
        elif pnl>0: wins+=1
        equity+=pnl; wk[k]=wk.get(k,0)+pnl
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak*100)
    return {"end":round(equity),"ret":round((equity/10000-1)*100,1),"taken":taken,
            "wins":wins,"stops":stops,"maxdd":round(maxdd,1),"peak":round(peak),
            "stop_detail":details}

print("Re-running 73 calls at DAILY vs HOURLY resolution...\n")
D=run("1d"); H=run("1h")
print(f"{'':10}{'END':>9}{'RET':>8}{'maxDD':>8}{'stops':>7}{'wins':>6}{'taken':>7}")
print(f"{'DAILY':10}${D['end']:>8,}{D['ret']:>7}%{D['maxdd']:>7}%{D['stops']:>7}{D['wins']:>6}{D['taken']:>7}")
print(f"{'HOURLY':10}${H['end']:>8,}{H['ret']:>7}%{H['maxdd']:>7}%{H['stops']:>7}{H['wins']:>6}{H['taken']:>7}")
print(f"\nHourly stop-outs (wicks that hit the -50% SL):")
for d in H["stop_detail"]:
    print("  ", *d)
print(f"\nverdict: daily stops={D['stops']}  hourly stops={H['stops']}  "
      f"-> {'SAME risk picture' if abs(D['stops']-H['stops'])<=1 else 'DIFFERENT - hourly is the truth'}")
