# @blockchainedbb crypto-call accuracy — report

**Scope:** ALL 142 strong call-candidate posts from **June–October 2025** (every post
that names a coin + has a direction/price), classified and — for genuine forward
calls — graded by Claude reading text + chart images, verified against Binance OHLCV
(matches TradingView) over a **7-day window**. She trades **high leverage**, so win
thresholds are small (BTC 1.5%, alts 2–3%) and we track favourable-vs-adverse
excursion, not just close. *(Coverage extends as Nov 2025→Jun 2026 finishes scraping.)*

## What her posts actually are (142 classified)
| Category | Count | |
|---|---|---|
| **Genuine forward CALL** | **45** | the only falsifiable ones (32%) |
| PnL brag / "target completed" | 35 | retroactive |
| Commentary / watchlist / vague | 26 | |
| "I called the bottom/top" victory lap | 13 | retroactive |
| Closing / managing a position | 10 | |
| Conditional ("if X then Y") | 5 | |
| Multi-week/month horizon | 5 | outside 7d test |
| Promo (Discord / ticker dump) | 4 | |

**Only ~1 in 3 chart-tagged posts is an actual forward call** — the rest is
retroactive bragging and noise. That ratio matters: her timeline *looks* more
accurate than her forward calls are.

## Accuracy of the 45 forward calls (7-day window)
| Metric | Score |
|---|---|
| **Close-based** — swing paid by window end | **26/45 = 57.8%** |
| **Excursion-based** — price popped her way ≥ threshold (a leveraged win) | **36/45 = 80.0%** |

## The real signal: regime + excursion asymmetry
| Regime | Close | Excursion | Adverse excursion (leverage killer) |
|---|---|---|---|
| Bull / normal (Jun – Oct 2) | 25/36 ≈ **69%** | 30/36 ≈ **83%** | small, ~ −1% to −5% (leverage-safe) |
| Oct 2025 crash (Oct 6–28) | 1/9 ≈ **11%** | 6/9 | **−6% to −63%** (liquidation) |

The crash "excursion wins" are illusory under leverage — the small favourable pop
(+1–3%) is wiped out by the adverse move (DOGE −63%, XRP −56%, ETH −21%, BTC −17%)
before it can be banked.

## Behavioural findings
1. **Trend-following permabull.** In uptrends her leveraged longs have great
   asymmetry (fav +6–25% vs adv −1–2%). July target calls all hit (BTC→112k, ETH
   2600/2888/3500), +8% to +22%.
2. **Does not call tops; weak at shorts (1/4 short calls).** Sep shorts too early;
   she longed straight into the October crash, buying the dip all the way down.
3. **Two-thirds of her "calls" are retroactive** PnL brags / victory laps / promo —
   not forward, falsifiable calls.

## UPDATE — crash period Nov 2025 → Mar 2026 (corrects the thesis)
Extended the scrape into the crash (BTC ~$108k → ~$68k). Graded **all 18 forward
calls** in this window. Key correction to the earlier read:
- She **flipped SHORT** (14 of 18 calls) and her shorts **caught the downtrend**:
  8/14 close-based (57%), ~86% on excursion (nearly every short went green
  intra-window). She is **NOT** a pure permabull.
- Her early-Nov **longs all failed** (4/4) — she was late letting go of the bounce.
- **Corrected thesis: trend-follower, right *inside* trends (up and down), late at
  the *turns*.** The only real blind spot is the transition (Oct top, early-Nov
  bounce) — once committed to a direction she rides it well.

## Full backtest — $10k mirror, Jun 2025 → Mar 2026 (63 calls)
Rules: $100 margin, 5x **isolated**, **−50% hard stop** (no liquidations), **$300/week**
breaker, 0.5% friction. Price data integrity-checked (0 errors; Oct-7 DOGE/XRP
mega-wicks confirmed real).
```
START $10,000 -> END $10,319  (+3.2%)   over 10 months incl. a ~-35% BTC crash
trades=63  wins=34  stops=9   max drawdown 5.0%   peak $10,773
```
Blindly mirroring her through the entire crash finishes **+3.2% with 5% max DD** —
you don't get rich, but the risk rules make it structurally impossible to get hurt.
(`backtest.py` copy-all alone, Jun–Oct, was +4.1% / 3.4% DD.)

## Implication for a follow / alert bot
Her edge is a **trend-follow signal**, not a flat hit-rate — strong inside trends
(both directions), weak at turns. Two designs both work:
1. **Risk-rule only (no filter):** the −50% stop + isolated + $300/week makes even
   blind copying survivable (+3.2%, 5% DD over 10 months). Simplest.
2. **Add a regime/turn filter** to skip her wrong-way trades at transitions for
   better returns. (Note: a *crude* 10-day-trend filter over-filtered and hurt —
   needs to target the turns specifically, not blanket-mute one direction.)
Alert-only (she scouts, you veto) remains the safest starting point.

## Method & caveats
- n=45 forward calls; 7-day window (matches her 2–3 day swing style).
- Leverage win thresholds: BTC 1.5%, ETH/BNB 2%, SOL/XRP/LTC/LINK 2.5%, DOGE 3%.
- "Buy the dip / accumulate" graded *long* (she expects net-higher in window).
- **Coverage Jun–Oct 2025 so far; Nov 2025→Jun 2026 scraping now** — will be
  appended (and will stress-test the regime finding against the full drawdown).
- Full per-call detail: `data/graded_all.json` (all 45) and `classify_all.py`
  (every one of the 142 classifications, transparent — nothing cherry-picked).
