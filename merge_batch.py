#!/usr/bin/env python3
"""merge_batch.py <scratch.json> — merge a batch of extracted call records into
data/tg_calls_extracted.json (upsert by id), then print progress."""
import json, os, sys

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "tg_calls_extracted.json")


def main():
    o = json.load(open(OUT)) if os.path.exists(OUT) else {"calls": []}
    new = json.load(open(sys.argv[1]))
    ex = {c["id"]: c for c in o["calls"]}
    for r in new:
        ex[r["id"]] = r
    o["calls"] = sorted(ex.values(), key=lambda c: c["id"])
    json.dump(o, open(OUT, "w"), indent=1, ensure_ascii=False)
    setups = sum(1 for c in o["calls"] if c.get("kind") in ("setup", "update"))
    print(f"merged. total records: {len(o['calls'])} "
          f"(tradeable setups: {setups})")


if __name__ == "__main__":
    main()
