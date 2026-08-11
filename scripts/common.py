#!/usr/bin/env python3
"""
Shared helpers for the generic scrapers. Keep this dependency-free (stdlib only)
so every script can import it without surprises.

Layout convention (everything runtime lives under <repo>/data, git-ignored):
    data/<account-slug>/twitter_posts.json      scraped X posts
    data/<account-slug>/telegram_posts.json     scraped Telegram messages
    data/<account-slug>/media/                   downloaded images/charts
    data/<account-slug>/analysis/                AI-authored scripts + outputs
    data/secrets/                                sessions, storage_state, .env-derived
    data/price_cache/                            Binance klines cache (shared)
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SECRETS = os.path.join(DATA, "secrets")


def slug(name: str) -> str:
    """A filesystem-safe folder name for an account handle / channel."""
    s = name.strip().lstrip("@").lower()
    s = s.split("t.me/")[-1].split("/")[-1]          # accept a t.me link
    s = re.sub(r"[^a-z0-9._-]+", "-", s).strip("-._")
    return s or "account"


def account_dir(name: str) -> str:
    d = os.path.join(DATA, slug(name))
    os.makedirs(d, exist_ok=True)
    return d


def ensure_secrets() -> str:
    os.makedirs(SECRETS, exist_ok=True)
    return SECRETS


def load_env() -> dict:
    """Read <repo>/.env (KEY=VALUE lines) then overlay real env vars.

    Same lightweight parser the scrapers have always used — no python-dotenv
    dependency. Returns a dict with the Telegram + Anthropic keys pre-seeded.
    """
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip()
                # Strip a whitespace-separated inline comment (` # ...`) so the
                # commented .env.example lines work when filled in. A '#' with no
                # leading space is kept (it may be part of a key/secret).
                m = re.search(r"\s#", v)
                if m:
                    v = v[:m.start()].rstrip()
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("TG_API_ID", "TG_API_HASH", "TG_PHONE", "ANTHROPIC_API_KEY"):
        env.setdefault(k, os.environ.get(k, ""))
    return env
