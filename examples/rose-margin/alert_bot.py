#!/usr/bin/env python3
"""
Rose Margin ALERT-ONLY bot (15-min poller).  NO auto-trading — by design.

Why alert-only: the backtest (docs/backtest_results.md) shows no harvestable
mechanical edge — best config -34%, alt moonshots are -EV, and her multibagger
"brags" are largely unrealizable wicks (docs/findings_grading.md). Her edge, if any,
is discretionary. So this surfaces her calls in real time and TAGS each with what the
analysis found, so a human decides. It does not place trades.

Polls the saved rose.session for new messages, classifies each new call/exit, prints
an alert tagged by segment verdict, and remembers the last id.

Run (in YOUR terminal/venv, same as the scraper):
    .venv/bin/python alert_bot.py --once     # single poll (test)
    .venv/bin/python alert_bot.py --loop     # poll every 15 min
"""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
STATE = os.path.join(HERE, "data", "alert_state.json")
LOG = os.path.join(HERE, "data", "alerts.log")
CHANNEL_MATCH = "rose_margin"
POLL_SECONDS = 15 * 60

LARGECAPS = {"BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LTC", "TRX",
             "LINK", "AVAX", "DOT", "BCH"}
CALLWORD = re.compile(r"\b(long|short(?:ing|ed|s)?|buy|bullish|setup|add|hold|scalp|"
                      r"accumulat|re-?buy|rebuy|re-?entry)\b", re.I)
SHORTW = re.compile(r"\bshort(?:ing|ed|s)?\b", re.I)   # short / shorting / shorts
CLOSEW = re.compile(r"\bclose[ds]?\b|\bclosing\b|\bstopped out\b|\bbook(?:ed)? profit\b|"
                    r"\bsl hit\b|\bcut loss\b|\bexit(?:ed|ing)?\b", re.I)
HASHTAG = re.compile(r"#([A-Za-z][A-Za-z0-9]{1,14})")
NUM = re.compile(r"(?<![\w.])\d[\d,]*\.?\d*")

VERDICT = {
    "short": "SHORT — her better side (~breakeven historically). OK to consider, "
             "esp. BTC/ETH; size small, she cuts fast.",
    "major_long": "MAJOR-COIN LONG — ~breakeven historically. Fine small; mirror her exit.",
    "alt_long": "ALT MOONSHOT LONG — -EV as a followable trade; her 'x5' brags are "
                "mostly unrealizable wicks. TINY lottery size or SKIP.",
    "exit": "EXIT signal — she's closing/stopping. If you mirror her, flatten this coin.",
    "update": "PERF UPDATE / brag — treat as marketing, not a new entry.",
    "info": "Commentary — no action.",
}


def load_env():
    env = {}
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    for k in ("TG_API_ID", "TG_API_HASH", "TG_PHONE"):
        env.setdefault(k, os.environ.get(k, ""))
    return env


def state_get():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE)).get("last_id", 0)
        except Exception:
            pass
    # seed from the scraped store so we don't replay history
    try:
        return max(p["id"] for p in
                   json.load(open(os.path.join(HERE, "data", "telegram_rose.json")))["posts"])
    except Exception:
        return 0


def state_put(last_id):
    json.dump({"last_id": last_id, "ts": datetime.now(timezone.utc).isoformat()},
              open(STATE, "w"))


def classify(text, has_photo):
    t = " ".join((text or "").split())
    low = t.lower()
    coins = [c.upper() for c in HASHTAG.findall(t)]
    primary = next((c for c in coins), None)
    # exit? (a close/stop verb wins outright; "close short #BTC" is an EXIT, the
    # "short" just says which side to flatten — not a new short)
    if CLOSEW.search(low):
        return "exit", primary, coins, t
    # a call? (chart photo + coin + call word, or text buy/short with coin).
    # checked BEFORE the brag detector so "#LAB Short 1x lev" isn't read as "x1".
    if (has_photo or CALLWORD.search(low)) and primary:
        d = "short" if SHORTW.search(low) else "long"
        if d == "short":
            seg = "short"
        else:
            seg = "major_long" if primary in LARGECAPS else "alt_long"
        return seg, primary, coins, t
    # perf brag (xN / +NNN%) with no fresh call word and no chart -> marketing
    if re.search(r"\bx\s?\d+\b|\b\d+x\b", low) and "lev" not in low:
        return "update", primary, coins, t
    return "info", primary, coins, t


def alert(msg_id, when, seg, primary, coins, text, has_photo):
    tag = {"short": "📉 SHORT", "major_long": "📈 MAJOR LONG",
           "alt_long": "🎰 ALT LONG", "exit": "✖ EXIT",
           "update": "📣 BRAG", "info": "· info"}[seg]
    line = (f"\n[{when}] {tag}  {('#'+primary) if primary else ''}"
            f"{'  📊chart' if has_photo else ''}\n"
            f"    msg: {text[:160]}\n"
            f"    >>> {VERDICT[seg]}")
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(f"{when}\t{seg}\t{primary or ''}\t{msg_id}\t{text[:200]}\n")
    return line


def poll():
    from telethon.sync import TelegramClient
    env = load_env()
    if not env["TG_API_ID"]:
        sys.exit("!! missing TG creds in .env")
    last_id = state_get()
    client = TelegramClient(os.path.join(HERE, "rose"), int(env["TG_API_ID"]),
                            env["TG_API_HASH"])
    client.flood_sleep_threshold = 120
    client.start(phone=env["TG_PHONE"] or None)
    channel = next((d.entity for d in client.iter_dialogs()
                    if CHANNEL_MATCH in (d.name or "").lower()), None)
    if channel is None:
        client.disconnect(); sys.exit("!! channel not found")
    new = list(client.iter_messages(channel, min_id=last_id, reverse=True))
    actionable = 0; maxid = last_id
    for m in new:
        maxid = max(maxid, m.id)
        seg, primary, coins, text = classify(m.message or "", bool(m.photo))
        if seg == "info" and not m.photo:
            continue
        actionable += 1
        when = m.date.astimezone(timezone.utc).strftime("%m-%d %H:%M") if m.date else "?"
        alert(m.id, when, seg, primary, coins, text, bool(m.photo))
    if maxid > last_id:
        state_put(maxid)
    print(f"\n>> polled: {len(new)} new msgs, {actionable} actionable "
          f"(last_id {last_id}->{maxid})", flush=True)
    client.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    a = ap.parse_args()
    if a.loop:
        print(">> Rose alert bot — polling every 15 min (Ctrl-C to stop)", flush=True)
        while True:
            try:
                poll()
            except Exception as e:
                print(f"!! poll error: {e}", flush=True)
            time.sleep(POLL_SECONDS)
    else:
        poll()


if __name__ == "__main__":
    main()
