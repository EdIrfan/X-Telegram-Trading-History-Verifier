#!/usr/bin/env python3
"""
Complete classification of ALL 142 strong candidates (data/sample.json), so
nothing is cherry-picked. Every post gets a category; every genuine forward
directional call is graded vs Binance (7-day window, leverage-adjusted).

Categories:
  CALL        - genuine forward directional call (graded)
  PNL         - retroactive PnL brag / "target completed"
  RETRO       - "I called the bottom/top" victory lap / commentary about past
  CLOSE       - closing or managing an existing position
  PROMO       - discord/giveaway/ticker-dump
  CONDITIONAL - "if X then Y" / not yet actionable
  HORIZON     - a real call but multi-week/month target (outside 7d test)
  COMMENTARY  - watchlist / vague / macro musings
"""
import json, os
from datetime import datetime, timedelta, timezone
from prices import price_at, range_high_low

HORIZON = 7
THRESH = {"BTC":1.5,"ETH":2.0,"BNB":2.0,"SOL":2.5,"XRP":2.5,"DOGE":3.0,"LTC":2.5,"LINK":2.5}
DT = {s["i"]: s["dt"] for s in json.load(open(os.path.join(os.path.dirname(__file__),"data","sample.json")))}

def C(coin,d,tg,note): return {"cat":"CALL","coin":coin,"dir":d,"tg":tg,"note":note}

