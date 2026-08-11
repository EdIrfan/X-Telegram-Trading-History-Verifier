# 02 — Architecture

## The container
Everything runs inside one Docker container defined by `.devcontainer/Dockerfile`
(+ `.devcontainer/devcontainer.json` for VS Code Dev Containers, or
`docker-compose.yml` for plain Docker). It bundles:
- Python 3.12 + the packages in `requirements.txt` (Playwright, Telethon, requests,
  markdown, rich).
- Playwright's Chromium browser, plus a virtual display (Xvfb) and noVNC/websockify
  so a human can watch/drive a real browser from their laptop at
  `http://localhost:6080/vnc.html` (needed for the one-time X/Twitter login, which
  trips captchas if done headlessly).
- Node + the `claude` CLI (Claude Code) preinstalled, so the coding agent can run
  interactively in the same box that has the scraped data and the price tooling.
- The whole repo bind-mounted at `/workspace` (or `.` under `docker-compose.yml`),
  so files written inside the container (scraped JSON, chart images, reports)
  appear on the host filesystem immediately — no copying out required.

Two ways to enter it:
- **VS Code Dev Containers** (recommended): `code .` → "Reopen in Container".
- **Plain Docker**: `docker compose up -d --build`, then
  `docker compose exec app <command>`.

## The three layers of code
1. **`scripts/` — fixed, generic tools.** Never edited for a new account. These are
   parametrized scrapers and shared utilities:
   - `scrape_telegram.py` — Telethon-based Telegram channel scraper.
   - `download_tg_media.py` — pulls chart images for call-style Telegram messages.
   - `x_login.py` — one-time interactive X/Twitter login via noVNC, saves cookies.
   - `scrape_twitter.py` — Playwright-based X/Twitter timeline scraper (uses the
     saved login), resumable, paced against rate limits.
   - `prices.py` — the price oracle: Binance spot/futures klines with local caching
     and automatic spot→futures fallback (for perp-only symbols, delisted alts,
     and Binance-futures-listed commodities like `CLUSDT` oil).
   - `common.py` — shared, dependency-free helpers: account-slug directory layout,
     `.env` loading, secrets path.
   - `start-display.sh` — brings up Xvfb + x11vnc + websockify (noVNC) inside the box.
   - `md2html.py` — converts a Markdown report to a self-contained HTML file so it
     can be read in a browser without VS Code.
   - `smoke-test.sh` — verifies the container is wired up correctly (binaries,
     Python imports, Chromium launches, noVNC assets present, scripts importable,
     auth detected, Binance reachable). Expected: `PASS=14 FAIL=0`.

2. **`data/<slug>/analysis/` — per-account code, written by the AI agent.** This is
   NOT fixed code — it's authored fresh for each account being analyzed, because
   every caller posts differently (chart-only vs. text calls, different exit
   conventions, different tickers). See [`04-workflow.md`](04-workflow.md) and
   `CLAUDE.md` for what these scripts are expected to do (extract, grade, backtest).
   `data/` is entirely git-ignored, so this code and its outputs never get committed.

3. **`examples/` — two full worked reference runs**, kept in the repo (scripts +
   docs only, data git-ignored) as methodology examples for future analyses:
   - `examples/rose-margin/` — a paid Telegram channel. Full extraction harness,
     3-way grader, risk-parity backtest, the "first-entry de-bias" that overturned
     inflated alt-moonshot brags, and a working alert bot.
     `examples/rose-margin/docs/` is called out in `CLAUDE.md` as the gold standard
     for both method and honesty.
   - `examples/blockchainedbb/` — a public X account. Scraping via a logged-in
     browser, hand-grading, laddered-exit backtest.
   Both note in their READMEs that their scripts assume they're run from the
   **original repo root** (paths like `data/...`), not from inside `examples/` —
   they're for reading, not re-running as-is.

## Data flow (per account, high level)
```
X account or Telegram channel
        │  scripts/scrape_twitter.py OR scripts/scrape_telegram.py
        ▼
data/<slug>/twitter_posts.json  OR  telegram_posts.json
        │  scripts/download_tg_media.py (Telegram only; X images come with the scrape)
        ▼
data/<slug>/media/            (chart images)
        │  AI agent reads charts + text, writes data/<slug>/analysis/extract.py
        ▼
normalized calls (JSON): entry / targets / SL / dir / kind / swing / ...
        │  AI agent writes data/<slug>/analysis/grade.py, using scripts/prices.py
        ▼
graded calls (3 methods: mirror-her / mechanical / let-it-run)
        │  AI agent writes data/<slug>/analysis/backtest.py
        ▼
backtested account curves, segmented by shorts / major longs / alt longs
        │  AI agent applies the honesty checks (CLAUDE.md §5)
        ▼
data/<slug>/analysis/REPORT.md  (+ optional alert_bot.py)
```
See [`04-workflow.md`](04-workflow.md) for the step-by-step commands and
[`../CLAUDE.md`](../CLAUDE.md) for the actual grading/backtesting/honesty rules.

## What's git-ignored vs. committed
- **Committed:** `scripts/`, `.devcontainer/`, `docker-compose.yml`, `CLAUDE.md`,
  `context/` (this folder), `examples/*/*.py` and `examples/*/docs/`, top-level docs.
- **Git-ignored:** all of `data/` (scraped posts, media, price cache, per-account
  analysis code and outputs), `.env`, `*.session` (Telegram), `*storage_state*`
  (X/Twitter cookies), `__pycache__/`, `.venv/`. Credentials and any specific
  caller's data never get committed — a clone always ships a blank tool.
