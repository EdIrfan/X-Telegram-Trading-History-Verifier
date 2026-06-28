> **⚠️ SHELVED (2026-06-27).** @blockchainedbb (X) sub-report — see `docs/REPORT.md` for the
> headline and the root `README.md` for the active project (Rose Margin).

# Strategy backtest — laddered TP + trailing stop (@blockchainedbb, 73 calls)

**Verification:** full **7-day window per trade**, walked on the **hourly price path**
(real intraday wicks checked candle-by-candle, not daily approximations). Entry priced
at the post-time hourly candle. Prices integrity-checked earlier (0 data errors).

## Strategy rules (5x isolated)
- **Initial stop −8% price** (= −40% of margin → −$40 on $100, −$200 on $500).
- **+6% → close 33%**, tighten stop to **−5%**.
- **Every +1.5% above** (7.5%…21%) → close **6.6%** more and **raise the stop +1.5%**
  (−5% → −3.5% → −2% → … → into profit). Fully out by +21%.
- **0.5% friction** on every trade. One entry per call (no DCA).
- Weekly circuit-breaker: **$100 acct → −$300 (3%)**, **$500 acct → −$500 (5%)**.

## Results (full year, Jun 2025 → Jun 2026)
| Account | End | Return | Max DD | Win rate | Full −8% stops |
|---|---|---|---|---|---|
| **$100/trade** | $10,292 | **+2.9%** | 4.6% | 59% (43/73) | 13 |
| **$500/trade** | $12,311 | **+23.1%** | 12.0% | 62% (43/69) | 9 |

## Read
- The $500 result is the $100 edge at 5x size: the **return scales ~linearly with
  position size, and so does the drawdown** — same signal quality, bigger bet.
- The signal is a thin, regime-dependent trend-follow edge; exit-rule tuning shifts the
  numbers a little but does not manufacture an edge that isn't there.
