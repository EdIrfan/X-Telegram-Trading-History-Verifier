#!/usr/bin/env python3
"""
Mine Rose_Margin's Telegram text for EXIT / CLOSE signals.

Her setups are on the chart images (data/tg_calls_extracted.json). Her EXITS are
almost always text-only ("close short #BTC", "stopped out manually -4%",
"book profit short #ETH #BTC"). The grader needs these real exits to bound the
variable hold per trade (close setup->exit by coin + chronology).

Output: data/tg_close_signals.json  -> list of
  {id, date, action, dir, coins[], pct, text}
  action: "stop" (SL hit) | "close" (manual flat) | "tp" (book/take profit)
Run:  .venv/bin/python build_close_signals.py
"""
import json, os, re

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "data", "telegram_rose.json")
OUT = os.path.join(HERE, "data", "tg_close_signals.json")

FOOTER = re.compile(r"provided by\s*:?\s*@?\w+\s*$", re.I)
HASHTAG = re.compile(r"#([A-Za-z][A-Za-z0-9]{0,14})")
PCT = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%")

# --- trigger patterns (ordered by classification priority) ---
STOP = re.compile(r"\bstopped out\b|\bget stopped\b|\bgot stopped\b|\bsl hit\b|"
                  r"\bstop ?loss hit\b|\bhit (?:the )?sl\b", re.I)
TP = re.compile(r"\bbook(?:ed|ing)? profit\b|\btake profit\b|\btaking profit\b|"
                r"\btp hit\b|\bhit tp\d?\b|\btp\d? hit\b", re.I)
CLOSE = re.compile(r"\bclose[ds]?\b|\bclosing\b|\bfully out\b|\bfully closed\b|"
                   r"\bexit(?:ed|ing)?\b|\bcut (?:loss|losses|the|position)\b|"
                   r"\bflat(?:tened)?\b", re.I)
DIR = re.compile(r"\b(short|long)s?\b", re.I)

# --- exclude obvious non-exit commentary even if a trigger word appears ---
EXCLUDE = re.compile(
    r"invalidated at|breakeven point|take profit every|take profit along|"
    r"shorters got stopped|longers got stopped|bottom shorters|always take profit|"
    r"if you (?:bought|sold)|will close|how to close|when to close|should close|"
    r"best performance|trade is closed at|rose army|exit .*market when|"
    r"completes the|red banana|"
    # candle-close / level talk (not a position close)
    r"close (?:above|below)|programmed to close|weekly is programmed|"
    # third-party whale/he/she/they closes & big-$ closes
    r"(?:whale|he|she|they)\s+(?:has |just |almost )?clos|closed \$?\d|"
    r"\d+\s*m\$?\s+(?:short|long|position)|pnl|"
    # market-wide commentary, not her own exit
    r"are closing (?:short|long)|bears are clos|bulls are clos|"
    r"setups got|got profit|you asked|tanked-ship|no chance .*exit|"
    # candle-close idioms & forward plans (not an executed exit)
    r"monthly close|weekly close|daily close|pretty close|consecutive|"
    r"fully exit at|% exit at|we exit market|final bias|crime season|"
    r"forced to close|are forced",
    re.I)

# non-coin hashtags to drop from the coin list
NOT_COIN = {"recall"}  # rare label tags; extend if needed

# plain-text ticker fallback (UPPERCASE isolated word) for untagged closes
# e.g. "closed BTC at 88k", "XMR DASH stopped out manually"
MAJORS = ("BTC ETH SOL XRP BNB DOGE ADA XLM ZEC HYPE TAO SUI LINK AVAX XMR DASH "
          "AAVE LTC TRX DOT NEAR ARB OP INJ TIA SEI BCH ETC FIL ATOM UNI ENA ONDO "
          "PEPE WIF BONK FART ASTER TRUMP ARIA STRK TUT EPT GPS").split()
MAJOR_RE = {m: re.compile(r"(?<![A-Za-z0-9])" + m + r"(?![A-Za-z0-9])") for m in MAJORS}


def clean(text):
    t = " ".join((text or "").split())
    t = FOOTER.sub("", t).strip()
    return t


def classify(t):
    if STOP.search(t):
        return "stop"
    if TP.search(t):
        return "tp"
    if CLOSE.search(t):
        return "close"
    return None


def main():
    posts = json.load(open(SRC))["posts"]
    out = []
    for p in posts:
        t = clean(p.get("text"))
        if not t or EXCLUDE.search(t):
            continue
        action = classify(t)
        if not action:
            continue
        coins = [c.upper() for c in HASHTAG.findall(t)
                 if c.lower() not in NOT_COIN]
        # plain-text major fallback (supplements tags; dedup preserves order)
        for m, rx in MAJOR_RE.items():
            if m not in coins and rx.search(t):
                coins.append(m)
        seen = set()
        coins = [c for c in coins if not (c in seen or seen.add(c))]
        m = DIR.search(t)
        pm = PCT.search(t)
        out.append({
            "id": p["id"],
            "date": (p.get("date") or "")[:19],
            "action": action,
            "dir": m.group(1).lower() if m else None,
            "coins": coins,
            "pct": float(pm.group(1)) if pm else None,
            "text": t[:200],
        })
    out.sort(key=lambda r: r["id"])
    json.dump({"count": len(out), "signals": out},
              open(OUT, "w"), indent=1, ensure_ascii=False)

    from collections import Counter
    print(f">> {len(out)} close/exit signals -> {OUT}")
    print("   by action:", dict(Counter(r["action"] for r in out)))
    coinc = Counter(c for r in out for c in r["coins"])
    print("   top coins:", coinc.most_common(15))
    print("   with %:", sum(1 for r in out if r["pct"] is not None))
    print("   no coin tag:", sum(1 for r in out if not r["coins"]))
    return out


if __name__ == "__main__":
    main()
