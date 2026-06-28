#!/usr/bin/env python3
"""
Scrape ANY Telegram channel's message history into JSON, via YOUR Telegram
account (Telethon / MTProto). Text + dates + media flags, per channel.

ONE-TIME SETUP (free, ~5 min) — done once, reused forever:
  1. Go to https://my.telegram.org -> "API development tools", log in with your
     phone, create an app. Copy the api_id (number) and api_hash (long string).
  2. Copy .env.example -> .env at the repo root and fill in:
        TG_API_ID=1234567
        TG_API_HASH=abcdef0123456789abcdef0123456789
        TG_PHONE=+11234567890
  3. Run this once IN THE CONTAINER TERMINAL:
        python scripts/scrape_telegram.py "<channel>"
     Telegram texts you a login code — paste it (and your 2FA password if any).
     A session is saved to data/secrets/telegram.session — no more logins.

<channel> may be: a @username, a t.me/... link, a numeric id, or a case-insensitive
substring of the channel title (it searches the chats you've joined). Output goes to
data/<channel>/telegram_posts.json.

    python scripts/scrape_telegram.py "@some_signals"
    python scripts/scrape_telegram.py "Rose_Margin" --since 2025-01-01
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import account_dir, ensure_secrets, load_env  # noqa: E402

from telethon.sync import TelegramClient  # noqa: E402

SESSION = os.path.join(ensure_secrets(), "telegram")  # -> telegram.session


def resolve_channel(client, ref):
    """Accept @username / t.me link / numeric id / title substring."""
    ref = ref.strip()
    # direct handle / link / id
    for candidate in ([int(ref)] if ref.lstrip("-").isdigit() else []) + \
                     ([ref] if (ref.startswith("@") or "t.me/" in ref) else []):
        try:
            return client.get_entity(candidate)
        except Exception:
            pass
    # else: substring match against joined dialogs
    low = ref.lstrip("@").lower()
    print(f">> Searching your chats for a title containing '{low}'...", flush=True)
    for d in client.iter_dialogs():
        if low in (d.name or "").lower():
            print(f"   match: '{d.name}' (id={d.id})", flush=True)
            return d.entity
    raise SystemExit(f"!! No chat matched '{ref}'. Join the channel first, or pass "
                     "its exact @username / t.me link / numeric id.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel", help="@username, t.me link, id, or title substring")
    ap.add_argument("--since", default="2025-01-01", help="YYYY-MM-DD")
    a = ap.parse_args()

    env = load_env()
    if not env["TG_API_ID"] or not env["TG_API_HASH"]:
        sys.exit("!! Missing TG_API_ID / TG_API_HASH in .env — see setup notes at "
                 "the top of this file.")
    since = datetime.strptime(a.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    client = TelegramClient(SESSION, int(env["TG_API_ID"]), env["TG_API_HASH"])
    client.flood_sleep_threshold = 120
    client.start(phone=env["TG_PHONE"] or None)
    print(">> Logged in.", flush=True)

    channel = resolve_channel(client, a.channel)
    title = getattr(channel, "title", None) or getattr(channel, "username", a.channel)
    out = os.path.join(account_dir(a.channel), "telegram_posts.json")

    posts, n = [], 0
    for msg in client.iter_messages(channel, reverse=True, offset_date=since):
        if msg.date and msg.date < since:
            continue
        mt = ("photo" if msg.photo else "video" if msg.video
              else "document" if msg.document else None)
        posts.append({
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "text": msg.message or "",
            "media_type": mt,
            "has_media": mt is not None,
            "views": getattr(msg, "views", None),
        })
        n += 1
        if n % 250 == 0:
            print(f"   {n} messages... (latest {msg.date.date()})", flush=True)
            json.dump({"channel": title, "count": len(posts), "posts": posts},
                      open(out, "w"), indent=1, ensure_ascii=False)

    json.dump({"channel": title, "scraped_at": datetime.utcnow().isoformat(),
               "since": since.isoformat(), "count": len(posts), "posts": posts},
              open(out, "w"), indent=1, ensure_ascii=False)
    print(f">> DONE. {len(posts)} messages -> {out}", flush=True)
    client.disconnect()


if __name__ == "__main__":
    main()
