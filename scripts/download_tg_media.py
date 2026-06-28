#!/usr/bin/env python3
"""
Download a Telegram channel's CHART images so the levels drawn on them (entry /
targets / SL) can actually be read. The scrape only stores media *flags*; this
fetches the photos for call-style messages into data/<channel>/media/.

Resumable: skips ids already on disk. Reuses the session from scrape_telegram.py.
    python scripts/download_tg_media.py "@some_signals"
    python scripts/download_tg_media.py "@some_signals" --all   # every photo, not just calls

A message is treated as a "call image" if it's a photo whose caption has a coin
hashtag AND a trade word — tune CALLWORD per channel if a caller phrases differently
(the AI playbook in CLAUDE.md covers this).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import account_dir, ensure_secrets, load_env  # noqa: E402

from telethon.sync import TelegramClient  # noqa: E402

SESSION = os.path.join(ensure_secrets(), "telegram")
COIN = re.compile(r"#[A-Za-z]")
CALLWORD = re.compile(r"\b(setup|long|short|buy|sell|entry|target|scalp)\b", re.I)


def resolve_channel(client, ref):
    ref = ref.strip()
    for cand in ([int(ref)] if ref.lstrip("-").isdigit() else []) + \
                ([ref] if (ref.startswith("@") or "t.me/" in ref) else []):
        try:
            return client.get_entity(cand)
        except Exception:
            pass
    low = ref.lstrip("@").lower()
    for d in client.iter_dialogs():
        if low in (d.name or "").lower():
            return d.entity
    raise SystemExit(f"!! No chat matched '{ref}'.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--all", action="store_true", help="download every photo")
    a = ap.parse_args()

    adir = account_dir(a.channel)
    posts_file = os.path.join(adir, "telegram_posts.json")
    if not os.path.exists(posts_file):
        sys.exit(f"!! {posts_file} not found — run scrape_telegram.py first.")
    imgdir = os.path.join(adir, "media")
    os.makedirs(imgdir, exist_ok=True)

    posts = json.load(open(posts_file))["posts"]
    want = set()
    for p in posts:
        if p["media_type"] != "photo":
            continue
        t = p["text"] or ""
        if a.all or (COIN.search(t) and CALLWORD.search(t)):
            want.add(p["id"])
    have = {int(f.split(".")[0]) for f in os.listdir(imgdir)
            if f.split(".")[0].isdigit()}
    todo = sorted(want - have)
    print(f">> images wanted: {len(want)} | have: {len(have)} | to fetch: {len(todo)}",
          flush=True)
    if not todo:
        print(">> nothing to do."); return

    env = load_env()
    client = TelegramClient(SESSION, int(env["TG_API_ID"]), env["TG_API_HASH"])
    client.flood_sleep_threshold = 120
    client.start(phone=env["TG_PHONE"] or None)
    channel = resolve_channel(client, a.channel)
    print(">> logged in.", flush=True)

    done = 0
    for i in range(0, len(todo), 100):
        for msg in client.get_messages(channel, ids=todo[i:i + 100]):
            if msg is None or not msg.photo:
                continue
            msg.download_media(file=os.path.join(imgdir, f"{msg.id}.jpg"))
            done += 1
            if done % 25 == 0:
                print(f"   {done}/{len(todo)}...", flush=True)
    print(f">> DONE. {done} images -> {imgdir}", flush=True)
    client.disconnect()


if __name__ == "__main__":
    main()
