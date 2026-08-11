# 01 — Overview

## What this is
**X-Telegram-Verifier** (repo name on GitHub: `X-Telegram-Trading-History-Verifier`)
is a self-contained dev container that reverse-engineers paid crypto "signal"
callers. Point it at **one X (Twitter) account or one Telegram channel** and an AI
coding agent running *inside* the container will:

1. Scrape every post/message from that account.
2. Read the chart images and extract structured trade calls (entry/targets/stop).
3. Grade each call against real historical Binance prices, look-ahead-safe.
4. Backtest a realistic, riskmanaged trading account off those grades.
5. Apply a set of honesty/bias checks (see [`../CLAUDE.md`](../CLAUDE.md) §5).
6. Write an honest verdict report — almost always **"alert-only, don't auto-trade"**.
7. Optionally build an alert-only bot that surfaces new calls tagged with the verdict.

## Why it exists
Paid crypto signal channels/accounts make big claims ("x10!", "94% win rate!").
This tool exists to test those claims against reality, cheaply, and skeptically.
Two worked examples (`examples/rose-margin`, `examples/blockchainedbb`) both
concluded **no harvestable mechanical edge → alert-only**. That's the expected
prior for any new account too — the tool is built to make the *data* overturn
that prior, not to assume a paid channel must be good.

## Key design decisions
- **No paid APIs.** Prices come from free Binance klines. Chart-reading is done by
  the AI agent looking at the image — no OCR/vision API bill.
- **The scrapers are the only fixed code.** Every caller formats calls differently
  (chart annotations vs. text, different tickers, different exit conventions), so
  extraction/grading/backtesting scripts are **written per-account by the AI agent**,
  not hardcoded once for all callers.
- **Everything account-specific lives under `data/`**, which is entirely git-ignored.
  A fresh clone of this repo ships the *tools*, never any caller's scraped data or
  analysis output.
- **The AI runs inside the container**, not as an external API call from a script.
  There's no `anthropic`/LLM SDK code in the pipeline — a human opens a terminal or
  chat interface inside the container and drives the agent interactively.
- **Alert-only by construction.** Nothing in this repo is wired to place real trades.
  The deliverable bot only surfaces calls with a verdict attached.

## Who this is for
- A person who subscribes to (or is considering subscribing to) a paid trading
  signal service and wants an honest, data-driven answer on whether it's worth it.
- Not a general backtesting framework — it's specifically built around "someone
  posts a chart/call on social media, does following it make money."