# Full classification of indices 0..141
K = {
 0:{"cat":"PROMO"}, 1:{"cat":"CLOSE"}, 2:{"cat":"PNL"}, 3:{"cat":"COMMENTARY"},
 4:{"cat":"CONDITIONAL"}, 5:{"cat":"COMMENTARY"},
 6:C("BTC","long",[],"approaching 55EMA, expect bounce"),
 7:{"cat":"RETRO"},
 8:C("BTC","long",[106000,108000],"ST zone 106-108k"),
 9:C("XRP","long",[],"bought XRP/ONDO spot dca1"),
 10:{"cat":"CLOSE"}, 11:{"cat":"CLOSE"},
 12:C("BTC","long",[108888],"alts rally until BTC 108888"),
 13:{"cat":"PNL"}, 14:{"cat":"CLOSE"}, 15:{"cat":"COMMENTARY"}, 16:{"cat":"PNL"},
 17:{"cat":"PNL"}, 18:{"cat":"PNL"},
 19:C("BTC","long",[],"100% buying the dip"),
 20:{"cat":"COMMENTARY"}, 21:{"cat":"RETRO"}, 22:{"cat":"COMMENTARY"},
 23:{"cat":"HORIZON"}, 24:{"cat":"RETRO"}, 25:{"cat":"RETRO"}, 26:{"cat":"RETRO"},
 27:C("XRP","long",[],"'does that look bearish?' = bullish"),
 28:C("BTC","long",[],"averaging SOW->UT, buying alts"),
 29:C("XRP","long",[],"buying 50% XRP/LTC/LINK"),
 30:{"cat":"COMMENTARY"}, 31:{"cat":"COMMENTARY"}, 32:{"cat":"PNL"}, 33:{"cat":"RETRO"},
 34:{"cat":"PNL"},
 35:C("BTC","long",[110000,112000],"sizing 104-105k, target 110-112k"),
 36:{"cat":"PNL"},
 37:C("XRP","long",[3.0],"XRP target ~2.7-3"),
 38:{"cat":"PNL"}, 39:{"cat":"COMMENTARY"}, 40:{"cat":"PNL"}, 41:{"cat":"RETRO"},
 42:C("ETH","long",[3000],"exit at 3k"),
 43:C("BTC","long",[110000,112000],"TP1 110k TP2 112k"),
 44:C("ETH","long",[2600],"ETH TP1 2600"),
 45:{"cat":"CLOSE"}, 46:{"cat":"PNL"}, 47:{"cat":"COMMENTARY"}, 48:{"cat":"PNL"},
 49:C("BTC","long",[112000],"SOW->UT, UT 112k"),
 50:{"cat":"CONDITIONAL"}, 51:{"cat":"PNL"}, 52:{"cat":"CLOSE"},
 53:C("BTC","long",[112000],"reclaim 108888 -> 112k bounce"),
 54:{"cat":"COMMENTARY"},
 55:C("ETH","long",[2888],"ETH could hit 2888-3k"),
 56:{"cat":"RETRO"}, 57:{"cat":"PNL"}, 58:{"cat":"PNL"}, 59:{"cat":"CLOSE"},
 60:{"cat":"HORIZON"}, 61:{"cat":"COMMENTARY"},
 62:C("ETH","long",[3500],"buy 2888 sell 3500"),
 63:{"cat":"COMMENTARY"}, 64:{"cat":"COMMENTARY"}, 65:{"cat":"RETRO"},
 66:{"cat":"CLOSE"}, 67:{"cat":"COMMENTARY"}, 68:{"cat":"RETRO"}, 69:{"cat":"COMMENTARY"},
 70:{"cat":"PROMO"}, 71:{"cat":"CONDITIONAL"}, 72:{"cat":"PROMO"},
 73:C("BTC","long",[116666],"target 116666"),
 74:{"cat":"PNL"}, 75:{"cat":"PNL"}, 76:{"cat":"HORIZON"},
 77:C("BNB","long",[888,1200],"long every dip to 888/1200"),
 78:C("BTC","long",[],"short almost done, gonna long bottom"),
 79:{"cat":"CLOSE"}, 80:{"cat":"PNL"}, 81:{"cat":"PNL"}, 82:{"cat":"PNL"}, 83:{"cat":"PNL"},
 84:C("BTC","short",[],"closed longs, 'brace yourself'"),
 85:C("BTC","long",[],"investor avg 105/100/96k"),
 86:C("XRP","long",[4.0],"average 2.5-2.66, target 4"),
 87:C("BTC","short",[],"BTC short going good"),
 88:C("ETH","short",[],"ETH short"),
 1088:C("BTC","short",[],"BTC short still (same post as 88)"),
 89:{"cat":"PROMO"}, 90:{"cat":"PNL"}, 91:{"cat":"PNL"}, 92:{"cat":"PNL"},
 93:C("BTC","short",[],"short from 117k playing out"),
 94:{"cat":"PNL"}, 95:{"cat":"CLOSE"},
 96:C("ETH","long",[5200],"DCA 3777-4000, TP5 5200"),
 97:C("ETH","long",[],"bought ETH"),
 98:C("BTC","long",[],"very little left to bottom"),
 99:{"cat":"PNL"}, 100:{"cat":"RETRO"},
 101:C("BTC","long",[],"bottom ~107k then up nonstop"),
 102:{"cat":"PNL"},
 103:C("BTC","long",[],"short done, now Uptober"),
 104:C("XRP","long",[],"DCA2 limits 2.5-2.6"),
 105:{"cat":"PNL"}, 106:{"cat":"PNL"},
 107:C("ETH","long",[],"limits 3777-3999 accumulate"),
 108:{"cat":"COMMENTARY"}, 109:C("BTC","long",[116000,117000],"target 116-117k"),
 110:{"cat":"HORIZON"}, 111:{"cat":"PNL"}, 112:{"cat":"COMMENTARY"},
 113:C("BTC","long",[],"bullish continuation, not shorting"),
 114:{"cat":"CONDITIONAL"}, 115:{"cat":"PNL"}, 116:{"cat":"PNL"}, 117:{"cat":"RETRO"},
 118:C("BTC","long",[],"dip 107-110k then continue up"),
 119:{"cat":"PNL"}, 120:{"cat":"PNL"},
 121:C("DOGE","long",[],"buying doge/shib tonight"),
 122:{"cat":"RETRO"},
 123:C("XRP","long",[4.0],"scaling XRP, to 4 next"),
 124:{"cat":"COMMENTARY"}, 125:{"cat":"COMMENTARY"}, 126:{"cat":"COMMENTARY"},
 127:{"cat":"HORIZON"}, 128:{"cat":"COMMENTARY"}, 129:{"cat":"PNL"},
 130:C("BTC","long",[],"buying 118-120k dips"),
 131:{"cat":"COMMENTARY"},
 132:C("ETH","long",[5200],"exit 5200, could reach 5500"),
 133:{"cat":"COMMENTARY"}, 134:{"cat":"COMMENTARY"}, 135:{"cat":"COMMENTARY"},
 136:C("XRP","long",[],"averaging XRP 2.6-2.7"),
 137:C("SOL","long",[],"95% ETF approval"),
 138:{"cat":"CONDITIONAL"},
 139:C("BTC","long",[],"next pump, 110-112k support"),
 140:C("ETH","long",[4200,4400,4700],"TPs 4200/4400/4700"),
 141:{"cat":"COMMENTARY"},
}

