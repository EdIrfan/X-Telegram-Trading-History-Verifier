# CLAUDE.md — playbook for the AI (you) running inside this container

You are Claude Code, running **inside the dev container** of a tool that
reverse-engineers paid crypto "signal" callers. A human points you at **one X
account or one Telegram channel** and asks something like *"analyze @somecaller"*.
Your job: scrape their calls, grade them against real prices, backtest a realistic
account, and deliver an **honest** verdict on whether the edge is real — then,
optionally, an **alert-only** bot. You do the analysis yourself; **the scrapers are
the only fixed code — you write the per-account extraction / grading / backtest**,
because every caller posts differently.

> You are NOT calling the Claude API from scripts. There is no `anthropic` SDK code
> in the pipeline. *You* read the charts, write the analysis files, and run them.

---

## 0. Ground rules (read once, apply always)
- **No paid APIs.** Prices come free from Binance klines (`scripts/prices.py`).
  Chart-reading is *you* looking at the image — $0.
- **Never commit secrets or data.** Everything under `data/` and `.env`,
  `*.session`, `*storage_state*` is git-ignored. Keep it that way.
- **Be honest, not promotional.** These callers brag. Your value is skepticism (§5).
  Never conclude "profitable" without surviving the bias checks. Default stance:
  **alert-only, human judgment, do NOT auto-trade** unless the numbers are
  overwhelmingly and robustly positive (they usually aren't).
- **Work per-account.** All outputs live in `data/<slug>/` (slug = the handle,
  lowercased). Put scripts you write in `data/<slug>/analysis/`.

## 1. Setup the user must have done (check, don't assume)
- **Telegram:** `.env` has `TG_API_ID/HASH/PHONE` (from my.telegram.org). First
  scrape triggers a login code in their Telegram app.
- **X/Twitter:** a session exists at `data/secrets/x_storage_state.json` — either
  from `python scripts/x_login.py` (noVNC login at http://localhost:6080/vnc.html)
  or a host-exported file dropped there.
- **You (Claude Code):** logged in once inside the container (`claude` → `/login` for a
  subscription, persisted in a named volume) or via `ANTHROPIC_API_KEY`. If a scrape needs
  a browser, run `bash scripts/start-display.sh`.

## 2. Scrape (fixed tools — parametrized, never edit for a new account)
```bash
# Telegram channel:
python scripts/scrape_telegram.py "@somecaller" --since 2025-01-01
python scripts/download_tg_media.py "@somecaller"      # chart images for call msgs
# X / Twitter account:
python scripts/x_login.py                               # once, via noVNC
python scripts/scrape_twitter.py somecaller --since 2025-01-01
```
Outputs: `data/<slug>/telegram_posts.json` or `twitter_posts.json`, and
`data/<slug>/media/` for images. Both scrapers **resume** (dedupe) — re-run to fill
gaps; X rate-limits, so several short runs beat one long one.

## 3. Extract the calls (you author this per account)
Read the messages + chart images and turn them into a normalized list of trades.
Write `data/<slug>/analysis/extract.py` (or just produce the JSON directly if it's
small). Target schema per call:
```
{ id, date, coin, binance_sym, market("spot"|"futures"),
  dir("long"|"short"), entry, targets[], sl,
  kind("setup"|"zone"|"spot"|"update"|"commentary"|"close"),
  swing(bool), note }
```
Conventions that matter:
- **Levels come from the chart image**, not the caption. Entry / targets / SL are
  what she draws. Read them off the picture.
- **Map tickers to Binance.** Use spot if listed, else USDT-M futures. Commodities
  count **iff** on Binance futures (e.g. WTI oil = `CLUSDT`); otherwise exclude.
- **Dedupe reposts** ("same chart 3 min later") but keep **changed-level** reposts
  as new trades.
- Tag `kind`: actionable setups vs. `update` (PnL brags), `commentary`, `close`
  (exits). Mine exit/close messages separately (text like *stopped out / booked /
  closing*) — her **exits are usually text, not charts**.
- Set `swing=true` for big-range moonshot longs (target +100%…+500%, wide SL).

## 4. Grade + backtest (you author this; model on examples/)
Use `scripts/prices.py` as the oracle: `ohlcv_auto(sym, start, end, "1h")` returns
`(candles, market)` and auto-falls-back spot→futures. Then:

**Grade every filled call, look-ahead-safe** (`data/<slug>/analysis/grade.py`):
- **Entry = limit fill** at her drawn level on the **first** candle that straddles it
  *after* she posts. Never touched in the window → "untriggered", skip. (No look-ahead.)
- **Max-hold:** 30d tactical / 90d swing, clipped to now.
- **Grade 3 ways** (this separated signal from noise on past callers):
  - **A — mirror her:** exit on her posted close/stop signal, else max-hold. She
    rides chart-SL wicks; do **not** auto-exit at the chart SL in method A.
  - **B — mechanical:** first touch of TP1 vs chart-SL (SL wins ties), else max-hold.
  - **C — let it run:** chart SL as initial stop; after +20% in favor, trail 25% off
    the peak. Tests whether her *entries* have edge when the exit isn't choked.
- `ret = (exit/entry − 1) × (+1 long / −1 short) − 0.5% friction`. Record
  `mfe`/`mae` (for shorts, mfe = lowest low, mae = highest high), `tp_hit`, `sl_hit`.

**Backtest a realistic account** (`data/<slug>/analysis/backtest.py`):
- **Risk-parity sizing:** notional = risk_budget ÷ her_SL_distance% (wide SL →
  smaller size; bounds the $ loss). PnL = notional × graded return.
- Event-driven & **fundable**: cap concurrent margin at equity (else skip as
  "unfunded"), ruin at $0, weekly circuit-breaker (stop trading the week after a
  −3%/−5% loss). 1× for alt moonshots; modest 2×–3× only for majors.
- Run segments separately: **shorts / major-coin longs / alt longs** — they behave
  very differently. Always include a flat-size baseline so you can see whether the
  risk rules *limit* a negative edge vs. *create* return.

## 5. The honesty checks (this is the whole point — do not skip)
Past callers looked great on the surface and were flat-to-negative underneath. Apply
the same scrutiny every time:
- **Survivorship / coverage bias:** are the chart setups her *late* re-entries while
  the brags cite the *first* entry? Re-grade the alts **from their earliest mention**
  over a long window before concluding anything about moonshots.
- **Brags are usually unrealizable wicks.** A "234×" peak on a low-float alt is an
  illiquid spike you can't sell into — realized return is a fraction of it. Grade the
  *takeable* path, not the screenshot. She's loud about the 1 winner and silent about
  the 20 that round-tripped to zero.
- **Forward-only.** Only grade falsifiable forward calls; drop "I called it" victory
  laps, promos, and position-management posts.
- **Mechanical ≠ her.** A blind chart-replay can't reproduce discretionary scaling /
  hedging / re-timing. State this as a caveat; it cuts both ways.

## 6. Deliverables
Write into `data/<slug>/analysis/`:
1. `REPORT.md` — TL;DR verdict, per-segment numbers, the bias caveats, and a clear
   recommendation (almost always: alert-only + which segments, if any, to consider).
2. The graded/backtest JSON + the scripts you wrote (so it's reproducible).
3. **Optional alert bot** (model on `examples/rose-margin/alert_bot.py`): a poller
   that surfaces new calls in real time, each tagged with the verdict for its segment.
   **Alert-only. It must never place trades.**

When you hand off `REPORT.md`, remind the user how to read it: it's on their host via the
`data/` mount, so VS Code Markdown preview, or `python scripts/md2html.py <REPORT.md>` →
open the `.html` in a browser, or `python -m rich.markdown <REPORT.md>` in the terminal.

## 7. Worked references — read these before you start
- `examples/rose-margin/` — full Telegram case: extraction harness, 3-way grader,
  risk-parity backtest, the **first-entry de-bias** that overturned the alt brags,
  and an alert bot. Its `docs/` are the gold standard for method + honesty.
- `examples/blockchainedbb/` — full X case: scraping, hand-grading, laddered-exit
  backtest. Verdict was +4.4%/yr (survivable, no real edge).

Both reached the same place: **no harvestable mechanical edge; alert-only.** Expect
that as the prior, and make the data overturn it rather than assuming a paid channel
must be good.
