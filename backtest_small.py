#!/usr/bin/env python3
"""
Re-analysis for a $1,000 account at $10 and $50/trade — modelling EXCHANGE ORDER
MINIMUMS, which break the laddered exit at small size (the non-linear effect).

Min order (Binance USDⓈ-M, representative): max($5, 0.001 BTC for BTC). The ladder
closes 11 pieces; any piece below the minimum can't be placed, so small accounts
exit coarsely (or can't open BTC at all) -> NOT a clean /10 of the big account.
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, ohlcv

LEV=5.0; FRICTION=0.005; INIT_SL=-0.08; HORIZON=7
TP=[(0.06,0.33)]
lvl=0.075
while lvl<=0.2100001: TP.append((round(lvl,4),0.066)); lvl+=0.015
MIN_QTY={"BTC":0.001,"ETH":0.001}   # binding lot size on Binance USDT-M perps

def min_order(coin, price):
    return max(5.0, MIN_QTY.get(coin,0.0)*price)

old=json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_all.json")))["calls"]
new=json.load(open(os.path.join(os.path.dirname(__file__),"data","graded_full.json")))["new_calls"]
calls=sorted([{"dt":r["dt"],"coin":r["coin"],"dir":r["dir"]} for r in old+new],key=lambda r:r["dt"])

def trade(coin,start,end,d,notional,enforce_min):
    p0=price_at(coin,start,interval="1h"); cs=ohlcv(coin,start,end,interval="1h")
    if not p0 or not cs: return None
    t0=int(start.timestamp()*1000); cs=[c for c in cs if c[0]>=t0-3600_000]
    if not cs: return None
    mo=min_order(coin,p0) if enforce_min else 0.0
    if notional<mo: return ("CANT_OPEN",0.0,False)   # position itself too small
    frac=1.0; realized=0.0; sl=INIT_SL; pend=list(TP); laddered=0
    for c in cs:
        hi,lo,cl=float(c[2]),float(c[3]),float(c[4])
        f_high=(hi-p0)/p0 if d=="long" else (p0-lo)/p0
        f_low=(lo-p0)/p0 if d=="long" else (p0-hi)/p0
        while pend and f_high>=pend[0][0]:
            l_,fr=pend.pop(0); fr=min(fr,frac)
            sl=-0.05 if l_==0.06 else sl+0.015          # trail the stop regardless
            if fr*notional>=mo:                          # only close if order clears min
                realized+=fr*l_; frac-=fr; laddered+=1
            # else: can't place that partial -> it stays in the position (rides)
        if frac>1e-9 and f_low<=sl: realized+=frac*sl; frac=0.0; break
    if frac>1e-9:
        f_end=(cl-p0)/p0 if d=="long" else (p0-cl)/p0; realized+=frac*f_end
    return ("OK", realized-FRICTION, laddered)

def run(start_cap, margin, weekly_stop, enforce_min):
    notional=margin*LEV; equity=peak=float(start_cap); maxdd=0.0; wk={}
    taken=wins=skip_open=skip_wk=coarse=0
    for r in calls:
        s=datetime.fromisoformat(r["dt"]+":00+00:00"); k=s.isocalendar()[:2]
        if wk.get(k,0.0)<=weekly_stop: skip_wk+=1; continue
        end=min(s+timedelta(days=HORIZON),datetime.now(timezone.utc))
        res=trade(r["coin"],s,end,r["dir"],notional,enforce_min)
        if res is None: continue
        status,ret,lad=res
        if status=="CANT_OPEN": skip_open+=1; continue
        if r["coin"]=="BTC" and lad<len(TP): coarse+=1   # ladder couldn't fully run
        pnl=notional*ret; taken+=1
        if pnl>0: wins+=1
        equity+=pnl; wk[k]=wk.get(k,0.0)+pnl
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak*100)
    return {"start":start_cap,"margin":margin,"end":round(equity,2),
            "ret":round((equity/start_cap-1)*100,1),"maxdd":round(maxdd,1),
            "taken":taken,"wins":wins,"cant_open":skip_open,"coarse_exits":coarse}

print("Min order sizes at sample prices: BTC@70k -> ${:.0f}, BTC@110k -> ${:.0f}\n"
      .format(0.001*70000, 0.001*110000))
configs=[(1000,10,-30),(1000,50,-50)]
print(f"{'Acct':>6}{'/trade':>8}{'notional':>10} | {'REALISTIC (min-order)':^34} | {'IDEAL (frac fills)':^22}")
print(f"{'':>24} | {'end':>9}{'ret':>7}{'open?':>7}{'coarse':>7} | {'end':>9}{'ret':>7}")
print("-"*92)
for cap,m,ws in configs:
    R=run(cap,m,ws,enforce_min=True); I=run(cap,m,ws,enforce_min=False)
    print(f"${cap:>5}{'$'+str(m):>8}{'$'+str(int(m*LEV)):>10} | "
          f"${R['end']:>8,}{R['ret']:>+6}%{R['taken']:>7}{R['coarse_exits']:>7} | "
          f"${I['end']:>8,}{I['ret']:>+6}%   (cant-open={R['cant_open']})")
print("\nnote: 'coarse' = BTC trades where the 11-step ladder could NOT fully execute")
print("      because partial closes fell below the exchange minimum order size.")
