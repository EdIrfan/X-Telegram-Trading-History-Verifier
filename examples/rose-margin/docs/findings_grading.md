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
bleed; we initially flagged coverage bias as a possible exoneration —
**but the phase-b de-bias below TESTED that and overturned it**: alt longs are −EV
even from her first entry, and the multibagger brags are largely unrealizable wicks.
Net: her followable edge is ~flat (shorts + majors); the alt moonshots are −EV.

## Implications for the $10k backtest
These fed the backtest design; it has since run (`docs/backtest_results.md`) and **even
the defensible subset lost** (best config −34%), confirming there's no riskable edge.
- Don't deploy the full undifferentiated portfolio (it's ~flat-to-negative).
- The defensible test was **her shorts + major-coin longs, mirror-her exits**, small
  risk-parity size — expected ~flat; quantified at best-case −34% (CORE-only, Plan A).
- Treat alt-moonshot longs as **tiny 1x lottery allocations** (user's instinct was
  right) with a **partial-TP + trailing** exit, NOT her fixed TP/SL — that's the only
  configuration where the entry edge (44% reach +20%) has a chance to pay.
- Her wide SLs ⇒ size down to bound loss (exactly the original premise).

---

## De-bias check (phase b): re-grading alt longs from her FIRST entry
`debias_alt_firstentry.py` → `data/debias_alt.json`. For the SAME 74 alt coins we
graded (survivorship-controlled), found each coin's earliest telegram mention = her
first call, re-priced on Binance, graded let-it-run over a **365-day** window.

**Result — coverage bias is NOT the savior; the alt bleed is real:**
- Peak reached from first entry: 8/74 ≥5×, 13 ≥3×, 22 ≥2×, 37 ≥1.5× — her entries
  genuinely have upside hit-rate (~30% touch 2×). She can pick pumpers.
- **Realized, though, is negative**: let-it-run w/ −50% stop **mean −11% / median −7%**;
  hold-through-no-stop **mean −17% / median −3%**; win 39–43%. Worse than bailing,
  because the dead alts bleed to −60%→−100% (TROY −100%, MOVE −97%, SAGA −96%…).

**The brags are mostly unrealizable peak prints (user's call, confirmed):**
- MYX first entry → **234× peak** on the chart, **realized ≈ +13%** — the spike is an
  illiquid low-float wick you cannot sell into. LAB 184× peak → −8% realized. The "x5"
  marketing cites peak screenshots, not takeable PnL. She brags the 1 winner's wick and
  is silent on the ~20 that round-tripped to zero. Classic subscription-farming barbell.

**Conclusion:** the alt-long negative EV survives the de-bias. Her measurable edge is
shorts ≈ breakeven + major longs ≈ breakeven; the alt moonshots are −EV as followable
trades regardless of entry timing. Treat her multiplier brags as marketing, not signal.
