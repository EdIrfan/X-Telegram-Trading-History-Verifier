# Rose Margin — $10,000 backtest rules (final)

The settled rule set used by `backtest_rose.py`. These were decided with the user over
2026-06-26/27; this doc states the final form. Results: `docs/backtest_results.md`.
Grading (the per-trade returns these rules size) is specified in `docs/grading_spec.md`.

## Position sizing = RISK-PARITY
- Risk budget per trade is a fixed $ amount; **position notional = risk_budget ÷
  her_SL_distance%**.
- Wider SL (small-cap 30–40%) → smaller position; tighter SL (BTC ~5%) → bigger position.
- This **bounds the $ loss per trade** regardless of how far away her SL sits — which is
  exactly her stated premise for using wide stops.

## The two plans (start $10,000 each)
The $500-risk plan was **dropped**: she trades constantly with many concurrent positions,
so $500/trade massively over-deploys a $10k account. Even $200 runs hot (see results).

| Plan | Margin/trade | Weekly stop | Per-trade SL cap (normal / swing) |
|---|---|---|---|
| **A "$100"** (conservative) | $100 | −3% (−$300) | $100 / $200 |
| **B "$200c5"** (aggressive) | $200 | −5% (−$500) | $200 / $400 |
| ~~$500~~ | — | — | **dropped** (over-leverages the account) |

Plan B keeps the smaller $200 notional but inherits the looser risk config that the
abandoned $500 plan would have used.

## 2× swing rule — BTC + large-caps only
- Her big-range moonshot **longs** (target +100% to +500%, wide SL) are **swing buys**, not
  tactical scalps. For these, **double both the risk budget and the per-trade $ SL cap**
  (Plan A: $100→$200; Plan B: $200→$400).
- **Restricted to BTC and large-caps. Altcoins are always 1× risk and 1× leverage**, even on
  buy-&-hold/swing intent — their wide stops make 2× too dangerous.
- Eligibility computed at backtest time: `2x = (swing == true) AND (coin in LARGECAPS)`.
- `LARGECAPS = {BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LTC, TRX, LINK, AVAX, DOT, BCH}`.
- Tactical trades (BTC/ETH/SOL scalp longs & shorts, small target/SL) always stay 1×.

## Leverage
- **2×–3× max** on tactical/large-cap trades; **1× for moonshot alts** (wide 20–40% SL → low
  leverage avoids liquidation). (The @blockchainedbb backtest used 5×; Rose's SL distances
  are far larger, so leverage is much lower.)
- Risk-parity already caps the $ loss; leverage only affects margin use and liquidation
  distance, not the PnL — PnL = notional × graded return.

## Hold model
- **Variable hold**: enter at her drawn entry, exit on the FIRST of {her target, her SL, her
  posted close} along the hourly price path (her trades run minutes → weeks).
- Her force-close messages (matched by coin + direction + time) drive the mirror-her exit.

## Strategies graded (per plan)
Each plan is run four ways, mapping the three grading lenses onto segments:
- **CORE-only** — shorts + large-cap longs, mirror-her exits (the defensible subset).
- **SEGMENTED** — CORE + alt longs on a let-it-run (Method C) overlay.
- **all-A** — mirror her on everything.
- **all-B** — mechanical TP/SL on everything.

## Account mechanics (event-driven & fundable)
- Margin is capped at the live account: if `deployed + new_margin > equity`, the trade is
  **unfunded** (skipped, counted) — models real concurrent-position limits.
- **Ruin** at equity ≤ $0 (blown).
- **Weekly circuit-breaker**: once a calendar week's realized PnL hits the plan's stop
  (−$300 / −$500), the rest of that week's trades are **skipped** (`wkskip`).

## Scope — what instruments count
- Anything on **Binance futures OR Binance spot**, crypto **or** commodity.
- Commodities are **in scope if listed**: WTI crude trades via the live **`CLUSDT`**
  perpetual (her #OIL/#CL calls, ids 51904/52134/52139/52140). `BRENT`/`USOIL`/`WTI`
  tickers are not on Binance and are excluded. (Caveat: id 52134 was charted on Brent, so
  grading it against CLUSDT/WTI carries the small Brent–WTI spread error; the CL ids are exact.)
- A `kind=="spot"` ("buy spot") call is only actionable if the coin is on Binance **spot**;
  futures-only → dropped (leveraged `setup` calls trade on futures, so futures-only is fine).
- Excluded only when there is **no Binance listing at all** (pure CFD / Hyperliquid-only).

## Exit / close signals (text pass) — `data/tg_close_signals.json`
- Built by `build_close_signals.py` from the 14,610 Telegram messages: her **setups** are
  chart images, but her **exits** are almost always text-only.
- **383 exit events**: `stop` (SL hit, 39) | `close` (manual flat, 334) | `tp`
  (book/take profit, 10). Fields `{id, date, action, dir, coins[], pct, text}`.
- Coins from #hashtags + an UPPERCASE plain-text fallback for majors ("closed BTC at 88k").
  33 are coin-agnostic general exits ("Close shorts", "Stopped out", "cut loss").
- Grader matching (variable hold): for each setup (coin, dir, post-date), the exit is the
  FIRST close-signal where the coin matches (or a direction-matching coin-agnostic close)
  dated AFTER the setup; else fall back to mechanical first-touch and/or the max-hold cap.
- Caveat: case-sensitive ticker match (avoids op/re/arb false hits), so a few lowercase
  mentions miss coin attribution → harmless, they fall back to a mechanical exit.
