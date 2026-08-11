# 07 — Glossary

- **Call** — a single trade idea posted by the account: a coin, direction
  (long/short), and usually entry/target/stop levels, drawn on a chart or stated
  in text.
- **Slug** — the filesystem-safe folder name for an account, e.g. `@Some_Signals`
  → `some_signals`. See `scripts/common.py:slug()`.
- **Kind** (of a call) — classification tag: `setup`/`zone`/`spot` (actionable),
  `update` (PnL brag on an existing position), `commentary` (no trade), `close`
  (an exit signal). Only actionable kinds get graded as forward calls.
- **Swing** — a call tagged as a big-range, moonshot-style long (large target,
  wide stop), as opposed to a tactical/short-hold trade. Affects max-hold window
  and position sizing in the backtest.
- **Untriggered** — a call whose entry price was never touched within the trading
  window after it was posted; excluded from grading (no fill, no result).
- **Look-ahead-safe** — a grading rule that only uses price data *after* the call
  was posted to decide fills/outcomes, never data from before the post (which
  would let the grader "cheat" by knowing the future).
- **Grading method A / mirror-her** — exit on the account's own posted close/stop
  signal, else hold to the max-hold deadline. Tests the account's *actual* results,
  including any wick-riding past the drawn stop.
- **Grading method B / mechanical** — exit on the first mechanical touch of either
  TP1 or the drawn stop-loss (SL wins simultaneous touches), else max-hold. Tests
  a blind, rules-only replay of the calls.
- **Grading method C / let-it-run** — use the chart stop as the initial stop, then
  trail 25% off the peak once +20% in favor is reached. Tests whether the entries
  have edge when exits aren't artificially choked.
- **MFE / MAE** — Maximum Favorable / Adverse Excursion: the best/worst price the
  trade reached during its window (best = highest high for longs, lowest low for
  shorts; adverse is the reverse), independent of when it was actually exited.
- **Risk-parity sizing** — position size set so that a fixed dollar risk budget is
  spent regardless of how wide the stop is: `notional = risk_budget / SL_distance%`.
  A wider stop produces a smaller position, bounding the dollar loss per trade.
- **Unfunded (backtest)** — a call that's skipped in the backtest because opening
  it would exceed the account's available margin at that point in time (the
  simulation caps concurrent margin at current equity rather than allowing
  unlimited leverage).
- **Weekly circuit-breaker** — a backtest rule that stops opening new trades for a
  week following a bad week (e.g. −3%/−5% loss), simulating a disciplined trader
  pausing after a drawdown.
- **Survivorship / coverage bias** — the risk that graded results overstate the
  edge because only "clean" chart setups were captured, missing earlier/messier
  entries into the same moves; mitigated by re-grading from the account's
  *earliest* mention of a coin, not just the polished chart post.
- **Realized vs. peak (brag) return** — the distinction between the price a trade
  could actually have been exited at (realized, on liquid volume) versus the
  best price the chart ever touched (peak/brag, often an unrealizable illiquid
  wick on a low-float altcoin).
- **Alert-only** — the default and (so far) only recommended deployment mode: a
  bot that notifies a human of new calls and their backtested verdict, but never
  places trades itself.
- **klines** — Binance's term for OHLCV candlestick data, fetched via
  `scripts/prices.py` from the public spot (`api.binance.com`) or USDT-M futures
  (`fapi.binance.com`) REST APIs.
- **storage_state** — Playwright's term for a saved browser session (cookies +
  local storage), used here to persist an X/Twitter login across scraper runs.
