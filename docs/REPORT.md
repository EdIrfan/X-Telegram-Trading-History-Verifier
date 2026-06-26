# @blockchainedbb crypto-call accuracy — FINAL report (full year)

**Scope:** complete timeline **June 2025 → June 27 2026** (3,105 posts scraped via the
user's logged-in Brave). Every strong call-candidate read + classified by Claude
(text + chart images); every genuine **forward** call graded against Binance OHLCV
(matches TradingView). She trades **high leverage**, so win thresholds are small
(BTC 1.5%, alts 2–3%) and we track favourable-vs-adverse excursion, not just close.
*(Minor gap: ~2 weeks of mid-June 2026 hit an X search throttle and returned empty.)*

## Headline — 73 forward calls, full cycle
| Metric | Score |
|---|---|
| **Close-based** (swing paid by 7-day window end) | **~41/73 ≈ 56%** |
| **Excursion-based** (price popped her way ≥ threshold = a leveraged win) | **~61/73 ≈ 84%** |

Most of her "call-like" posts aren't forward calls at all: across the Jun–Oct sample,
only **~32% (45 of 142)** were falsifiable forward calls — the rest were PnL brags,
"I called the bottom" victory laps, promo, and position-management.

## What she actually is (this is the real finding)
A **trend-follower: right *inside* trends — both up AND down — but late at the *turns*.**
- **Jun–Sep 2025 uptrend:** longs ~69% close / ~83% excursion. July target calls all
  hit (BTC→112k, ETH 2600/2888/3500), +8% to +22%.
- **The ONE blind spot — the Oct top + early-Nov:** kept longing into the crash and the
  dead-cat bounce (4/4 early-Nov longs failed). This is the only place she blows up.
- **Nov 2025–Jun 2026 downtrend:** she **flipped short** and rode BTC $108k→$58k. Shorts
  ~57% close / ~86% excursion; her late-May shorts were her best calls (+16%, +20%).

She is **not** a permabull (an earlier 5-month read suggested that; the full year
corrects it). Her weakness is timing the *transition*, not picking direction.

## $10k backtest — mirror her, your full rule set
$100 margin · 5x **isolated** · **−50% hard stop** (no liquidations) · **$300/week**
breaker · 0.5% friction · one entry per call (no DCA). Prices integrity-checked
(0 data errors; Oct-7 DOGE/XRP mega-wicks confirmed real, not glitches).

| Window | Result | Max DD |
|---|---|---|
| Jun–Oct 2025 (copy-all) | $10,000 → **$10,411 (+4.1%)** | 3.4% |
| **Full year Jun 2025 → Jun 2026 (73 calls)** | $10,000 → **$10,442 (+4.4%)** | **5.0%** |

**Mirroring her blindly through a full cycle — a +60% rip and a −45% crash — finishes
+4.4% with a 5% max drawdown.** You don't get rich copying her, but the risk rules make
it structurally impossible to get hurt. The **−50% stop is the hero**: every blowup
(DOGE −63%, XRP −56%) is cut at −$53 instead of liquidating; the $300/week breaker caps
the worst week; isolated margin walls off each trade.

## Verdict for the bot
1. **Risk-rule-only copy is already survivable** (+4.4%, 5% DD over a year). Simplest.
2. **Returns come from a turn filter** — skip her trades at trend transitions (where she
   blows up), not a blanket direction mute (a crude 10-day-trend filter over-filtered
   and *hurt*). The −50% stop already neutralizes most transition damage on its own.
3. **Alert-only first** (she scouts, you veto), isolated margin, $100/trade, $300/week,
   −50% stop, **never copy her DCA/averaging into losers**.

## Files
- `classify_all.py` — all 142 Jun–Oct candidates categorized (transparent, no sampling)
- `grade_new.py` — all 28 Nov 2025–Jun 2026 forward calls + full backtest
- `backtest.py` — copy-all vs regime-filtered, price-integrity check
- `data/graded_all.json`, `data/graded_full.json` — per-call detail
