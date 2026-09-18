# Third-party Pine sources kept for porting

Verbatim copies of open-source TradingView scripts we port into `pipeline/`.
Kept so a port can always be diffed against the exact source it claims to
follow. Do not edit; if the author updates, add a dated copy alongside.

| file | author | ported to | notes |
|---|---|---|---|
| `oratnek_advanced_structure_pivot.pine` | @oratnek_ill | `pipeline/screeners/structure_pivot.py` | v6, received 2026-08-17 via Andy |
| `oratnek_asp_probe.pine` | (derived) | golden-check probe | oratnek's ASP unchanged + a table that prints last-bar state; paste into TV web on a daily chart, compare with `python -m pipeline.tools.structure_pivot_probe` |
| `oratnek_vcs_probe.pine` | (derived) | golden-check probe | VCS v2 unchanged + parts table; compare with `python -m pipeline.tools.vcs_probe` |
| `oratnek_vcs_v2.pine` | @oratnek_ill | `pipeline/adapters/yfinance_adapter.py::calculate_vcs` | v6 'updated code', received 2026-08-17; supersedes the modified port of the older version |
| `tradedudenyc_candles_stage_analysis_modified.pine` | @TradeDudeNYC (tradingview.com/v/agQTA0Vq/), modified | `pipeline/screeners/stage_analysis.py::stage_tdn_series` | v6; copied 2026-09-18 verbatim from Andy's `~/Documents/Trading/03_Trading_Strategies/Strategy_Docs/Candles Stage Analysis.txt`, whose header says "Stage definitions are copied from @TradeDudeNYC's indicator ... & modified later". Only the stage-selection block is ported; colours/labels are display |