def verify(coin,dt,direction,tg):
    thr=THRESH.get(coin,2.5)
    start=datetime.fromisoformat(dt+":00+00:00")
    end=min(start+timedelta(days=HORIZON),datetime.now(timezone.utc))
    p0=price_at(coin,start); lo,hi=range_high_low(coin,start,end); pend=price_at(coin,end)
    if not p0 or not pend: return "UNVERIFIABLE","UNVERIFIABLE",None,None,"no price"
    move=(pend-p0)/p0*100
    fav=(hi-p0)/p0*100 if direction=="long" else (p0-lo)/p0*100
    adv=(p0-lo)/p0*100 if direction=="long" else (hi-p0)/p0*100
    near=[t for t in tg if 0.3*p0<=t<=3*p0]
    tgt_hit=False
    if near:
        t=max(near) if direction=="long" else min(near)
        tgt_hit=(direction=="long" and hi>=t) or (direction=="short" and lo<=t)
    if direction=="long": cv="CORRECT" if (move>=thr or tgt_hit) else "INCORRECT"
    else: cv="CORRECT" if (move<=-thr or tgt_hit) else "INCORRECT"
    ev="CORRECT" if fav>=thr else "INCORRECT"
    return cv,ev,round(fav,1),round(adv,1),f"{p0:g}->{pend:g} ({move:+.1f}%) fav+{fav:.1f}/adv-{adv:.1f}"

calls=[]; cats={}
for i in sorted(K):
    e=K[i]; idx=i if i<1000 else 88
    cats[e["cat"]]=cats.get(e["cat"],0)+1
    if e["cat"]=="CALL":
        cv,ev,fav,adv,info=verify(e["coin"],DT[idx],e["dir"],e["tg"])
        calls.append({"i":idx,"dt":DT[idx],"coin":e["coin"],"dir":e["dir"],
                      "close":cv,"exc":ev,"fav":fav,"adv":adv,"note":e["note"],"info":info})

def rate(key):
    c=sum(r[key]=="CORRECT" for r in calls); w=sum(r[key]=="INCORRECT" for r in calls)
    return c,w,(c/(c+w)*100 if c+w else 0)
cc,cw,cacc=rate("close"); ec,ew,eacc=rate("exc")

json.dump({"category_counts":cats,"n_calls":len(calls),
           "close_based":{"correct":cc,"incorrect":cw,"pct":round(cacc,1)},
           "excursion_based":{"correct":ec,"incorrect":ew,"pct":round(eacc,1)},
           "calls":calls},
          open(os.path.join(os.path.dirname(__file__),"data","graded_all.json"),"w"),indent=2)

print("=== ALL 142 strong candidates classified ===")
for k,v in sorted(cats.items(),key=lambda x:-x[1]): print(f"  {v:3d}  {k}")
print(f"\n=== {len(calls)} graded forward CALLS (7d, leverage-adj) ===")
print(f"{'DT':17}{'COIN':5}{'DIR':6}{'CLOSE':6}{'EXC':5} fav/adv  note")
for r in calls:
    print(f"{r['dt']:17}{r['coin']:5}{r['dir']:6}"
          f"{('WIN' if r['close']=='CORRECT' else 'L'):6}"
          f"{('WIN' if r['exc']=='CORRECT' else 'L'):5} +{r['fav']}/-{r['adv']}  {r['note'][:30]}")
print(f"\nCLOSE-based:     {cc}/{cc+cw} = {cacc:.1f}%")
print(f"EXCURSION-based: {ec}/{ec+ew} = {eacc:.1f}%")
