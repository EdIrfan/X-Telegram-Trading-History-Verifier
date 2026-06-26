#!/usr/bin/env python3
"""Weekly P&L table, $100 vs $500 accounts, same laddered strategy (hourly path)."""
import json, os
from datetime import datetime, timedelta, timezone, date
from prices import price_at, ohlcv

LEV=5.0; FRICTION=0.005; INIT_SL=-0.08; HORIZON=7
TP=[(0.06,0.33)]
lvl=0.075
while lvl<=0.2100001: TP.append((round(lvl,4),0.066)); lvl+=0.015

old=json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_all.json")))["calls"]
new=json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_full.json")))["new_calls"]
calls=sorted([{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in old+new],key=lambda r:r["dt"])

def tret(coin,start,end,d):
    p0=price_at(coin,start,interval="1h"); cs=ohlcv(coin,start,end,interval="1h")
    if not p0 or not cs: return None
    t0=int(start.timestamp()*1000); cs=[c for c in cs if c[0]>=t0-3600_000]
    if not cs: return None
    frac=1.0; realized=0.0; sl=INIT_SL; pend=list(TP)
    for c in cs:
        hi,lo,cl=float(c[2]),float(c[3]),float(c[4])
        f_high=(hi-p0)/p0 if d=="long" else (p0-lo)/p0
        f_low=(lo-p0)/p0 if d=="long" else (p0-hi)/p0
        while pend and f_high>=pend[0][0]:
            l_,fr=pend.pop(0); fr=min(fr,frac); realized+=fr*l_; frac-=fr
            sl=-0.05 if l_==0.06 else sl+0.015
        if frac>1e-9 and f_low<=sl: realized+=frac*sl; frac=0.0; break
    if frac>1e-9:
        f_end=(cl-p0)/p0 if d=="long" else (p0-cl)/p0; realized+=frac*f_end
    return realized-FRICTION

# precompute per-call return once (same for both accounts)
rets={}
for r in calls:
    start=datetime.fromisoformat(r["dt"]+":00+00:00")
    end=min(start+timedelta(days=HORIZON),datetime.now(timezone.utc))
    rets[r["dt"]]=tret(r["coin"],start,end,r["dir"])

def weekly(margin,weekly_stop):
    notional=margin*LEV; wk_pnl={}; wk_n={}; wk={}
    for r in calls:
        start=datetime.fromisoformat(r["dt"]+":00+00:00"); k=start.isocalendar()[:2]
        if wk.get(k,0.0)<=weekly_stop: continue
        ret=rets[r["dt"]]
        if ret is None: continue
        pnl=notional*ret
        wk[k]=wk.get(k,0.0)+pnl; wk_pnl[k]=wk_pnl.get(k,0.0)+pnl; wk_n[k]=wk_n.get(k,0)+1
    return wk_pnl,wk_n

A_pnl,A_n=weekly(100,-300); B_pnl,B_n=weekly(500,-500)
weeks=sorted(set(A_pnl)|set(B_pnl))

def monday(iso):  # ISO (year,week)->Monday date
    return date.fromisocalendar(iso[0],iso[1],1).isoformat()

eqA=eqB=10000.0
rows=[]
print(f"{'Week (Mon)':12}{'#':>3} | {'$100 P&L':>9}{'$100 Eq':>9} | {'$500 P&L':>10}{'$500 Eq':>10}")
print("-"*64)
for k in weeks:
    a=A_pnl.get(k,0.0); b=B_pnl.get(k,0.0); n=max(A_n.get(k,0),B_n.get(k,0))
    eqA+=a; eqB+=b
    print(f"{monday(k):12}{n:>3} | {a:>+9.0f}{eqA:>9.0f} | {b:>+10.0f}{eqB:>10.0f}")
    rows.append({"week":monday(k),"trades":n,"p100":round(a),"eq100":round(eqA),
                 "p500":round(b),"eq500":round(eqB)})
print("-"*64)
print(f"{'TOTAL':12}{sum(max(A_n.get(k,0),B_n.get(k,0)) for k in weeks):>3} | "
      f"{eqA-10000:>+9.0f}{eqA:>9.0f} | {eqB-10000:>+10.0f}{eqB:>10.0f}")

# markdown table
md=["# Weekly P&L — $100 vs $500 accounts (laddered strategy)\n",
    "| Week (Mon) | Trades | $100 P&L | $100 Equity | $500 P&L | $500 Equity |",
    "|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['week']} | {r['trades']} | {r['p100']:+} | {r['eq100']:,} | {r['p500']:+} | {r['eq500']:,} |")
md.append(f"| **TOTAL** |  | **{round(eqA-10000):+}** | **{round(eqA):,}** | **{round(eqB-10000):+}** | **{round(eqB):,}** |")
open(os.path.join(os.path.dirname(__file__),"WEEKLY_PNL.md"),"w").write("\n".join(md)+"\n")
print("\n-> WEEKLY_PNL.md written")
