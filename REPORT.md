# @blockchainedbb crypto-call accuracy — interim report

**Scope graded so far:** 37 genuine *forward* directional calls, **June–October 2025**
(the 5 months scraped before X throttled advanced search). Graded by Claude reading
each post's text + chart image; verified against Binance OHLCV (matches TradingView)
over a **7-day window**. She trades **high leverage**, so win-thresholds are small
(BTC 1.5%, alts 2–3%) and we track favourable-vs-adverse excursion, not just close.

## Headline (two honest numbers)
| Metric | Score |
|---|---|
| **Close-based** — did the swing pay by window end | **18/37 = 48.6%** |
| **Excursion-based** — did price ever pop her way ≥ threshold (a leveraged win) | **29/37 = 78.4%** |

The truth for a leveraged account sits between these, and is **regime-dependent**.

## The real signal: regime + excursion asymmetry
| Regime | Close | Excursion | Adverse excursion (leverage killer) |
|---|---|---|---|
| Bull / normal (Jun–early Oct) | 17/28 ≈ **61%** | 23/28 ≈ **82%** | small, ~ −1% to −5% (leverage-safe) |
| Oct 2025 crash (Oct 6–28) | 1/9 ≈ **11%** | 6/9 ≈ 67%* | **−6% to −63%** (liquidation) |

\* Excursion "wins" in the crash are illusory under leverage — the favourable pop
(+1–3%) is wiped out by the adverse move (DOGE −63%, XRP −56%, ETH −21%, BTC −17%)
long before it can be banked.

## Behavioural findings
1. **Trend-following permabull.** In uptrends her leveraged longs have great
   asymmetry (fav +6–25% vs adv −1–2%). July target calls all hit (BTC→112k,
   ETH 2600/2888/3500), +8% to +22%.
2. **Does not call tops; weak at shorts (1/5).** Sep shorts too early; she longed
   straight into the October crash and kept buying the dip all the way down.
3. **Lots of retroactive posting.** Of 142 "call-like" posts, ~105 were PnL brags,
   "I called the bottom" victory laps, promo dumps, or position management — only
   ~37 were falsifiable *forward* calls.

## Implication for a follow/alert bot
Her calls are not a flat hit-rate — they're a **regime trade**. Edge is real in
confirmed uptrends (leverage-safe asymmetry), catastrophic once trend breaks. A bot
must **mute her longs when trend structure breaks / market is in a downtrend**, or it
inherits exactly the Oct-crash blowups. Alert-only with a regime veto = right design.

## Caveats & next steps
- n=37; 7-day window (matches her 2–3 day swing style).
- Win thresholds assume high leverage: BTC 1.5%, ETH/BNB 2%, SOL/XRP/LTC/LINK 2.5%,
  DOGE 3%. Adjustable in `score_graded.py`.
- Coverage is **Jun–Oct 2025 only**. Nov 2025–Jun 2026 still to scrape (X
  advanced-search throttle — resume next session, gentler pacing) to extend n and
  capture more regimes.
- Per-call detail (fav/adv excursion, verdicts) in `data/graded.json`.
