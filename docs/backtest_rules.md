# Rose Margin — backtest design rules (decided with user, fill in during phase 6)

## Position sizing = RISK-PARITY (match her wide SL by shrinking size)
- Risk budget per trade is a FIXED $ amount; position size = risk_budget / her_SL_distance%.
- Wider her SL (smallcap 30-40%) -> smaller position. Tighter SL (BTC 5%) -> bigger position.
- This bounds the $ loss per trade regardless of her crazy SL distances.

## $10,000 plan, two variants
- "$100 plan": base risk $100/trade (1% of 10k).
- "$500 plan": base risk $500/trade (5% of 10k).

## 2x risk for INSANE long-range SWING setups (user rule, 2026-06-26)
- Her big-range moonshot LONGS (target +100% to +500%, wide SL) = SWING buys, NOT normal buys.
- For these swing setups, DOUBLE the risk budget:
    $100 plan -> $200 risk on swing setups
    $500 plan -> $1000 risk on swing setups
- Tight tactical trades (BTC/ETH/SOL scalp longs & shorts, small target/SL) stay at 1x risk.
- Need a "swing" flag per setup (big target multiple + wide SL) vs "tactical".

## Hold model
- VARIABLE hold: enter at her entry, exit on FIRST of {her target, her SL, her close msg}.
- Horizon up to weeks (her trades run minutes -> weeks). Use hourly price path.
- Use her force-close messages (matched by coin + time) as exit signals.

## Grade two ways
1. follow-her-exactly (her close / SL / target, whichever first)
2. mechanical (target vs SL first-touch only)

## UPDATE (user, 2026-06-26): SL cap also 2x on swing setups
- The hard per-trade $ stop-loss CAP doubles too on swing setups (not just the risk budget).
- "$500 plan had $200 SL -> now $400 SL" on swing trades.
- So: $500 plan normal cap = $200 / swing cap = $400 ; $100 plan normal = $100 / swing = $200.
- RECONCILE at phase 6: confirm exact mapping of "risk budget" vs "$ SL cap"
  (user also said risk "$500 -> $1000"; clarify whether risk==SL-cap or separate).

## Leverage (user, 2026-06-26)
- 2x-3x MAX. 1x for moonshot alts (wide 20-40% SL -> low lev avoids liquidation).
- (X-account backtest used 5x; Rose uses much lower because her SL distances are huge.)
- Risk-parity sizing already caps the $ loss; leverage only affects capital/liquidation.

## UPDATE (user, 2026-06-27): 2x only for BTC + large-caps
- The 2x swing risk/SL is RESTRICTED to BTC and large-caps. NO 2x for altcoins,
  even on buy&hold/swing. Altcoins always stay 1x risk (and 1x leverage).
- So: 2x_eligible = (swing == true) AND (coin in LARGECAPS).
- LARGECAPS := BTC, ETH, BNB, SOL, XRP, ADA, DOGE, LTC, TRX, LINK, AVAX, DOT, BCH
  (top ~caps; refine at phase 6). Everything else = altcoin -> 1x always.
- The "swing" flag in tg_calls_extracted.json marks her swing/hold intent; the 2x
  eligibility is swing AND largecap (applied at backtest time, not in the flag).

## UPDATE (user, 2026-06-27): DROP $500 plan; run $100 + "$200-with-500-config"
- She trades A LOT (constant re-entries, scenario hedges, many CONCURRENT positions).
  Deploying $500/trade would massively over-leverage the $10k acct across simultaneous trades.
- So the two plans are now:
    PLAN A "$100"  : $100 margin/trade, CONSERVATIVE config (3%/wk stop, per-trade SL cap $100 normal / $200 swing)
    PLAN B "$200c5": $200 margin/trade, but use the AGGRESSIVE $500 CONFIG
                     (5%/wk stop, per-trade SL cap $200 normal / $400 swing)
- $500/trade plan is DROPPED entirely.
- Rationale: smaller per-trade notional keeps the account from blowing up when many
  of her positions are open at once; the $200 just inherits the looser $500 risk rules.

## UPDATE (user, 2026-06-27): spot-buy calls require SPOT listing
- Many coins are on Binance FUTURES but NOT on Binance SPOT.
- A kind:"spot" call (she says "buy spot"/"buy some at spot") is only actionable if the
  coin is on Binance SPOT. If it's futures-only -> IGNORE that spot call (can't buy spot).
- Leveraged setups (kind:"setup") trade on futures, so futures-only is fine for them.
- At grading: for kind=="spot", check coin against binance_symbols.json["spot"]; drop if absent.

## UPDATE (user, 2026-06-27): commodities ARE in scope IF on Binance futures
- Earlier I excluded oil/commodity calls as "not crypto coins". User corrected this:
  if the instrument is actually listed on Binance FUTURES, do NOT ignore it.
- Verified: **CLUSDT (WTI crude oil) perpetual IS live on Binance futures**
  (`fapi/v1/klines?symbol=CLUSDT` -> HTTP 200, gradeable). BRENT/USOIL/WTI tickers are NOT.
- So her oil calls (#OIL / #BRENT / #CL) are NOW INCLUDED, graded via the Binance CLUSDT perp:
  ids 51904, 52134, 52139, 52140 -> binance:true, binance_sym="CLUSDT".
- Caveat: 52134 was charted on Brent (Hyperliquid); its entry is Brent-priced, so grading it
  against CLUSDT (WTI) carries the small Brent-WTI spread error. WTI/CL ids are exact.
- General rule going forward: scope = anything on Binance futures OR Binance spot, crypto OR
  commodity. Only exclude instruments with NO Binance listing (e.g. pure CFD/Hyperliquid-only).
