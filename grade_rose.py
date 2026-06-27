#!/usr/bin/env python3
"""
Grade Rose Margin's calls two ways (see docs/grading_spec.md).

A) follow-her : exit at earliest of {her close/stop signal, chart-SL touch, max-hold}
B) mechanical : exit at earliest of {TP1 touch, SL touch, max-hold}

Entry = her drawn level as a LIMIT (filled on first 1h candle that touches it after
she posts; never touched -> untriggered). Raw price-move return only; leverage and
sizing live in the backtest layer.

Run:  .venv/bin/python grade_rose.py
Out:  data/graded_rose.json
"""
import json, os, datetime as dt
from collections import defaultdict, Counter
from prices import ohlcv_auto

HERE = os.path.dirname(__file__)
CALLS = os.path.join(HERE, "data", "tg_calls_extracted.json")
CLOSES = os.path.join(HERE, "data", "tg_close_signals.json")
POSTS = os.path.join(HERE, "data", "telegram_rose.json")
SYMS = os.path.join(HERE, "data", "binance_symbols.json")
OUT = os.path.join(HERE, "data", "graded_rose.json")

FRICTION = 0.005
HOUR = 3600_000
DAY = 86400_000
NOW_MS = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
HIST_START = "2024-11-01"   # floor for per-symbol 1h history fetch


def to_ms(s):
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * 1000)


# ---------- load ----------
calls = json.load(open(CALLS))["calls"]
closesig = json.load(open(CLOSES))["signals"]
posts = json.load(open(POSTS))["posts"]
id2date = {p["id"]: p.get("date") for p in posts}
spot_set = set(json.load(open(SYMS)).get("spot", []))

# ---------- close-signal index ----------
# Direction MATTERS: "close short #BTC" must not flatten a BTC long. We keep the
# signal's dir; a signal applies to a trade iff sdir is None (generic close) or
# sdir == the trade's direction.
coin_sigs = defaultdict(list)        # COIN -> [(ms, action, sdir)]
agnostic = []                        # [(ms, action, sdir)]
for s in closesig:
    ms = to_ms(s.get("date"))
    if ms is None:
        continue
    rec = (ms, s["action"], s.get("dir"))
    if s["coins"]:
        for c in s["coins"]:
            coin_sigs[c].append(rec)
    else:
        agnostic.append(rec)
for c in coin_sigs:
    coin_sigs[c].sort(key=lambda r: r[0])   # by ms (sdir may be None -> no tuple cmp)
agnostic.sort(key=lambda r: r[0])


def her_exit(coin, direction, after_ms):
    """earliest (ms, action) close-signal applicable to this open trade, or None.

    Match requires same direction (or a direction-agnostic close)."""
    best = None
    for ms, act, sdir in coin_sigs.get(coin, ()):
        if ms > after_ms and (sdir is None or sdir == direction):
            best = (ms, act); break
    for ms, act, sdir in agnostic:
        if ms > after_ms and (sdir is None or sdir == direction):
            if best is None or ms < best[0]:
                best = (ms, act)
            break
    return best


# ---------- per-symbol 1h candle cache (persisted ~1 day; present-window won't
#            disk-cache via prices.py, so we cache full history here) ----------
import time
_CANDLES = {}
_HCDIR = os.path.join(HERE, "data", "price_cache")


def candles(sym):
    if sym in _CANDLES:
        return _CANDLES[sym]
    cf = os.path.join(_HCDIR, f"hist_{sym}_1h.json")
    rows = mkt = None
    if os.path.exists(cf) and time.time() - os.path.getmtime(cf) < DAY / 1000:
        try:
            obj = json.load(open(cf)); rows, mkt = obj["rows"], obj["mkt"]
        except Exception:
            rows = None
    if rows is None:
        raw, mkt = ohlcv_auto(sym, HIST_START, NOW_MS + DAY, "1h")
        rows = [(c[0], float(c[2]), float(c[3]), float(c[4])) for c in raw]
        try:
            os.makedirs(_HCDIR, exist_ok=True)
            json.dump({"rows": rows, "mkt": mkt}, open(cf, "w"))
        except Exception:
            pass
    _CANDLES[sym] = (rows, mkt)
    return _CANDLES[sym]


def hit_sl(h, l, direction, sl):
    return (l <= sl) if direction == "long" else (h >= sl)


def hit_tp(h, l, direction, tp):
    return (h >= tp) if direction == "long" else (l <= tp)


