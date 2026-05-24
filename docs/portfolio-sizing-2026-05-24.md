# Position-Sizing Analysis — 2026-05-24

_233 closed trades · $1,000,000 starting capital · fixed R = $2,500 (0.25% of equity)_

## TL;DR

- **Median trade is sized to risk 1.32R** (mean 1.85R) on the initial stop. 62% of trades risked >1R; 30% risked >2R. Your tactical-leg design intentionally accepts 2-3R initial risk on burst entries.
- **Sizing has weak relationship with ATR** (r = -0.06) — position size doesn't track volatility much. Your stated rule (larger size for lower-ATR) is not strongly reflected in the data.
- **Best-performing risk bucket**: **< 1R** (mean realized R = +1.35, win rate 40% on 89 trades).
- **Worst-performing risk bucket**: **1-2R** (mean realized R = -0.04 on 75 trades).
- **Cost of oversized losses**: 64 trades risked >1.5R and lost — total realized -50.16R. This is the dollar cost of stretching past your R limit on losers.

## By ATR bucket — actual sizing vs ideal for 1R risk

`Median position %` = the size you actually trade. 
`Ideal pos % for 1R` = the size that would deliver exactly 1R risk if your stop is 1 ATR away. 
Anything well above ideal means you're running tactical-leg oversized; below means under-leveraged.

| ATR bucket | # trades | Median pos % | Ideal pos % (1R) | Median stop dist (ATR) | Median initial risk (R) | Median realized R |
|---|---:|---:|---:|---:|---:|---:|
| **<3%** | 5 | 10.55% | 16.67% | 1.46× | 1.28R | -0.67R |
| **3-5%** | 46 | 9.41% | 6.25% | 0.67× | 0.72R | -0.55R |
| **5-7%** | 68 | 8.48% | 4.17% | 0.80× | 1.45R | -0.27R |
| **7-10%** | 73 | 7.66% | 2.94% | 0.49× | 1.26R | -0.35R |
| **10%+** | 41 | 6.11% | 2.27% | 0.51× | 1.39R | +0.00R |

## By initial-risk bucket — do oversized trades earn more?

Sort trades by how much R was at risk on the initial stop. 
If mean realized R rises with risk, oversizing is paying off. If it plateaus or falls, extra risk is unrewarded.

| Initial risk | # trades | Win rate | Mean realized R | Median realized R |
|---|---:|---:|---:|---:|
| **< 1R** | 89 | 40% | +1.35R | -0.06R |
| **1-2R** | 75 | 28% | -0.04R | -0.57R |
| **2-3R** | 40 | 40% | +0.39R | -0.28R |
| **3-5R** | 21 | 38% | +0.53R | -0.16R |
| **5R+** | 8 | 50% | +0.03R | -0.15R |

## Top 10 oversized trades (by initial-risk R)

Trades that risked the most R on the initial stop. Check whether the size was justified.

| Ticker · Entry | Position % | ATR% | Stop dist (ATR) | Initial risk R | Realized R |
|---|---:|---:|---:|---:|---:|
| OKLO · 2026-05-05 | 12.51% | 10.2% | 8.89× | 45.26R | +0.01R |
| VRT · 2026-03-05 | 9.23% | 5.4% | 6.98× | 13.86R | +0.16R |
| GEV · 2026-01-15 | 23.03% | 3.4% | 2.13× | 6.63R | -0.54R |
| SOXS · 2026-05-14 | 15.77% | 15.8% | 0.64× | 6.36R | +1.81R |
| LEU · 2026-01-27 | 16.16% | 10.1% | 0.89× | 5.81R | -1.10R |
| SOXS · 2026-05-17 | 15.09% | 14.1% | 0.65× | 5.49R | +1.33R |
| TSLL · 2026-05-10 | 8.71% | 5.8% | 2.56× | 5.19R | -0.32R |
| CWEB · 2026-05-12 | 12.22% | 4.0% | 2.58× | 5.02R | -1.08R |
| FIG · 2026-05-14 | 15.77% | 6.0% | 1.31× | 4.96R | +0.49R |
| CRCL · 2026-05-10 | 17.42% | 7.5% | 0.95× | 4.92R | -1.33R |

## Biggest losses on oversized trades

Trades that risked >1.5R AND lost money. The closest data we have to 'what did oversizing cost me?'

| Ticker · Entry | Position % | ATR% | Initial risk R | Realized R |
|---|---:|---:|---:|---:|
| BABA · 2026-01-20 | 11.24% | 3.9% | 1.73R | -5.68R |
| AEO · 2026-01-05 | 10.00% | 3.8% | 1.82R | -2.78R |
| BABA · 2026-01-14 | 5.01% | 3.4% | 1.75R | -2.69R |
| ACMR · 2026-04-21 | 10.16% | 5.7% | 2.55R | -1.42R |
| CRCL · 2026-05-10 | 17.42% | 7.5% | 4.92R | -1.33R |
| NOWL · 2026-05-19 | 7.65% | 9.7% | 1.57R | -1.31R |
| RKLB · 2026-03-16 | 9.21% | 7.1% | 2.36R | -1.25R |
| SLV · 2026-05-07 | 13.81% | 3.6% | 2.36R | -1.23R |
| NOWL · 2026-05-18 | 14.71% | 8.4% | 3.24R | -1.14R |
| ONDS · 2026-04-30 | 6.26% | 8.1% | 1.79R | -1.14R |

## Recommended sizing curve

Given your fixed R = $2,500 (0.25% of $1M), a tight ≤1 ATR stop, and the tactical-leg goal of 2-3R initial risk on burst entries, here's the size to put on for each ATR bucket. Adjust ±1% for context.

| ATR% | For 1R risk | For 2R (tactical low) | For 3R (tactical high) |
|---|---:|---:|---:|
| **3-5%** | 6.2% | 12.5% | 18.8% |
| **5-7%** | 4.2% | 8.3% | 12.5% |
| **7-10%** | 2.9% | 5.9% | 8.8% |
| **10%+** | 2.3% | 4.5% | 6.8% |

_Rule of thumb_: **position % ≈ (target_R × 0.25%) × 100 / ATR%**. E.g., ATR 7% × 3R target → position ≈ 10.7%. ATR 10% × 2R target → position ≈ 5%.
