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

## Implication for a follow / alert bot
Her edge is a **regime trade**, not a flat hit-rate: real in confirmed uptrends
(leverage-safe asymmetry), catastrophic once trend breaks. A bot must **mute her
longs when trend structure breaks / market is in a downtrend**, or it inherits the
Oct-crash blowups. Alert-only with a market-regime veto = right design.

## Method & caveats
- n=45 forward calls; 7-day window (matches her 2–3 day swing style).
- Leverage win thresholds: BTC 1.5%, ETH/BNB 2%, SOL/XRP/LTC/LINK 2.5%, DOGE 3%.
- "Buy the dip / accumulate" graded *long* (she expects net-higher in window).
- **Coverage Jun–Oct 2025 so far; Nov 2025→Jun 2026 scraping now** — will be
  appended (and will stress-test the regime finding against the full drawdown).
- Full per-call detail: `data/graded_all.json` (all 45) and `classify_all.py`
  (every one of the 142 classifications, transparent — nothing cherry-picked).
