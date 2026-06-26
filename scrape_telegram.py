#!/usr/bin/env python3
"""
Scrape a Telegram channel's message history into JSON, using YOUR Telegram account
via Telethon (MTProto). Mirrors the Brave/X scraper: text + dates + media flags.

ONE-TIME SETUP (free, ~5 min):
  1. Go to https://my.telegram.org -> "API development tools", log in with your
     phone, create an app. Copy the api_id (a number) and api_hash (a long string).
  2. Create a file named `.env` next to this script (it's git-ignored) with:
        TG_API_ID=1234567
        TG_API_HASH=abcdef0123456789abcdef0123456789
        TG_PHONE=+91XXXXXXXXXX
  3. Run THIS script once in your terminal:  python scrape_telegram.py
     Telegram will text you a login code — paste it when prompted (and your 2FA
     password if you have one). A `rose.session` file is saved so you never have
     to log in again.

It then finds the channel by title and pulls Jan 1 2025 -> today into
data/telegram_rose.json.
"""
import json
import os
from datetime import datetime, timezone

from telethon.sync import TelegramClient

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "data", "telegram_rose.json")
CHANNEL_MATCH = "rose_margin"            # case-insensitive substring of the title
SINCE = datetime(2025, 1, 1, tzinfo=timezone.utc)


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
    print(">> Searching your chats for a channel matching "
          f"'{CHANNEL_MATCH}'...", flush=True)
    for d in client.iter_dialogs():
        title = (d.name or "")
        if CHANNEL_MATCH in title.lower():
            print(f"   match: '{title}'  (id={d.id})", flush=True)
            return d.entity
    raise SystemExit(f"!! No chat title contains '{CHANNEL_MATCH}'. Edit "
                     "CHANNEL_MATCH or join the channel first.")


def main():
    env = load_env()
    if not env["TG_API_ID"] or not env["TG_API_HASH"]:
        raise SystemExit("!! Missing TG_API_ID / TG_API_HASH. See setup notes "
                         "at the top of this file (.env).")
    client = TelegramClient(os.path.join(HERE, "rose"), int(env["TG_API_ID"]),
                            env["TG_API_HASH"])
    client.flood_sleep_threshold = 120     # auto-wait through rate limits
    client.start(phone=env["TG_PHONE"] or None)
    print(">> Logged in.", flush=True)

    channel = find_channel(client)
    posts, n = [], 0
    # reverse=True + offset_date => oldest-first starting just after SINCE
    for msg in client.iter_messages(channel, reverse=True, offset_date=SINCE):
        if msg.date and msg.date < SINCE:
            continue
        text = msg.message or ""
        mt = None
        if msg.photo: mt = "photo"
        elif msg.video: mt = "video"
        elif msg.document: mt = "document"
        posts.append({
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "text": text,
            "media_type": mt,
            "has_media": mt is not None,
            "views": getattr(msg, "views", None),
        })
        n += 1
        if n % 250 == 0:
            print(f"   {n} messages... (latest {msg.date.date()})", flush=True)
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            json.dump({"channel": getattr(channel, "title", "rose"),
                       "count": len(posts), "posts": posts},
                      open(OUT, "w"), indent=1, ensure_ascii=False)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"channel": getattr(channel, "title", "rose"),
               "scraped_at": datetime.utcnow().isoformat(),
               "since": SINCE.isoformat(), "count": len(posts), "posts": posts},
              open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f">> DONE. Saved {len(posts)} messages -> {OUT}", flush=True)
    client.disconnect()


if __name__ == "__main__":
    main()
