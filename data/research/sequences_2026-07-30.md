# Sequence mining — as of 2026-07-30

## Read this before the table

- **One regime.** 89 archive sessions across a single market environment. A sequence that works here may only be describing that environment.
- **Multiple comparisons.** Many sequences were tested; some will look excellent by chance. Every number below is reported **net of a random-entry baseline** drawn from the same tickers and dates, and any sequence whose two half-samples disagree in sign is flagged unstable and excluded from the ranking.
- **Survivorship.** Prices were fetched today, so delisted and renamed tickers are missing (44 of 3872 tickers). Those failures skew toward losers, so the surviving numbers are, if anything, flattering. Per-sequence instances lost to missing prices are in the `lost` column.
- **Window.** 10 archive sessions. The archive omits non-session and untrustworthy days, so an N-session gap spans more calendar time than N days.
- Ranked on `net_median_excess_10`; `--min-n 20`, `--seed 42`.

## Ranked sequences

| Sequence | n | lost | net median excess (10d) | median MFE (R) | median MAE (R) | win rate |
|---|---:|---:|---:|---:|---:|---:|
| vcp -> momentum_97 | 110 | 54 | 4.4% | 1.97 | -1.21 | 54% |
| episodic_pivot -> healthy_charts | 177 | 13 | 2.1% | 1.64 | -1.39 | 53% |
| vol_up_gainers -> ema21_watch | 412 | 84 | 1.1% | 1.51 | -1.36 | 50% |
| healthy_charts -> ema21_watch | 6924 | 930 | 0.7% | 1.49 | -1.39 | 49% |
| ema21_watch -> healthy_charts | 4887 | 478 | 0.5% | 1.48 | -1.42 | 49% |
| episodic_pivot -> gainers_4pct | 282 | 18 | 0.3% | 1.69 | -1.41 | 46% |
| vol_up_gainers -> gainers_4pct | 2385 | 583 | 0.1% | 1.68 | -1.40 | 47% |
| episodic_pivot -> vol_up_gainers | 173 | 4 | -0.3% | 1.78 | -1.62 | 43% |
| vcp -> gainers_4pct | 646 | 54 | -0.3% | 1.41 | -1.42 | 45% |
| momentum_97 -> healthy_charts | 3917 | 302 | -0.4% | 1.72 | -1.55 | 47% |
| vol_up_gainers -> episodic_pivot | 180 | 17 | -0.7% | 1.81 | -1.84 | 42% |
| vcp -> healthy_charts | 554 | 49 | -0.7% | 1.50 | -1.54 | 45% |
| gainers_4pct -> vol_up_gainers | 3671 | 749 | -1.2% | 1.61 | -1.59 | 45% |
| ema21_watch -> vcp | 766 | 130 | -1.2% | 1.50 | -1.48 | 40% |
| momentum_97 -> episodic_pivot | 184 | 11 | -1.4% | 1.52 | -2.47 | 45% |
| gainers_4pct -> episodic_pivot | 479 | 47 | -1.5% | 1.77 | -1.76 | 43% |
| healthy_charts -> vcp | 812 | 65 | -1.7% | 1.53 | -1.53 | 39% |
| vcp -> vol_up_gainers | 226 | 10 | -1.7% | 0.96 | -1.64 | 35% |

## Excluded — unstable across half-samples

| Sequence | n | net median excess |
|---|---:|---:|
| episodic_pivot -> ema21_watch | 21 | 7.1% |
| ema21_watch -> episodic_pivot | 84 | 2.6% |
| healthy_charts -> episodic_pivot | 248 | 2.4% |
| ema21_watch -> momentum_97 | 1245 | 1.8% |
| gainers_4pct -> ema21_watch | 2271 | 1.3% |
| episodic_pivot -> momentum_97 | 172 | 1.0% |
| healthy_charts -> momentum_97 | 3731 | 1.0% |
| ema21_watch -> gainers_4pct | 3666 | 0.9% |
| healthy_charts -> gainers_4pct | 7272 | 0.8% |
| vol_up_gainers -> momentum_97 | 1028 | 0.6% |
| ema21_watch -> vol_up_gainers | 1004 | 0.6% |
| vol_up_gainers -> healthy_charts | 1210 | 0.4% |
| vol_up_gainers -> vcp | 66 | 0.2% |
| healthy_charts -> vol_up_gainers | 2130 | 0.2% |
| gainers_4pct -> momentum_97 | 3461 | 0.0% |
| gainers_4pct -> healthy_charts | 4484 | -0.0% |
| momentum_97 -> vol_up_gainers | 1359 | -0.3% |
| momentum_97 -> ema21_watch | 1819 | -0.3% |
| momentum_97 -> gainers_4pct | 4157 | -0.4% |
| vcp -> ema21_watch | 609 | -0.5% |
| gainers_4pct -> vcp | 394 | -0.6% |
| momentum_97 -> vcp | 170 | -1.9% |

## Excluded — fewer than 20 instances

| Sequence | n | net median excess |
|---|---:|---:|
| episodic_pivot -> vcp | 2 | 3.9% |
| vcp -> episodic_pivot | 13 | -5.2% |
