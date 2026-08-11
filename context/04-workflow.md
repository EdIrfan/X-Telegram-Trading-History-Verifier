# 04 — The per-account workflow

This is the operational sequence any AI agent (or human) follows to analyze one
account. The detailed *rules* for each step (exact grading logic, backtest sizing,
bias checks) live in [`../CLAUDE.md`](../CLAUDE.md) — this file is the sequence of
commands and artifacts, not the methodology itself.

## Step 1 — Scrape
```bash
# Telegram channel
python scripts/scrape_telegram.py "@some_signals" --since 2025-01-01
python scripts/download_tg_media.py "@some_signals"

# X / Twitter account
bash scripts/start-display.sh                 # once per container session
python scripts/x_login.py                     # once ever (see 03-setup.md)
python scripts/scrape_twitter.py some_handle --since 2025-01-01
```
Both scrapers are **resumable/dedupe on re-run** — safe to run multiple times to
fill gaps. X rate-limits aggressively; several short runs beat one long run.
Outputs land in `data/<slug>/twitter_posts.json` or `telegram_posts.json`, and
`data/<slug>/media/` for chart images.

## Step 2 — Extract calls (AI-authored, per account)
The agent reads the scraped messages and chart images and writes
`data/<slug>/analysis/extract.py` (or emits JSON directly if the dataset is small)
producing a normalized list of calls: `{id, date, coin, binance_sym, market,
dir, entry, targets[], sl, kind, swing, note}`. Key conventions (full detail in
`CLAUDE.md` §3):
- Entry/target/SL levels come from **reading the chart image**, not the caption.
- Tickers map to a Binance symbol (spot if listed, else USDT-M futures; commodities
  only if they're on Binance futures).
- Reposts of the same chart are deduped; reposts with **changed levels** are new calls.
- Calls are tagged by `kind` (setup/zone/spot/update/commentary/close) so that only
  actionable, falsifiable calls get graded.
- Exits are usually **text posts**, not charts — mine "stopped out / booked /
  closing" language separately from the chart-based entries.

## Step 3 — Grade (AI-authored, per account)
The agent writes `data/<slug>/analysis/grade.py`, using `scripts/prices.py` as the
price oracle (`ohlcv_auto` auto-falls-back spot→futures). Each call is graded
**look-ahead-safe**: entry fills at the first candle touching her level *after* the
post; calls that never trigger are marked "untriggered" and skipped. Grading runs
**three parallel methods** (mirror-her / mechanical TP-vs-SL / let-it-run-with-trail)
to separate genuine entry edge from exit-timing effects. Full formulas and exit
rules are in `CLAUDE.md` §4.

## Step 4 — Backtest (AI-authored, per account)
The agent writes `data/<slug>/analysis/backtest.py`: risk-parity position sizing
(wider stop → smaller size), a fundable/event-driven account simulation (margin
capped at equity, ruin at $0, a weekly circuit-breaker after a bad week), run
separately by segment (shorts / major-coin longs / alt longs), always alongside a
flat-size baseline for comparison. Full rules in `CLAUDE.md` §4.

## Step 5 — Apply the honesty checks
Before writing any verdict, the agent re-checks the results against known bias
traps: survivorship/coverage bias on late re-entries, unrealizable "brag" wicks on
illiquid alts, forward-calls-only discipline, and the caveat that a mechanical
backtest can't replicate discretionary exits. See `CLAUDE.md` §5 — **this step is
the actual point of the tool** and should never be skipped or rushed.

## Step 6 — Deliverables
Written into `data/<slug>/analysis/`:
1. `REPORT.md` — TL;DR verdict, per-segment numbers, bias caveats, and a clear
   recommendation (almost always: alert-only, and which segments if any are worth
   watching).
2. The graded/backtest JSON and every script the agent wrote, so the analysis is
   reproducible from scratch.
3. Optionally, `alert_bot.py` (modeled on `examples/rose-margin/alert_bot.py`): a
   poller that surfaces new calls tagged with the segment verdict. **Alert-only —
   it must never place trades.**

## Reading the report afterward
`data/` is bind-mounted to the host, so `REPORT.md` is a normal file on the host
filesystem too:
- VS Code Markdown preview (`Ctrl`/`Cmd`+`Shift`+`V`), or
- `python scripts/md2html.py data/<slug>/analysis/REPORT.md` → open the `.html`
  in any browser, or
- `python -m rich.markdown data/<slug>/analysis/REPORT.md` in a terminal, or
- any other Markdown-capable host app (Obsidian, Typora, ...).
