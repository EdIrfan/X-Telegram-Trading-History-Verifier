# X-Telegram-Verifier 🔬

Point it at **any X (Twitter) account or any Telegram channel** that posts crypto
"signals", and an AI (Claude Code, running *inside* the container) will scrape every
call, grade it against **real Binance prices**, backtest a realistic account, and tell
you — honestly — whether the edge is real. Then, if you want, it builds you an
**alert-only** bot.

It's a self-contained dev container: a real browser you log into once (viewable in
your laptop browser via noVNC), the Telegram + price tooling, **and Claude Code +
the VS Code extension preinstalled**, so the whole "scrape → read charts → grade →
backtest → report" loop happens in one box. The scrapers are fixed; the AI writes the
per-account analysis (every caller formats calls differently — see `CLAUDE.md`).

> **Why "free-ish":** there are **no paid data APIs** — prices are free Binance
> klines and chart-reading is just the model looking at the image. The only cost is
> running Claude Code, which you can do on a **$20/mo Claude Pro subscription**
> (log in once inside the container — no per-token cost) instead of a metered API key.

---

## What you need
- **Docker** (Desktop or Engine).
- **VS Code** with the *Dev Containers* extension — *recommended path*. (Or use plain
  Docker; see [below](#plain-docker-no-vs-code).)
- **Claude Code auth** — you log in **once inside the container** (it persists in a named
  volume across rebuilds). Either:
  - a **Claude Pro/Max subscription** ($0/token): run `claude`, then `/login`, **or**
  - an **`ANTHROPIC_API_KEY`** (pay-per-token) — set it in your host shell (passed through)
    or `export` it inside the container.
- For **Telegram**: a free `api_id`/`api_hash` from <https://my.telegram.org>.
- For **X/Twitter**: just an X account you can log into once.

## Quick start (VS Code Dev Container)
```bash
git clone <your-fork-url> X-Telegram-Verifier
cd X-Telegram-Verifier
cp .env.example .env          # fill in Telegram creds &/or API key (see comments)
code .                        # VS Code → "Reopen in Container" when prompted
```
The container builds (browser + Claude Code + tools). Once inside, open the terminal:

```bash
# --- Telegram channel ---
python scripts/scrape_telegram.py "@some_signals" --since 2025-01-01
python scripts/download_tg_media.py "@some_signals"

# --- X / Twitter account ---  (one-time login, viewable via noVNC)
bash scripts/start-display.sh           # then open http://localhost:6080/vnc.html
python scripts/x_login.py               # log into X in that noVNC browser tab, once
python scripts/scrape_twitter.py some_handle --since 2025-01-01
```
Then just **open Claude Code** (the sidebar, or `claude` in the terminal) and say:

> *"Analyze @some_handle"* — or — *"Analyze the @some_signals telegram channel I scraped."*

It follows `CLAUDE.md`: extracts the calls, grades them three ways, backtests a
realistic account, applies the bias checks, and writes a report into
`data/<account>/analysis/` — then offers to build an alert-only bot.

### Windows
Works via **Docker Desktop** (with the **WSL2** backend) + VS Code Dev Containers — the
same `code .` → *Reopen in Container* flow. Two tips: clone into your **WSL2** filesystem
(e.g. `\\wsl$`) for speed, and don't worry about line endings — `.gitattributes` forces LF
so the in-container shell scripts run. Auth is the same `claude` → `/login` inside the box
(no host `~/.claude` mounting needed, so Windows' lack of `$HOME` is a non-issue).

## Plain Docker (no VS Code)
```bash
cp .env.example .env
docker compose up -d --build
open http://localhost:6080/vnc.html     # for the X login
docker compose exec app python scripts/scrape_telegram.py "@some_signals"
docker compose exec app claude          # the AI, inside the container
```

---

## The honest part (please read)
This tool exists because **most paid callers are flat-to-negative under scrutiny**,
and the marketing ("x5! x10!") is usually **unrealizable illiquid wicks**. The AI is
instructed (in `CLAUDE.md`) to *assume no edge* and make the data prove otherwise:
forward-calls-only, survivorship/coverage de-bias, realized-not-peak returns. The
default deliverable is **alert-only** — surface the calls, tag them with the verdict,
let a human decide. **It does not auto-trade, and you shouldn't wire it to.**

## Reading the reports
The AI writes its findings as Markdown into `data/<account>/analysis/` (e.g. `REPORT.md`).
Because `data/` is **bind-mounted to your host**, those files also appear in the repo
folder *on your computer* — so you're never stuck reading raw Markdown in a container:
- **VS Code** — open the `.md` and hit Markdown preview (`Ctrl`/`Cmd`+`Shift`+`V`).
- **Any browser** (no VS Code) — convert to a self-contained HTML and open it on your host:
  ```bash
  python scripts/md2html.py data/<account>/analysis/REPORT.md   # writes REPORT.html
  ```
- **In the terminal** (headless) — `python -m rich.markdown data/<account>/analysis/REPORT.md`.
- Or just open the `.md` in any host app (Obsidian, Typora, …) — it's a normal file.

The finished verdict reports are also **published (committed) under `Reports/`**, one folder
per account — `Reports/<Platform>-<handle>/REPORT.md` (+ `.html`), e.g.
`Reports/Telegram-CryptoAman_Free/`. That's the only thing checked into git from a run: the
**raw scrapes, caches and credentials under `data/` stay local and git-ignored**.

## Limitations
- **X rate-limits hard.** The scraper paces + backs off and **resumes** on re-run;
  expect to run it a few times to fill a long history. Patience > one big run.
- **Telegram** needs you to actually be a member of the channel you scrape.
- **1-hour price granularity** can miss sub-hour wicks (rare; minor).
- Chart-reading quality depends on the model; ambiguous charts get flagged.

## Layout
```
scripts/         fixed, generic tools (scrapers + Binance price oracle + helpers)
  scrape_twitter.py / x_login.py / scrape_telegram.py / download_tg_media.py
  prices.py / common.py / start-display.sh / md2html.py / smoke-test.sh
.devcontainer/   the container (Dockerfile + devcontainer.json)
docker-compose.yml   plain-Docker alternative
CLAUDE.md        the AI's playbook — the analysis workflow + honesty rules
examples/        two full worked cases (data git-ignored):
  rose-margin/      Telegram — extraction, 3-way grader, de-bias, alert bot
  blockchainedbb/   X/Twitter — scraping, grading, laddered backtest
Reports/         published verdict reports — COMMITTED (Reports/<Platform>-<handle>/REPORT.md)
data/            everything runtime (per-account scrapes, caches, outputs) — git-ignored
```

## Security
- `.env`, `*.session`, and `*storage_state*` are git-ignored; **your credentials
  never leave your machine** — you log into Telegram/X yourself, in your container.
- All raw scrapes, caches and intermediate outputs under `data/` are git-ignored — a
  clone ships the **tools**, never a caller's raw data or your credentials.
- The exception is the **published verdict reports** under `Reports/`, which *are*
  committed on purpose — they hold the analysis + recommendation only (no credentials,
  no raw scrape), so the conclusions can be versioned and shared.
- The optional alert bot is **alert-only** by construction.
