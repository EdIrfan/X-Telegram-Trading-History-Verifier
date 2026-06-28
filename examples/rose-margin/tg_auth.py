#!/usr/bin/env python3
"""Two-step Telegram login so the assistant can drive it: `request` sends the
code to your phone; `signin <CODE>` completes login and saves rose.session."""
import json, os, sys
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

HERE = os.path.dirname(__file__)
HASHFILE = os.path.join(HERE, ".tg_codehash")


def env():
    e = {}
    for line in open(os.path.join(HERE, ".env")):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e


def client(e):
    c = TelegramClient(os.path.join(HERE, "rose"), int(e["TG_API_ID"]), e["TG_API_HASH"])
    c.connect()
    return c


def main():
    e = env(); c = client(e)
    if c.is_user_authorized():
        print("ALREADY_LOGGED_IN"); c.disconnect(); return
    mode = sys.argv[1] if len(sys.argv) > 1 else "request"
    if mode == "request":
        sent = c.send_code_request(e["TG_PHONE"])
        json.dump({"hash": sent.phone_code_hash}, open(HASHFILE, "w"))
        print("CODE_SENT to", e["TG_PHONE"][:3] + "...")
    elif mode == "signin":
        code = sys.argv[2]
        ph = json.load(open(HASHFILE))["hash"]
        try:
            c.sign_in(e["TG_PHONE"], code, phone_code_hash=ph)
            print("LOGIN_OK")
        except SessionPasswordNeededError:
            print("NEEDS_2FA_PASSWORD")  # must be finished in your own terminal
    c.disconnect()


if __name__ == "__main__":
    main()
