#!/usr/bin/env python3
"""
Resumable harness for reading Rose's chart images.

  python extract_helper.py next [N]   -> print next N undone call-images
                                         (id, date, caption, filepath) for me to Read
  python extract_helper.py stat        -> progress counts

The extractions themselves live in data/tg_calls_extracted.json, written by
extract_helper.py add '<json-array>' (one record per call):
  {"id":39091,"coin":"XRP","dir":"long","entry":2.14,"targets":[3.616],
   "sl":1.8165,"tgt_pct":[69.45],"sl_pct":-14.88,"lev":null,"chart_ex":"binance",
   "note":""}
Records with "skip":true (not a real call / unreadable) are counted done but excluded.
"""
import json, os, re, sys
from collections import OrderedDict

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "telegram_rose.json")
IMG = os.path.join(HERE, "data", "tg_images")
OUT = os.path.join(HERE, "data", "tg_calls_extracted.json")
BSYM = os.path.join(HERE, "data", "binance_symbols.json")


def binance_set():
    s = json.load(open(BSYM))
    return set(s["fut"]) | set(s["spot"])


def load_out():
    if os.path.exists(OUT):
        return json.load(open(OUT))
    return {"calls": []}


def call_images():
    posts = {p["id"]: p for p in json.load(open(DATA))["posts"]}
    binance = binance_set()
    out = []
    for f in os.listdir(IMG):
        if not f.split(".")[0].isdigit():
            continue
        i = int(f.split(".")[0])
        p = posts.get(i)
        if not p:
            continue
        t = p["text"] or ""
        m = re.search(r'#([A-Za-z][A-Za-z0-9]{1,12})', t)
        coin = m.group(1).upper() if m else None
        out.append({"id": i, "date": p["date"][:16], "coin": coin,
                    "caption": t.split("\n")[0][:60],
                    "on_binance": coin in binance if coin else False,
                    "path": os.path.join("data", "tg_images", f)})
    out.sort(key=lambda r: r["date"])
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stat"
    done = {c["id"] for c in load_out()["calls"]}
    imgs = call_images()
    # NOTE: caption-coin/on_binance below are HINTS only. The true coin + Binance
    # listing is decided by READING the chart header (LLM), not this regex.
    todo = [r for r in imgs if r["id"] not in done]

    if cmd == "stat":
        print(f"call-images: {len(imgs)} | extracted: {len(done)} | "
              f"remaining: {len(todo)}")
    elif cmd == "next":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
        for r in todo[:n]:
            print(f"{r['id']}\t{r['date']}\t{r['coin']}(hint)\t{r['caption']}\t{r['path']}")
    elif cmd == "add":
        recs = json.loads(sys.argv[2])
        o = load_out()
        existing = {c["id"]: c for c in o["calls"]}
        for r in recs:
            existing[r["id"]] = r
        o["calls"] = sorted(existing.values(), key=lambda c: c["id"])
        json.dump(o, open(OUT, "w"), indent=1, ensure_ascii=False)
        print(f"saved. total extracted: {len(o['calls'])}")


if __name__ == "__main__":
    main()
