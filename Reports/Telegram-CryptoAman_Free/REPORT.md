# Crypto Aman (`@CryptoAman_Free` · `Crypto Aman🔐CryptoVipTools`) — verdict

**Analyzed:** 2026-06-28 · 15,050 Telegram messages (2025-01-01 → 2026-06-28) ·
prices = free Binance 1h klines (spot, futures fallback). Same "CryptoVipTools"
network as the `Rose_Margin` worked example.

---

## TL;DR — **No harvestable mechanical edge. Alert-only; do NOT auto-trade.**

Crypto Aman posts **structured scalp calls** with the levels written in the caption
text (entry zone, a ladder of targets, and a "2H candle close beyond SL" stop). I
extracted **531 unique calls** (Oct 2025 → Jun 2026), graded **509** look-ahead-safe
against real Binance prices, and backtested a realistic $10k account.

The signal is, at best, a **gross coin-flip**:

- Trading her **stated plan** (laddered partial take-profits, close-based stop) returns
  **+25% summed gross → −77% summed after a modest 0.2% round-trip cost → −229% at
  0.5%.** Per trade: **−0.15%** net (55% win rate). The result lives or dies entirely
  on trading costs, i.e. there is no margin above fees.
- A realistic $10k account trading **everything** ends at **−8% to −16%** over the ~9
  months (risk-parity sizing makes it *worse*, a classic sign the underlying edge is
  negative).
- The losses concentrate in **alt-coin scalps** and in one of the two posters
  ("**Orange**"). **Majors** (BTC/ETH/SOL/BNB/XRP) and the "**Apple**" poster are
  roughly **breakeven-to-marginally-positive** — but thin, method-dependent, and from a
  single 9-month sample, so **not** something to bank real money on.

Context: this window was a **bear market** — BTC **−51%**, ETH **−65%** buy-and-hold.
A scalper staying ~breakeven-gross through that isn't a disaster, but it isn't alpha
either, and after costs it bleeds.

---

## What she posts (and what's gradeable)

| Bucket | Count | Used? |
|---|---:|---|
| Total messages scraped | 15,050 | — |
| Promo / BingX-referral spam | ~2,650 | excluded |
| Update posts ("TARGET 1 ✅ / move SL to entry") | ~4,210 | not entries (her exit signals) |
| **Structured entry calls (numeric Entry+SL+Type)** | **531 unique** | **graded** |
| → graded | 509 | 12 untriggered, 10 no-Binance-price |

**Format (the dominant template, Oct-2025 onward):**
```
🔊 ETH SCALP TRADE:
Current price - $2975
Entry price - $2970 - $2960          ← entry zone
Type - LONG
Target - $2990, $3000 & $3010+       ← laddered targets (3–5 typical)
Stop Loss (SL) - If 2H candle closes below $2940
```
These are **tight scalps**: median stop distance **2.5%**, median hold **~13h**, two
named posters (**Apple** 364, **Orange** 130). Because the call fully specifies the
exit plan, *grading her stated plan = mirroring her* — no discretionary close-signal
mining was needed (unlike Rose).

**Coverage limit:** Jan–Sep 2025 calls were posted as **chart images with prose
captions** (levels on the picture), not the structured text template, so they are
**not text-gradeable** and are excluded. The graded universe is the **structured-scalp
era, 2025-10-09 → 2026-06-28** (~9 months, ~2 calls/day). This is forward-graded with
no winner cherry-picking, so there's no survivorship bias *within* the window.

---

## How it was graded (look-ahead-safe)

- **Entry** = limit fill at her entry **zone**, on the first 1h candle after the post
  that reaches it; never reached within max-hold → **untriggered** (12, dropped).
- **Max-hold** 120h (5d, generous vs her 2H–24H scalp horizon); clipped to now.
- Three exits per filled trade:
  - **LADDER (her plan)** — exit 1/N of size at each target (wick-touch); remainder
    stops when a **1h candle *closes*** beyond SL (faithful to her "2H candle close"
    rule); leftover at max-hold close.
  - **MECH** — single first-touch of **TP1 vs SL** (both intrabar; SL wins ties). A
    hard-stop, pessimistic version.
  - **RUN** — let-it-run: close-based initial stop, then 25% trail after +20% in favor.
- `return = (exit/entry − 1) × dir`. Friction reported at **0% / 0.2% / 0.5%**
  round-trip (0.2% is the headline — realistic for liquid perps).

---

## Results

### Per-trade (509 trades, net of 0.2%)

| Method | Win% | Avg/trade | Avg win | Avg loss | Sum |
|---|---:|---:|---:|---:|---:|
| **LADDER** (her plan) | 55.4% | **−0.15%** | +1.54% | −2.25% | **−76.6%** |
| MECH (TP1 vs hard SL) | 79.1% | −0.18% | +0.57% | −3.04% | −91.5% |
| RUN (let-it-run) | 25.3% | −0.79% | +5.44% | −2.91% | −404.7% |

- **MECH wins 79% of the time and still loses** — the textbook scalper trap: TP1 (the
  first, nearest target) fills **83%** of the time for a tiny gain, but the **20%** that
  hit the stop lose ~5× as much. Small wins, fat tails.