# ---------- trade universe ----------
def is_trade(r):
    if not r.get("binance") or r.get("kind") not in ("setup", "zone", "spot"):
        return False
    if r.get("dir") not in ("long", "short") or r.get("entry") in (None, 0):
        return False
    if str(r.get("note", "")).lower().startswith("duplicate of"):
        return False
    if r["kind"] == "spot" and r["binance_sym"] not in spot_set:
        return False
    return True


def grade(r):
    coin, sym, d = r["coin"], r["binance_sym"], r["dir"]
    entry = float(r["entry"]); sl = r.get("sl")
    sl = float(sl) if sl is not None else None
    tgts = [float(t) for t in (r.get("targets") or [])]
    tp1 = tgts[0] if tgts else None
    swing = bool(r.get("swing"))
    post_ms = to_ms(id2date.get(r["id"]))
    if post_ms is None:
        return {"id": r["id"], "coin": coin, "skip": "no_date"}
    maxhold = (90 if swing else 30) * DAY
    end_ms = min(post_ms + maxhold, NOW_MS)
    rows, mkt = candles(sym)
    if not rows:
        return {"id": r["id"], "coin": coin, "skip": "price_fail"}

    # ---- fill (limit at entry) ----
    fill_i = None
    for i, (ot, h, l, cl) in enumerate(rows):
        if ot < post_ms - HOUR:
            continue
        if ot > end_ms:
            break
        if l <= entry <= h:
            fill_i = i; fill_ms = ot; break
    if fill_i is None:
        return {"id": r["id"], "coin": coin, "dir": d, "kind": r["kind"],
                "skip": "untriggered"}

    sign = 1.0 if d == "long" else -1.0

    # ---- walk once, resolve methods A/B/C + excursions ----
    her = her_exit(coin, d, post_ms)
    her_ms = her[0] if her else None
    A = B = C = None
    mh = ml = None
    cpk = entry          # running peak (long: max high) / trough (short: min low)
    c_act = False        # trailing activated (price moved ACT in favor)
    last_cl = rows[fill_i][3]
    for ot, h, l, cl in rows[fill_i:]:
        if ot > end_ms:
            break
        last_cl = cl
        mh = h if mh is None else max(mh, h)
        ml = l if ml is None else min(ml, l)
        # Method A "mirror her posts": exit ONLY on her announced close/stop signal
        # (she holds through chart-SL wicks unless she posts a stop). Else max-hold.
        if A is None and her_ms is not None and ot >= her_ms:
            A = (cl, "her_stop" if her[1] == "stop" else "her_close", ot)
        # Method B: SL vs TP1 first-touch (SL wins ties)
        if B is None:
            slt = sl is not None and hit_sl(h, l, d, sl)
            tpt = tp1 is not None and hit_tp(h, l, d, tp1)
            if slt:
                B = (sl, "sl", ot)
            elif tpt:
                B = (tp1, "tp", ot)
        # Method C "let it run": wide initial stop = her chart SL; once price moves
        # +ACT in favor, switch to a TRAIL% trailing stop off the peak. (Illustrative,
        # NOT parameter-optimised — tests whether her ENTRIES have edge if you don't
        # choke the exit.)  ACT=20%, TRAIL=25%.
        if C is None:
            if d == "long":
                cpk = max(cpk, h)
                if cpk >= entry * 1.20:
                    c_act = True
                stopc = cpk * 0.75 if c_act else sl
                if stopc is not None and l <= stopc:
                    C = (stopc, "trail" if c_act else "init_sl", ot)
            else:
                cpk = min(cpk, l)
                if cpk <= entry * 0.80:
                    c_act = True
                stopc = cpk * 1.25 if c_act else sl
                if stopc is not None and h >= stopc:
                    C = (stopc, "trail" if c_act else "init_sl", ot)
    if A is None:
        A = (last_cl, "max_hold", end_ms)
    if B is None:
        B = (last_cl, "max_hold", end_ms)
    if C is None:
        C = (last_cl, "max_hold", end_ms)

    def ret(px):
        return round((px / entry - 1) * sign - FRICTION, 4)

    still_open = (post_ms + maxhold > NOW_MS)
    flags = []
    if tp1 is None:
        flags.append("no_target")
    if sl is None:
        flags.append("no_sl")
    if mkt == "futures":
        flags.append("futures_px")
    return {
        "id": r["id"], "coin": coin, "sym": sym, "dir": d, "kind": r["kind"],
        "swing": swing, "post_date": id2date.get(r["id"], "")[:16],
        "entry": entry, "fill_h_after": round((fill_ms - post_ms) / HOUR, 1),
        "A_ret": ret(A[0]), "A_reason": A[1], "A_hold_h": round((A[2] - fill_ms) / HOUR, 1),
        "B_ret": ret(B[0]), "B_reason": B[1], "B_hold_h": round((B[2] - fill_ms) / HOUR, 1),
        "C_ret": ret(C[0]), "C_reason": C[1], "C_hold_h": round((C[2] - fill_ms) / HOUR, 1),
        "tp_hit": B[1] == "tp", "sl_hit_mech": B[1] == "sl",
        # favorable / adverse excursion (per direction)
        "mfe": (round((mh - entry) / entry, 4) if d == "long"
                else round((entry - ml) / entry, 4)) if (mh and ml) else None,
        "mae": (round((ml - entry) / entry, 4) if d == "long"
                else round((entry - mh) / entry, 4)) if (mh and ml) else None,
        "still_open": still_open and (A[1] == "max_hold" or B[1] == "max_hold"),
        "flags": flags,
    }


