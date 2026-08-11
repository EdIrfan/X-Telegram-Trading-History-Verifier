# 05 — File layout

## Repo root (committed)
```
CLAUDE.md              the AI's analysis playbook: extraction/grading/backtest
                        rules and the honesty checks — read before analyzing any account
context/               this folder — model-agnostic project briefing
README.md              human-facing quick start
TODO.md                current project status / open tasks (time-sensitive, check it)
requirements.txt        Python deps: playwright, requests, Telethon, markdown, rich
docker-compose.yml      plain-Docker entry point (alternative to VS Code Dev Containers)
.devcontainer/
  Dockerfile            builds the container: Python, Node, claude CLI, Chromium, noVNC
  devcontainer.json     VS Code Dev Containers config (mounts, ports, auth wiring)
.env.example            template for .env (Telegram creds + ANTHROPIC_API_KEY)
scripts/                fixed, generic tools — see context/02-architecture.md
  scrape_telegram.py
  download_tg_media.py
  x_login.py
  scrape_twitter.py
  prices.py
  common.py
  start-display.sh
  md2html.py
  smoke-test.sh
examples/                two full worked reference analyses (data git-ignored)
  rose-margin/            Telegram case — extraction, 3-way grader, alert bot, docs/
  blockchainedbb/         X/Twitter case — scraping, grading, laddered backtest, docs/
```

## `data/` (git-ignored — created at runtime, never committed)
```
data/
  <account-slug>/                 one per analyzed account (slug = lowercased handle)
    twitter_posts.json            raw scrape (X accounts)
    telegram_posts.json           raw scrape (Telegram channels)
    media/                        downloaded chart images
    analysis/                     AI-authored, per-account code + outputs
      extract.py                  raw posts -> normalized calls
      grade.py                    normalized calls -> 3-way graded results
      backtest.py                 graded results -> account simulation
      REPORT.md                   the final honest verdict (the main deliverable)
      alert_bot.py                optional: alert-only live poller
      *.json                      intermediate/graded/backtest data, for reproducibility
  secrets/
    telegram.session              Telethon session (after first Telegram login)
    x_storage_state.json          X/Twitter cookies (after x_login.py)
  price_cache/                    cached Binance klines, shared across all accounts
```

`data/<slug>` naming: `scripts/common.py:slug()` lowercases the handle, strips a
leading `@`, accepts a `t.me/...` link, and sanitizes to `[a-z0-9._-]`.

## Why this split
- Anything that's the **same regardless of which account** you're analyzing lives
  in `scripts/` and is committed — it's the reusable tool.
- Anything **specific to one account's analysis** (extraction logic, grading
  quirks, the report itself) lives under `data/<slug>/analysis/` and is git-ignored
  — because every caller's posting style is different, that code is written fresh
  by the AI agent each time, and it may reference the actual scraped content of a
  paid/private channel that shouldn't be committed.
- `examples/` is the deliberate exception: two *finished* per-account analyses kept
  in git (code + docs, not the underlying scraped data) purely as methodology
  references for the next analysis.
