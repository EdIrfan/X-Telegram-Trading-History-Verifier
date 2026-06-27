# Rose Margin — grading methodology (as built)

How the 628 extracted calls + 383 close-signals become per-trade outcomes, graded
**three ways**, look-ahead-safe. Grading produces raw **price-move returns** (1x, after
friction); position sizing / leverage / weekly stops are applied separately by the
backtest layer (`backtest_rose.py`) — clean separation, same as the @blockchainedbb work.

Implemented in `grade_rose.py` → `data/graded_rose.json`. **413 of 418 filled trades
graded** (5 never touched their entry = untriggered). Results: `docs/findings_grading.md`.

Inputs:
- `data/tg_calls_extracted.json` (628 records; setup/zone/spot/update/commentary/plan/close)
- `data/tg_close_signals.json` (383 exit events: stop/close/tp)
- `data/telegram_rose.json` (post `id → date`, to timestamp each call)
- Price oracle: Binance 1h klines via `prices.py` (spot + futures fallback, see §E)

---

## A. Trade universe — what gets graded
A record is graded iff ALL hold:
- `binance == true`
- `kind in {"setup","zone","spot"}` (the actionable kinds)
- `dir in {"long","short"}`
- `entry` is not null
- it is not a collapsed duplicate (§B)
- for `kind=="spot"`: the coin must be on Binance **spot** (`binance_symbols.json["spot"]`),
  else dropped — you can't buy spot a futures-only listing.

Excluded (kept in the dataset as cross-checks / context, never graded as trades):
- `update` (29) — performance brags (MYX 3x, BEAT +448%…). Used to **sanity-check** the
  grader (her claimed result should roughly match what we compute for that coin/window).
- `commentary` (16), `plan` (1) — theses/scenarios, no executable entry.
- `close` (3) — these are exits; folded into the close-signals, not setups.

## B. Deduplication
- Records whose `note` starts with `"duplicate of <id>"` are **reposts of the same trade**
  (she spams the same chart minutes apart). Collapsed: keep the primary, drop the dups.
- Reposts with a **changed level** ("Baby short re-post, entry moved to 687") are kept as
  **separate** trades — a new entry is a new decision.
- After collapse: **418 unique entries reached the fill model; 413 filled and were graded.**

## C. Multi-leg panels (dual / triple BTC+ETH+SOL)
- Stored as ONE record on the primary coin, the other legs in the `note`
  ("ETH leg: short 1619 → 1082.47, SL 1725.34"). We grade the **primary coin only**.
- The embedded secondary legs are NOT graded (would need note-parsing) — this slightly
  undercounts ETH/SOL. Documented limitation (§K).

## D. Entry model — limit fill at her drawn entry (look-ahead-safe)
She draws a specific entry on every chart. We model it as a **limit order at `entry`**:
- From the call's post timestamp, walk 1h candles forward (up to max-hold, §H).
- Fill at `entry` on the **first candle whose [low, high] straddles `entry`** (fill price
  = `entry`). At-market calls (entry ≈ price at post) fill on the first candle; true limits
  ("buy below 69420") fill when price reaches the level.
