# Example — @blockchainedbb (X / Twitter)

> **📁 WORKED EXAMPLE.** A complete real run of the generic tool against a public X
> account. Kept as a reference for *method*. These scripts were written to run from the
> **original repo root** (paths like `data/posts.json`), not from `examples/` — read them
> to see how the X path works, not to re-run as-is. Data is git-ignored. The current
> generic entry point is the root `README.md` + `CLAUDE.md`.

## What this was
A full-year (Jun 2025 → Jun 2026) accuracy + backtest study of the X caller
**@blockchainedbb**. Posts were scraped by attaching Playwright to a logged-in Brave
over CDP (the container now does this more cleanly via `scripts/x_login.py` +
`scripts/scrape_twitter.py`), then every falsifiable **forward** call was graded against
Binance OHLCV and run through a realistic $10k backtest.

## Verdict
**+4.4%/yr** mirroring her blindly (5% max drawdown) — survivable but **no real edge**.
She's a trend-follower: right inside trends, late at the turns; her shorts in the
2025–26 downtrend were her best calls. The risk rules (−50% hard stop, isolated margin,
weekly breaker) make it *hard to get hurt* but don't manufacture alpha. Deprioritized.

## Files
- `scrape_posts.py`, `launch_brave_debug.sh`, `probe.py`, `test_connect.py` — scraping
- `classify_all.py`, `grade_new.py`, `extract_llm.py`, `score_graded.py`, `analyze.py` — grading
- `backtest.py`, `backtest_ladder.py`, `backtest_precise.py`, `backtest_small.py`, `weekly_table.py` — backtests
- `docs/REPORT.md`, `docs/STRATEGY_REPORT.md`, `docs/WEEKLY_PNL.md` — write-ups
