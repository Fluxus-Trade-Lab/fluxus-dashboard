"""Context helpers: percentile framing and the secondary-level ladder."""
import pytest

from pipeline.reference.context import percentile_of, ranked_levels, load_history


def test_percentile_places_value_in_its_own_history():
    hist = [-10.0, -5.0, 0.0, 5.0, 10.0]
    assert percentile_of(-10.0, hist)["pct"] == pytest.approx(10.0)   # lowest
    assert percentile_of(0.0, hist)["pct"] == pytest.approx(50.0)     # median
    assert percentile_of(10.0, hist)["pct"] == pytest.approx(90.0)    # highest


def test_percentile_reports_sample_size_and_flags_thin_samples():
    # The whole point: 14 sessions and 500 sessions render the same on a page.
    thin = percentile_of(0.0, list(range(14)))
    assert thin["n"] == 14 and thin["thin"] is True
    deep = percentile_of(0.0, list(range(60)))
    assert deep["n"] == 60 and deep["thin"] is False


def test_percentile_handles_empty_history_without_inventing_a_number():
    r = percentile_of(-1.9e9, [])
    assert r["pct"] is None and r["n"] == 0 and r["thin"] is True


def test_percentile_ignores_missing_entries():
    assert percentile_of(5.0, [1.0, None, 9.0])["n"] == 2


def test_ranked_levels_excludes_the_headline_walls():
    ps = {7400: -3.0e9, 7550: +2.0e9, 7500: +1.5e9, 7350: -1.0e9, 7600: +0.2e9}
    out = ranked_levels(ps, spot=7450, exclude={7400, 7550}, n=3)
    assert [r["strike"] for r in out] == [7500, 7350, 7600]
    assert out[0]["rank"] == 1


def test_ranked_levels_annotates_side_and_distance():
    ps = {7500: +1.5e9, 7350: -1.0e9}
    out = ranked_levels(ps, spot=7450, n=5)
    above = next(r for r in out if r["strike"] == 7500)
    below = next(r for r in out if r["strike"] == 7350)
    assert above["side"] == "above" and above["distance"] == 50.0
    assert below["side"] == "below" and below["distance"] == -100.0
    assert above["sign"] == "positive" and below["sign"] == "negative"


def test_ranked_levels_orders_by_magnitude_not_by_sign():
    ps = {7300: -5.0e9, 7600: +1.0e9, 7500: +4.0e9}
    assert [r["strike"] for r in ranked_levels(ps, spot=7450, n=3)] == [7300, 7500, 7600]


def test_load_history_skips_documents_missing_the_field():
    docs = [{"total_gex": 1.0}, {"other": 2.0}, {"total_gex": 3.0}]
    assert load_history(docs) == [1.0, 3.0]
