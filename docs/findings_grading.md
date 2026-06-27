# Rose Margin — grading findings (her real ups & downs)

Graded **413 of 418** unique tradeable entries (5 untriggered) from
`data/tg_calls_extracted.json` against Binance 1h klines, three ways
(`grade_rose.py` → `data/graded_rose.json`). Raw price-move % per trade, 1x, 0.5%
friction; leverage/sizing NOT yet applied. See `docs/grading_spec.md` for method.

Three exit lenses:
- **A – mirror her posts**: exit on her announced close/stop signal, else max-hold.
- **B – mechanical**: TP1 vs chart-SL first-touch (her SL as a hard intraday stop).
- **C – let it run**: wide initial stop (chart SL) then a 25% trailing stop after
  +20% in favor. Illustrative, NOT parameter-tuned.

## Headline (per-trade, 1x, after friction)
| Segment | n | A win% | A avg | A med | B avg |
|---|--:|--:|--:|--:|--:|
| **ALL** | 413 | 30% | **−6.4%** | −1.3% | −8.0% |
| Shorts | 130 | 33% | **+0.2%** | −0.6% | +1.4% |
| Major longs (BTC/ETH) | 113 | 31% | **−1.1%** | −0.8% | −5.1% |
| Alt longs | 170 | 26% | **−14.9%** | −7.0% | −17.0% |
| **Tradeable (shorts+major longs)** | 243 | 32% | **−0.4%** | −0.7% | −1.6% |

Excursion (all trades): median favorable **+13%**, median adverse **−23%**.

## What this says about her
1. **Shorts ≈ breakeven, slight positive.** She's a nimble, fast short-side scalper
   — opens, then closes quickly (Method A holds capture little; she cuts at ~flat).
   Her best late-2025/2026 BTC/ETH shorts did work (+14%/+15%) but many earlier ones
   got shaken out on pre-move chop (BTC wicked 93k before the 125k→59k crash).
2. **Major (BTC/ETH) longs ≈ breakeven** mirroring her (−1.1%); she scratches them.
   Mechanically worse (−5.1%) because her tight-ish long stops get wicked in chop.
3. **Alt longs bleed** (−15%) — BUT see the two big caveats below; this number is
   NOT a fair verdict on her alt game.
4. **The alpha is in the EXIT, not a missing entry edge.** Her alt-long *entries* are
   frequently right: **44% reach +20%, 22% reach +50%, 10% reach +100%** intra-trade.
   Yet realized returns are flat/negative because **both her targets are too tight
   (cap runners) and her stops too tight (cut before the move)**:
   - MYX: she stopped −7%; it then did **~200x** (mechanical TP1 capped at +105%).
   - BSB: +337% favorable, she closed −70%.  BAN: +218% then round-tripped to −6%.
   This is the answer to "6–21% TP or go crazier": **her fixed targets leave huge
   money on the table; a partial-TP + trail/let-run on a small position is the edge.**

## Two caveats that materially soften the alt-long bleed
- **Coverage bias (big one):** her multibagger brags are "x5 **from first entry**".
  We extracted the chart setups, which are often the **late re-entries** (e.g. we
  hold LAB at $17 *after* its pump, BEAT at $1.97 mid-pump), NOT the early $4-5 / $0.5
  first entries that actually 5x'd. So we systematically **caught her late entries and
  missed her winning early ones** → alt longs look worse than her published record.
- **Lottery shape:** alt longs are left-skewed (mean −15% ≪ a few huge winners);
  window (max-hold 30/90d) + 1h granularity can miss multi-month pumps.

## Bottom line (honest)
On the trades we can fairly grade (**shorts + major longs, n=243**), mirroring her
exactly is **~flat (−0.4%/trade, median −0.7%)** after friction — a **thin, basically
neutral edge**, echoing the @blockchainedbb result. Her alt-moonshot longs as captured
bleed, but that's confounded by coverage bias and the lottery shape, so it is **not**
proof she's −EV on alts — her real edge there (if any) lives in the early entries we
don't have and in a let-it-run exit she doesn't use.

## Implications for the $10k backtest
- Don't deploy the full undifferentiated portfolio (it's ~flat-to-negative).
- The defensible test: **her shorts + major-coin longs, mirror-her exits**, small
  risk-parity size — expected ~flat, low-drawdown; quantify it.
- Treat alt-moonshot longs as **tiny 1x lottery allocations** (user's instinct was
  right) with a **partial-TP + trailing** exit, NOT her fixed TP/SL — that's the only
  configuration where the entry edge (44% reach +20%) has a chance to pay.
- Her wide SLs ⇒ size down to bound loss (exactly the original premise).
