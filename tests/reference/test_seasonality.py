"""Tests for the pure monthly-seasonality computation."""
import pandas as pd

from pipeline.reference.seasonality import monthly_seasonality


def _const_month_series(month_values: dict[tuple[int, int], float]) -> pd.Series:
    """Daily close series where every day in (year, month) holds a constant.

    Makes month-end resampling deterministic: the month-end close is exactly the
    constant, so month-over-month returns are hand-computable.
    """
    frames = []
    for (y, m), v in month_values.items():
        idx = pd.date_range(f"{y}-{m:02d}-01", periods=20, freq="B")
        frames.append(pd.Series(v, index=idx))
    return pd.concat(frames).sort_index()


def test_august_stats_across_two_years():
    # Jul->Aug 2024: 100 -> 105 (+5%);  Jul->Aug 2025: 200 -> 190 (-5%).
    s = _const_month_series({
        (2024, 6): 99, (2024, 7): 100, (2024, 8): 105,
        (2025, 6): 199, (2025, 7): 200, (2025, 8): 190,
    })
    out = monthly_seasonality(s)
    aug = next(m for m in out["months"] if m["month"] == 8)
    assert aug["n"] == 2
    assert abs(aug["mean_pct"] - 0.0) < 1e-6      # (+5 + -5)/2
    assert abs(aug["win_pct"] - 50.0) < 1e-6
    assert round(aug["max_pct"], 2) == 5.0 and round(aug["min_pct"], 2) == -5.0
    by_year = {r["year"]: round(r["ret_pct"], 2) for r in out["by_year"]["8"]}
    assert by_year == {2024: 5.0, 2025: -5.0}


def test_history_span_and_month_coverage():
    s = _const_month_series({(2024, m): 100 + m for m in range(1, 13)})
    out = monthly_seasonality(s)
    assert out["history"]["start"] == "2024-01-01"
    # Every calendar month that has a computable return appears exactly once.
    assert len({m["month"] for m in out["months"]}) == len(out["months"])
    assert all(1 <= m["month"] <= 12 for m in out["months"])
