# Rose Margin — $10,000 backtest results

`backtest_rose.py` → `data/backtest_rose.json`. Risk-parity sizing (notional =
risk_budget / her_SL_distance), PnL = notional × graded_return (0.5% friction
already in returns). Event-driven & fundable: margin capped at the account, ruin
at $0, −3%/−5% weekly circuit-breaker. Two plans, four strategies each.

## Results (start $10,000)
| Plan | Strategy | End $ | Return | MaxDD | Trades | Win% | wk-skips | unfunded | Peak margin |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **A $100** | **CORE-only** (shorts+largecap longs) | **6,598** | **−34.0%** | 41% | 243 | 33% | 31 | 5 | $10.5k |
| A $100 | SEGMENTED (core + alt let-it-run) | 2,783 | −72.2% | 73% | 310 | 30% | 57 | 46 | $8.4k |
| A $100 | all-A (mirror her, everything) | 2,391 | −76.1% | 76% | 286 | 32% | 79 | 48 | $8.3k |
| A $100 | all-B (mechanical TP/SL) | 151 | −98.5% | 99% | 199 | 21% | 94 | 120 | $7.2k |
| B $200c5 | CORE-only | 2,538 | −74.6% | 78% | 204 | 32% | 36 | 39 | $10.1k |
| B $200c5 | SEGMENTED | 1,504 | −85.0% | 86% | 183 | 29% | 56 | 174 | $9.4k |

**Raw signal (flat $1,000/trade, no risk-parity, no stops):** segmented −187%,
all-A −264%, all-B −329% of the $10k. So the **weekly stop + risk-parity + funding
caps REDUCE the loss** (−187% → −72%); they don't create the loss — the signal is
negative on its own.

## Where the PnL comes from (Plan A, segmented)
| Segment | n | PnL |
|---|--:|--:|
| Shorts | 130 | **+$29** (breakeven) |
| Large-cap longs | 149 | −$3,480 |
| Alt longs | 134 | −$5,883 |

## Reading it (honest)
1. **No profitable configuration.** Best is Plan-A CORE-only at **−34%**. Everything
   that includes the alt-moonshot longs, or uses mechanical TP/SL, is far worse.
2. **The weekly −3%/−5% breaker works** (57/56 trades skipped after a bad week) and
   materially limits drawdown — but it cannot rescue a negative-edge signal.
3. **Plan B ($200 risk) over-deploys**: 174 unfunded skips (vs 46 for Plan A) — at
   $200 risk × her trade frequency the $10k can't fund the concurrent positions.
   This quantitatively confirms dropping the $500 plan; even $200 is too hot here.
4. **Risk-parity + 2×-swing AMPLIFY losses** because they up-size tight-SL trades and
   double swing-largecap risk — rules built for a positive edge magnify a negative one.

## The three big caveats (why this is a FLOOR, not a fair verdict on her)
1. **Coverage bias (decisive for alt longs):** her multibagger brags are "x5 from
   FIRST entry"; we extracted the chart setups, which are mostly her LATE re-entries
   (we hold LAB at $17 after its pump, not the $4 first entry that 5×'d). The
   −$5,883 alt-long bleed is therefore overstated — her winning early entries aren't
   in our data and can't be graded.
2. **She is discretionary, not mechanical.** She scales, hedges, force-closes, and
   re-times in real-time. A blind chart-replay (this backtest) can't reproduce that.
   The fact that her SHORTS net breakeven mechanically hints real timing skill that a
   mechanical mirror dilutes.
3. **Her exits leave money on the table** (MYX stopped −7% then +200x); a let-it-run
   overlay helps but our 1h/▶max-hold window still misses multi-month pumps.

## Bottom line
As a **blind mechanical strategy on the charts we captured**, Rose Margin does **not**
show a harvestable, riskable edge — best case −34%, most configs −70% to −98%. This is
similar to (actually worse than) the @blockchainedbb result (+4.4%). BUT the alt-long
coverage bias + her discretionary management mean this is a **lower bound on a blind
copy**, not proof she's a losing trader. Her shorts + major-coin timing are ~breakeven
mechanically, which is where any real edge would live.

## Implication for the final phase (alert bot)
An **alert-only** bot is the right call precisely because her edge (if any) is
discretionary: surface her calls in real time so a human applies judgment —
specifically (a) take shorts + major-coin longs, (b) skip or tiny-size alt moonshots,
(c) **trail winners she cuts early**. Do NOT wire it to auto-trade on these results.
