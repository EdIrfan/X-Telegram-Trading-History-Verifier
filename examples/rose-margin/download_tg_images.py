#!/usr/bin/env python3
"""
Download the CHART images for Rose_Margin call messages, so the levels she draws
(entry / targets / SL) can actually be read. The scrape only stored flags, not the
pictures — this fetches the photos for call-style messages into data/tg_images/.

Resumable: skips ids already on disk. Uses the saved rose.session login.
    .venv/bin/python download_tg_images.py
"""
import json
import os
import re
from telethon.sync import TelegramClient

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "telegram_rose.json")
IMGDIR = os.path.join(HERE, "data", "tg_images")
CHANNEL_MATCH = "rose_margin"

# A message is a "call" if it's a photo whose caption has a coin hashtag AND a
# trade word. (Levels are inside the chart; caption just labels it.)
COIN = re.compile(r'#[A-Za-z]')
CALLWORD = re.compile(r'\b(setup|long|short|buy|sell|entry|target)\b', re.I)


def load_env():
    env = {}
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("TG_API_ID", "TG_API_HASH", "TG_PHONE"):
        env.setdefault(k, os.environ.get(k, ""))
    return env


def call_ids():
    posts = json.load(open(DATA))["posts"]
    ids = []
    for p in posts:
        if p["media_type"] != "photo":
            continue
        t = p["text"] or ""
        if COIN.search(t) and CALLWORD.search(t):
            ids.append(p["id"])
    return set(ids)


def find_channel(client):
    for d in client.iter_dialogs():
        if CHANNEL_MATCH in (d.name or "").lower():
            return d.entity
    raise SystemExit("!! channel not found")


def main():
    os.makedirs(IMGDIR, exist_ok=True)
    want = call_ids()
    have = {int(f.split(".")[0]) for f in os.listdir(IMGDIR)
            if f.split(".")[0].isdigit()}
    todo = sorted(want - have)
    print(f">> call-images wanted: {len(want)} | already have: {len(have)} | "
          f"to download: {len(todo)}", flush=True)
    if not todo:
        print(">> nothing to do."); return

    env = load_env()
    client = TelegramClient(os.path.join(HERE, "rose"), int(env["TG_API_ID"]),
                            env["TG_API_HASH"])
    client.flood_sleep_threshold = 120
    client.start(phone=env["TG_PHONE"] or None)
    channel = find_channel(client)
    print(">> logged in.", flush=True)

    done = 0
    # fetch in id-chunks to keep requests reasonable
    for i in range(0, len(todo), 100):
        chunk = todo[i:i + 100]
        for msg in client.get_messages(channel, ids=chunk):
            if msg is None or not msg.photo:
                continue
            out = os.path.join(IMGDIR, f"{msg.id}.jpg")
            msg.download_media(file=out)
            done += 1
            if done % 25 == 0:
                print(f"   downloaded {done}/{len(todo)}...", flush=True)

    print(f">> DONE. Downloaded {done} images -> {IMGDIR}", flush=True)
    client.disconnect()


if __name__ == "__main__":
    main()