def main():
    universe = [r for r in calls if is_trade(r)]
    graded, skips = [], []
    for r in universe:
        g = grade(r)
        (skips if "skip" in g else graded).append(g)

    # ---------- summary ----------
    def stats(rows, key):
        rs = [x[key] for x in rows]
        wins = [x for x in rs if x > 0]
        return {
            "n": len(rs),
            "win_rate": round(len(wins) / len(rs) * 100, 1) if rs else 0,
            "avg_ret_%": round(sum(rs) / len(rs) * 100, 2) if rs else 0,
            "avg_win_%": round(sum(wins) / len(wins) * 100, 2) if wins else 0,
            "avg_loss_%": round(sum(x for x in rs if x <= 0) /
                                max(1, len([x for x in rs if x <= 0])) * 100, 2),
            "sum_%": round(sum(rs) * 100, 1),
        }

    summary = {
        "candidates": len(universe),
        "graded": len(graded),
        "skipped": dict(Counter(s["skip"] for s in skips)),
        "A_follow_her": stats(graded, "A_ret"),
        "B_mechanical": stats(graded, "B_ret"),
        "C_letitrun": stats(graded, "C_ret"),
        "B_tp_hit_%": round(sum(g["tp_hit"] for g in graded) / len(graded) * 100, 1),
        "B_sl_hit_%": round(sum(g["sl_hit_mech"] for g in graded) / len(graded) * 100, 1),
        "A_exit_reasons": dict(Counter(g["A_reason"] for g in graded)),
        "B_exit_reasons": dict(Counter(g["B_reason"] for g in graded)),
        "by_dir_A": {dd: stats([g for g in graded if g["dir"] == dd], "A_ret")
                     for dd in ("long", "short")},
        "by_dir_B": {dd: stats([g for g in graded if g["dir"] == dd], "B_ret")
                     for dd in ("long", "short")},
        "by_dir_C": {dd: stats([g for g in graded if g["dir"] == dd], "C_ret")
                     for dd in ("long", "short")},
        "C_alt_long": stats([g for g in graded if g["dir"] == "long"
                             and g["coin"] not in ("BTC", "ETH")], "C_ret"),
        "C_major_long": stats([g for g in graded if g["dir"] == "long"
                               and g["coin"] in ("BTC", "ETH")], "C_ret"),
        "by_kind_A": {kk: stats([g for g in graded if g["kind"] == kk], "A_ret")
                      for kk in ("setup", "zone", "spot")},
        # regime split: 2025 (bull, BTC 88k->125k) vs 2026 (bear, 125k->59k)
        "A_by_year": {y: stats([g for g in graded if g["post_date"][:4] == y], "A_ret")
                      for y in ("2025", "2026")},
        "B_by_year": {y: stats([g for g in graded if g["post_date"][:4] == y], "B_ret")
                      for y in ("2025", "2026")},
        "A_dir_x_year": {f"{dd}-{y}":
                         stats([g for g in graded if g["dir"] == dd
                                and g["post_date"][:4] == y], "A_ret")
                         for dd in ("long", "short") for y in ("2025", "2026")},
    }
    json.dump({"summary": summary, "trades": graded, "skipped": skips},
              open(OUT, "w"), indent=1)

    print(json.dumps(summary, indent=1))
    print(f"\n-> {OUT}  ({len(graded)} graded, {len(skips)} skipped)")


if __name__ == "__main__":
    main()