- If `entry` is never touched in the window → **no fill**, trade skipped and reported as
  "untriggered" (5 of 418 — she watches and doesn't always get filled).
- Why: keeps her targets/SL **exactly as she drew them** (all relative to her entry),
  models how she actually trades, and only ever looks *forward* for the touch → no
  look-ahead bias. The 0.5% friction (§I) absorbs slippage/optimism.

## E. Price oracle
- Binance **1h** klines (wicks catch most intrabar touches; her holds run hours → weeks).
- `prices.py` provides `ohlcv_auto(symbol, …)`: try **spot** (`api/v3/klines`); on empty/404
  fall back to **USDT-M futures** (`fapi/v1/klines`). Many of her coins are perp-only, and
  `CLUSDT` (WTI oil) is futures-only — confirmed live on fapi. Both markets are cached
  (`data/price_cache/hist_<sym>_1h.json`); spot-vs-perp price diff is negligible for grading.

## F. Exit logic — graded THREE ways
For each filled trade we compute all three exits over the same 1h walk:

**Method A — "mirror her posts"** (her discretion + her risk bound):
- Exit at the EARLIEST of:
  1. her first matching **close-signal** after entry — coin matches (or a coin-agnostic
     close whose `dir` matches); exit price = that bar's close;
  2. **max-hold** cap (§H) → exit at the last candle's close.
- She holds **through chart-SL wicks** unless she actually posts a stop, so Method A does
  **not** auto-exit on the chart SL (an earlier version did; removed — it mis-scored her).
  When she posts a stop it lands as a close-signal (`her_stop`) via case 1.
- Exit reasons observed: `her_close` 299, `her_stop` 72, `max_hold` 42.

**Method B — "mechanical first-touch"** (rules-only, ignores her messages):
- Walk from fill; exit at the FIRST touch of `targets[0]` (TP1) → win, or `sl` → loss,
  whichever comes first (**SL wins ties**); else **max-hold** close.
- Exit reasons: `sl` 292, `max_hold` 77, `tp` 44. (v1 = first target / full exit; a
  laddered multi-TP exit is a possible v2 toggle.)

**Method C — "let it run"** (tests whether her *entries* have edge if the exit isn't choked):
- Initial stop = her chart SL. Once price moves **+20% in favor (ACT)**, switch to a **25%
  trailing stop off the running peak**; else max-hold. Illustrative, **NOT** parameter-tuned.
- Reasons: `init_sl` / `trail` / `max_hold`.

## G. Target / SL edge cases
- `targets == []` (off-screen / moonshot / "buy & hold"): Method B has no TP → exits only on
  SL or max-hold; Methods A and C still work. Flagged `no_target`.
- `sl == null` (zones, some moonshots): Method B has no SL → exits only on TP or max-hold;
  if also no target → mechanically ungradeable (B = max-hold only). Flagged `no_sl`.
  These lean on Method A (her close-signals) for a meaningful exit.

## H. Max-hold caps
- Tactical (`swing` not set): **30 days**. Swing / moonshot (`swing == true`): **90 days**.
- Always clipped to "now" (2026-06-27) for still-open recent trades (exit = last close,
  marked `open` / `unrealized`).

## I. PnL definition (per trade, raw)
- `ret = (exit/entry − 1) × (+1 long / −1 short) − 0.5% friction`.
- This is the **price-move return at 1x**. Leverage, margin sizing, risk-parity, the 2×
  swing rule (BTC + large-cap only), lev caps and weekly circuit-breakers are all applied by
  the **backtest layer**, never here. Grading just establishes per-trade truth.
- Also recorded per trade: `tp_hit`, `sl_hit`, `hold_h`, and `mfe`/`mae` (max favorable /
  adverse excursion %). For shorts, mfe uses the lowest low and mae the highest high.

## J. Outputs
- `data/graded_rose.json`: `summary` block + `trades[]` of per-trade dicts
  `{id, coin, dir, kind, swing, post_date, entry, fill_date,
    A_ret/A_reason/A_hold_h, B_ret/B_reason, C_ret/C_reason/C_hold_h,
    tp_hit, sl_hit, mfe, mae, flags[]}`, plus `skipped` (untriggered + ungradeable).
- `summary` reports counts, fill rate, win rate and avg win/loss per method, B's TP/SL-hit
  %, and breakdowns by direction and by segment (short / large-cap long / alt long).

## K. Known limitations (documented, not hidden)
1. Secondary legs of multi-coin panels are ungraded (§C) — slightly undercounts ETH/SOL.
2. Limit-fill assumes she gets her drawn entry (mildly optimistic; friction offsets).
3. 1h granularity can miss sub-hour wick touches (rare; minor).
4. Close-signal ticker match is case-sensitive (avoids op/re/arb false hits), so a few
   lowercase mentions miss coin attribution → those fall back to mechanical exits.
5. "Her real entry timing" is the message timestamp; if she entered before posting, real
   fills could differ slightly.

## L. Settled decisions (these were defaults; all confirmed and kept)
1. **Entry** = her drawn limit level, filled on first touch (not blind market-at-post).
2. **Dedup** = collapse "duplicate of"; keep changed-level reposts separate.
3. **Multi-leg panels** = grade the primary coin only.
4. **Max-hold** = 30d tactical / 90d swing.
5. **Method A does NOT honor the chart SL** — she rides wicks; only her posted stop exits.
   (This reverses the original draft, which auto-exited Method A at the chart SL.)
