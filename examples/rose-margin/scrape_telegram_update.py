#!/usr/bin/env python3
"""
INCREMENTAL update for the Rose_Margin Telegram scrape.

Instead of re-downloading the whole history, this loads the existing
data/telegram_rose.json, finds the highest message id we already have, and pulls
ONLY messages newer than that (Telethon `min_id`). New messages are appended and
the file is re-saved (channel/since metadata preserved). Fast + cheap.

Run in YOUR terminal (uses the saved rose.session login):
    python scrape_telegram_update.py
"""
import json
import os
from datetime import datetime

from telethon.sync import TelegramClient

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "telegram_rose.json")
CHANNEL_MATCH = "rose_margin"            # case-insensitive substring of the title


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


def find_channel(client):
    for d in client.iter_dialogs():
        if CHANNEL_MATCH in (d.name or "").lower():
            print(f">> channel: '{d.name}'", flush=True)
            return d.entity
    raise SystemExit(f"!! No chat title contains '{CHANNEL_MATCH}'.")


def main():
    data = json.load(open(OUT))
    posts = data["posts"]
    have_ids = {p["id"] for p in posts}
    last_id = max(have_ids)
    print(f">> have {len(posts)} messages, newest id = {last_id}", flush=True)

    env = load_env()
    if not env["TG_API_ID"] or not env["TG_API_HASH"]:
        raise SystemExit("!! Missing TG_API_ID / TG_API_HASH in .env")
    client = TelegramClient(os.path.join(HERE, "rose"), int(env["TG_API_ID"]),
                            env["TG_API_HASH"])
    client.flood_sleep_threshold = 120
    client.start(phone=env["TG_PHONE"] or None)
    print(">> logged in.", flush=True)

    channel = find_channel(client)
    added = 0
    # min_id => only messages strictly newer than what we already stored
    for msg in client.iter_messages(channel, min_id=last_id, reverse=True):
        if msg.id in have_ids:
            continue
        mt = None
        if msg.photo: mt = "photo"
        elif msg.video: mt = "video"
        elif msg.document: mt = "document"
        posts.append({
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "text": msg.message or "",
            "media_type": mt,
            "has_media": mt is not None,
            "views": getattr(msg, "views", None),
        })
        have_ids.add(msg.id)
        added += 1
        if added % 100 == 0:
            print(f"   +{added} new... (latest {msg.date.date()})", flush=True)

    posts.sort(key=lambda p: p["id"])
    data["posts"] = posts
    data["count"] = len(posts)
    data["scraped_at"] = datetime.utcnow().isoformat()
    json.dump(data, open(OUT, "w"), indent=1, ensure_ascii=False)
    latest = max((p["date"] for p in posts if p["date"]), default="?")
    print(f">> DONE. Added {added} new messages -> {len(posts)} total "
          f"(latest {latest})", flush=True)
    client.disconnect()


if __name__ == "__main__":
    main()
