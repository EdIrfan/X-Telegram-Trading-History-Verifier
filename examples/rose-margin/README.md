> **📁 WORKED EXAMPLE.** This is a complete, real run of the generic tool against a paid
> Telegram channel — kept as a reference for the AI and for humans. The scripts here were
> written to run from the **original repo root** (paths like `data/...`, `rose.session`),
> not from `examples/`; read them for *method*, not to re-run as-is. The current generic
> entry point is the root `README.md` + `CLAUDE.md`. Its `docs/` are the gold-standard
> methodology. Data is git-ignored, so only the scripts + docs are here.

# Crypto-signal reverse-engineering — Rose Margin (and @blockchainedbb, shelved)

This repo reverse-engineers paid crypto "signal" callers: extract every call, grade it
against real Binance prices, backtest a realistic $10k account, and decide whether the
edge is real. Two subjects:

- **Rose Margin** (`Rose_Margin🔐CryptoVipTools`, paid Telegram) — the **current focus**.
- **@blockchainedbb** (X/Twitter) — **shelved/deprioritized** after a disappointing
  +4.4% result (its files/scripts remain: `backtest_ladder.py`, `docs/REPORT.md`,
  `docs/STRATEGY_REPORT.md`, `docs/WEEKLY_PNL.md`, `data/graded_*.json`). Don't spend
  time here unless asked.

## TL;DR verdict (Rose Margin)
**No harvestable mechanical edge.** Mirroring her calls with realistic risk-parity
sizing loses 34–98% of a $10k account depending on config. Decomposition:
- **Shorts ≈ breakeven** (her better side; fast scalps).
- **BTC/ETH longs ≈ breakeven** (she scratches majors).
- **Alt-moonshot longs are −EV** — confirmed even from her *first* entry over a full
  year. Her "x5/x10" brags are mostly **unrealizable illiquid wicks** (MYX "234×" peak
  → ~+13% realizable) and she stays silent on the ~20 alts that round-trip to zero.
  Treat the multiplier brags as **subscription marketing, not signal**.

Because her edge (if any) is **discretionary**, the deliverable is an **alert-only bot**
(`alert_bot.py`) that surfaces her calls in real time, tagged with these verdicts, so a
human applies judgment. **It does not auto-trade — and the data says it shouldn't.**

Full reasoning: `docs/findings_grading.md`, `docs/backtest_results.md`.

## Pipeline (data flow)
```
Telegram (rose.session)
  ├─ scrape_telegram_update.py ─→ data/telegram_rose.json      (14.6k messages)
  ├─ download_tg_images.py     ─→ data/tg_images/              (628 call-chart imgs)
  │
  ├─ [LLM reads each chart] ───→ data/tg_calls_extracted.json  (628 calls: entry/TP/SL/dir)
  │     via extract_helper.py (next/add) + merge_batch.py
  ├─ build_close_signals.py ───→ data/tg_close_signals.json    (383 exit events)
  │
  ├─ grade_rose.py ────────────→ data/graded_rose.json         (3-way graded, per trade)
  │     prices.py = Binance klines (spot + futures fallback for CLUSDT/perp-only)
  ├─ backtest_rose.py ─────────→ data/backtest_rose.json       ($10k, 2 plans, segmented)
  ├─ debias_alt_firstentry.py ─→ data/debias_alt.json          (alt longs from 1st entry)
  └─ alert_bot.py              (live 15-min poller, alert-only)
```

## How to run (always use the venv; Telegram scripts need `.env` + `rose.session`)
```bash
.venv/bin/python scrape_telegram_update.py     # pull new Telegram messages (incremental)
.venv/bin/python download_tg_images.py         # pull new call-chart images
.venv/bin/python extract_helper.py stat        # extraction progress (628/628 done)
.venv/bin/python build_close_signals.py        # rebuild exit-signal set from messages
.venv/bin/python grade_rose.py                 # grade all calls 3 ways (writes graded_rose.json)
.venv/bin/python backtest_rose.py              # $10k backtest, both plans + baselines
.venv/bin/python debias_alt_firstentry.py      # re-grade alt longs from her first entry
.venv/bin/python alert_bot.py --once           # one poll (test);  --loop = every 15 min
```
Re-reading 628 charts is the only manual/LLM step: `extract_helper.py next 12` →
read each image → write `batchN.json` → `merge_batch.py batchN.json`.

## Key methodology decisions (see docs/ for full rationale)
- **Entry** = her drawn level as a **limit order** (fill on first touch after she posts;
  never touched → "untriggered"). Look-ahead-safe.
- **Graded 3 ways**: A = mirror her posts (close/stop signals), B = mechanical TP1-vs-SL
  first-touch, C = let-it-run (wide stop then 25% trail). 0.5% round-trip friction.
- **Sizing = risk-parity**: notional = risk_budget / her_SL_distance, so her wide SLs
  shrink the position and bound the $ loss (her premise). PnL = notional × return;
  leverage (2–3× / 1× moonshot) only affects margin & liquidation, not PnL.
- **Two plans**: A "$100" (R=$100/$200 swing, −$300/wk stop); B "$200c5" (R=$200/$400,
  −$500/wk stop). The old "$500 plan" is **dropped** — even $200 over-deploys given her
  trade frequency (Plan B hits 174 unfunded skips on a $10k account).
- **2× swing risk** only for BTC + large-caps; alts always 1×. Scope = anything on
  Binance futures or spot, crypto **or** commodity (oil via `CLUSDT`); pure CFD/
  Hyperliquid-only instruments excluded.

## Docs index
| File | What |
|---|---|
| `docs/grading_spec.md` | Grading methodology, as built (entry/exit/3 methods/edge cases) |
| `docs/findings_grading.md` | Her real ups/downs + the phase-b de-bias (the verdict) |
| `docs/backtest_rules.md` | Final $10k backtest rules (sizing, the two plans, scope, exits) |
| `docs/backtest_results.md` | $10k results, both plans, caveats |
| `docs/REPORT.md`, `STRATEGY_REPORT.md`, `WEEKLY_PNL.md` | @blockchainedbb (shelved) |

## Constraints / security
- **No paid APIs** — all chart-reading is by the LLM at $0; all prices are free Binance
  klines.
- `.env` and `*.session` are git-ignored; **Telegram credentials are never shared** —
  the user logs in themselves; `api_hash` is treated like a password.
- `data/*.json` and `data/tg_images/` are git-ignored; the derived JSON
  (`tg_calls_extracted.json`, `graded_rose.json`, etc.) are force-added so results
  are versioned.
- The alert bot is **alert-only**; it never places trades.

## Status (2026-06-27)
628/628 charts extracted · 383 exit signals · graded 3 ways · $10k backtest done ·
alt longs de-biased · alert bot built & live-tested. Conclusion: **alert-only, apply
human judgment; do not auto-trade.** Misc one-off/exploratory scripts (`probe.py`,
`classify_all.py`, `score_graded.py`, `backtest_small.py`, etc.) are scratch and not
part of the pipeline above.