- **RUN is catastrophic** — her *entries* have no trend-continuation edge; giving the
  trade room just donates it back.

### Friction sensitivity (LADDER, summed)
| 0% (gross) | 0.2% (net) | 0.5% (net) |
|---:|---:|---:|
| **+25.2%** | **−76.6%** | **−229.3%** |

The whole edge is **inside the spread**. Gross breakeven, net bleed.

### Segments (LADDER, net 0.2%, summed)
| Segment | n | Win% | Sum |
|---|---:|---:|---:|
| Majors (BTC/ETH/SOL/BNB/XRP) | 322 | 58.1% | **+1.6%** |
| Alts | 187 | 50.8% | **−78.2%** |
| Major longs | 225 | 56.4% | −10.9% |
| Alt longs | 146 | 52.7% | −40.8% |
| Longs | 371 | 55.0% | −51.7% |
| Shorts | 138 | 56.5% | −24.8% |
| **Apple** poster | 364 | 60.2% | **+9.2%** |
| **Orange** poster | 130 | 40.8% | **−94.8%** |

> Note: by the pessimistic **MECH** method, *every* segment — including Apple
> (−56.6%) — is negative. The only non-negative cuts (Apple, majors, shorts) appear
> **only** under the laddered exit. Edge that exists in one exit rule and vanishes in
> another is not robust.

### Realized vs. the brag
- Average **favorable excursion (MFE) = +6.2%** per trade, but average **realized
  LADDER = −0.15%**. The price often moves her way; her tight targets/stops (and the
  reversals) mean almost none of that 6.2% is harvestable.
- **168 of 509** trades moved **≥1% in her favor yet still finished ≤0** on the ladder.
- "Exit-at-peak" (+6.2% avg) is the kind of number a screenshot would brag — it is
  **unrealizable**.

---

## Realistic $10k account (event-driven, risk-parity, 5× margin cap, 0.2% cost)

| Config | Final | Return | maxDD |
|---|---:|---:|---:|
| ALL · risk-parity 1.5%/trade | $8,394 | **−16.1%** | 36% |
| ALL · risk-parity 1.0%/trade | $9,187 | −8.1% | 25% |
| ALL · flat $1,000 notional (baseline) | $9,234 | −7.7% | 13% |
| MAJORS only | $9,886 | −1.1% | 27% |
| ALTS only | $8,582 | −14.2% | 23% |
| **APPLE poster only** | $11,830 | **+18.3%** | 27% |
| LONGS only | $8,195 | −18.0% | 30% |
| SHORTS only | $10,286 | +2.9% | 17% |

Risk-parity (bigger size on tighter stops) **deepens** the loss vs the flat baseline —
when the underlying expectancy is ≤0, "smart" sizing just levers the bleed.

---

## Honesty caveats (read these)

1. **Costs decide everything.** Gross ≈ breakeven; the verdict flips entirely on the
   assumed round-trip cost. On thin alts, real cost (spread + slippage on a leveraged
   scalp) is likely **worse** than 0.2%, so the live result is at the pessimistic end.
2. **Execution realism is generous to her.** I assume you get her exact entry zone via
   limit and that TP fills on a wick touch. Her posts have human latency (identical
   reposts 3 min apart), and a follower's fills will be worse than modeled.
3. **The "Apple +18%" is a hypothesis, not a green light.** One poster, one 9-month
   window, ~breakeven per-trade (+0.025% net), positive only with compounding under one
   exit rule, and negative under MECH. No out-of-sample. Treat as *worth watching*.
4. **Coverage.** Only the structured-text era (Oct 2025→) is graded; the 2025
   chart-image calls aren't text-gradeable. 10 calls on `CRO`/`MNT` are dropped — those
   coins have **no Binance listing at all** (free-oracle limitation), not cherry-picked.
5. **Bear-market regime.** BTC −51% / ETH −65% over the window; a different regime could
   look different — but "needs a bull market to work" is itself not an edge.

---

## Recommendation

**Alert-only. Do not auto-trade this channel.** As a whole it is **net-negative** after
realistic costs, dragged down by alt scalps and the "Orange" poster. If you want to
keep watching anything, restrict alerts to **Apple's major-coin scalps** and treat them
as **breakeven-until-proven-otherwise**, applying your own judgment on entry/cost — not
as a signal to size into. The marketing multipliers are unrealizable peak excursions,
not takeable returns.

---

## Reproducibility (all scripts in this folder)
| Script | Output |
|---|---|
| `explore.py`, `samples.py`, `classify_explore.py` | data profiling / format discovery |
| `extract.py` | `calls_extracted.json` — 531 structured calls |
| `grade.py` | `graded.json` — 509 graded, 3 ways + segments |
| `backtest.py` | `backtest.json` — $10k account, 8 configs |

Raw scrape: `../telegram_posts.json` (15,050 msgs). Prices cached in `../price_cache/`.
Re-run: `docker exec x-telegram-verifier python data/cryptoaman_free/analysis/<script>.py`.
