# Rose Margin — Grading methodology spec (v1)

Goal: turn the 628 extracted calls + 383 close-signals into per-trade outcomes, graded
**two ways**, look-ahead-safe, so we can measure her real edge BEFORE building the $10k
backtest. Grading produces raw **price-move returns**; position sizing / leverage / weekly
stops are applied later by the backtest layer (clean separation, like the @blockchainedbb work).

Inputs:
- `data/tg_calls_extracted.json` (628 records; setup/zone/spot/update/commentary/plan/close)
- `data/tg_close_signals.json` (383 exit events: stop/close/tp)
- `data/telegram_rose.json` (post `id -> date`, to timestamp each call)
- Price oracle: Binance 1h klines via `prices.py` (+ futures fallback, see §E)

---

## A. Trade universe — what gets graded
Grade a record iff ALL:
- `binance == true`
- `kind in {"setup","zone","spot"}`  (the actionable kinds)
- `dir in {"long","short"}`
- `entry` is not null
- it is NOT a collapsed duplicate (see §B)
- for `kind=="spot"`: coin must be on Binance **SPOT** (`binance_symbols.json["spot"]`), else drop.

Excluded (kept in dataset, used only as cross-checks / context):
- `update` (29) — performance brags (MYX 3x, BEAT +448%…). Used to **validate** the grader
  (her claimed result should roughly match what we compute for that coin/window).
- `commentary` (16), `plan` (1) — theses/scenarios, no executable entry.
- `close` (3) — these are exits; folded into the close-signals, not setups.

## B. Deduplication (critical — avoids inflating trade count)
- Records whose `note` starts with `"duplicate of <id>"` are **reposts of the same trade**
  (she spams the same chart minutes apart). Collapse: keep only the primary; drop the dups.
- Records noted as re-posts with a **changed level** (e.g. "Baby short re-post (entry moved
  to 687)") are kept as **separate** trades (new entry = new decision).
- Result: ~565 raw setups/zones → estimated ~330–360 unique tradeable entries after collapse
  (exact count printed at run).

## C. Multi-leg panels (dual/triple BTC+ETH+SOL)
- These were stored as ONE record on the primary coin, with the other legs described in the
  `note` ("ETH leg: short 1619 -> 1082.47, SL 1725.34"). v1 grades the **primary coin only**.
- The embedded secondary legs are NOT graded in v1 (would need note-parsing). This undercounts
  ETH/SOL slightly; documented limitation, can be added in v2.

## D. Entry model — limit fill at her drawn entry (look-ahead-safe)
She draws a specific entry on every chart. Model it as a **limit order at `entry`**:
- From the call's post timestamp, walk 1h candles forward (up to max-hold, §H).
- Fill at `entry` on the **first candle whose [low,high] straddles `entry`**
  (fill price = `entry`). At-market calls (entry ≈ price at post) fill on the first candle;
  true limits ("buy below 69420") fill when price reaches the level.
- If `entry` is never touched within the window → **no fill**, trade skipped (counted as
  "untriggered", reported separately — she watches and doesn't always get filled).
- Rationale: keeps her targets/SL **percentages exactly as she drew them** (all relative to
  her entry), models how she actually trades (drawn entries), and only ever looks *forward*
  for the touch → no look-ahead bias. The 0.5% friction (§I) covers slippage/optimism.

## E. Price oracle
- Binance **1h** klines (wicks catch most intrabar touches; her holds are hours→weeks).
- `prices.py` currently hits SPOT (`api/v3`). Many of her coins are **perp-only** and
  `CLUSDT` (oil) is futures-only → extend with a **futures fallback**: try spot; on empty/404
  fall back to `fapi/v1/klines` (USDT-M perp). Cache both. (CLUSDT confirmed live on fapi.)
- Spot vs perp price diff is negligible for grading; use whichever the symbol lists on.

## F. Exit logic — graded TWO ways
For each filled trade, compute both:

**Method A — "follow her exactly"** (her discretion + her risk bound):
- Exit at the EARLIEST of:
  1. her first matching **close-signal** after entry — coin matches (or a coin-agnostic
     close whose `dir` matches), exit price = market at that signal's bar;
  2. price touching her **chart SL** (she does get stopped — 39 stop-signals confirm it);
  3. **max-hold** cap (§H) → exit at last candle's close.
- Exit reason recorded: `her_close` / `her_stop` / `chart_sl` / `max_hold`.

**Method B — "mechanical first-touch"** (rules-only, ignores her messages):
- Walk candles from fill; exit at FIRST touch of `targets[0]` (TP1) → win at TP1,
  or `sl` → loss at SL, whichever first; else **max-hold** close.
- Exit reason: `tp` / `sl` / `max_hold`.
- (v1 = first target only / full exit. Laddered multi-TP is a v2 toggle.)

## G. Target / SL edge cases
- `targets == []` (off-screen / moonshot / "buy & hold"): Method B has no TP → exits only on
  SL or max-hold. Method A still uses her signal. Flagged `no_target`.
- `sl == null` (zones, some moonshots): Method B has no SL → exits only on TP or max-hold;
  if also no target → mechanically ungradeable → B = max-hold only. Flagged `no_sl`.
- These lean on close-signals (Method A) for a meaningful exit.

## H. Max-hold caps
- Tactical (`swing` not set): **30 days**. Swing/moonshot (`swing == true`): **90 days**.
- Always clipped to "now" (2026-06-27) for still-open recent trades (exit = last close,
  marked `open`/`unrealized`).

## I. PnL definition (per trade, raw)
- `ret = (exit/entry - 1) * (+1 long / -1 short) - 0.5% friction`.
- This is the **price-move return** (1x). Leverage, margin sizing, risk-parity, the 2× swing
  rule (BTC+largecap only), lev caps, weekly circuit-breakers → all applied by the **backtest
  layer**, not here. Grading just establishes per-trade truth.
- Also record: `tp_hit` (bool), `sl_hit` (bool), `hold_hours`, `mfe`/`mae` (max favorable/
  adverse excursion %, for the "her ups/downs" stats in step 5).

## J. Outputs
- `data/graded_rose.json`: list of per-trade dicts
  `{id, coin, dir, kind, swing, post_date, entry, fill_date, A_exit, A_ret, A_reason,
    B_exit, B_ret, B_reason, tp_hit, sl_hit, hold_hours, mfe, mae, flags[]}`
  plus a `summary` block (counts, fill rate, win rate A/B, avg win/loss, SL-hit %, by coin).
- Untriggered (no-fill) and ungradeable records listed separately with reasons.

## K. Known limitations (documented, not hidden)
1. Secondary legs of multi-coin panels ungraded (§C).
2. Limit-fill assumes she gets her drawn entry (mildly optimistic; friction offsets).
3. 1h granularity can miss sub-hour wick touches (rare; minor).
4. Case-sensitive ticker match in close-signals misses a few lowercase mentions (§ close pass).
5. "her real entry timing" is the message timestamp; if she entered before posting, real
   fills could differ slightly.

## L. Decisions needing a nod (defaults chosen, override any)
1. **Entry** = her drawn limit level, filled on first touch (vs. blind market-at-post). _default: limit-fill_
2. **Dedup** = collapse "duplicate of"; keep changed-level reposts separate. _default: yes_
3. **Multi-leg panels** = grade primary coin only in v1. _default: yes_
4. **Max-hold** = 30d tactical / 90d swing. _default: those_
5. **Method A honors chart SL** as a hard loss bound (exit at min{her-signal, SL, max-hold}). _default: yes_
