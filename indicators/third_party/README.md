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
