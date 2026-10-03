"""RS unify option B: the switch reads rs_rating, the revert key restores the
old fields, and the forward-test shadow logs both lists."""
from pipeline.constants import rs_leg
from pipeline.tools import rs_switch_shadow as S


def _row(t, **kw):
    base = {"ticker": t, "tradeable": True, "avg_volume": 3e6, "sma50_dist": 0.05,
            "close": 50.0, "market_cap": 5e9, "vcs": 70, "adr_pct": 5.0,
            "change_pct": 0.05, "rel_volume": 2.0, "from_open_pct": 0.01,
            "sector": "Technology", "industry": "Software",
            "rs_1m": 50, "rs_21d": 50, "rs_3m": 50, "rs_rating": 50}
    base.update(kw)
    return base


def test_field_switch_and_revert_key():
    assert rs_leg.field("liquid_leader", unified=True) == "rs_rating"
    assert rs_leg.field("liquid_leader", unified=False) == "rs_3m"
    assert rs_leg.field("4pct_bullish", unified=False) == "rs_21d"
    assert "monthly_leader_97" not in rs_leg.LEGS     # B keeps it on rs_1m


EXACT = {"liquid_leader": {"OLD": (True, False), "NEW": (False, True), "BOTH": (True, True),
                           "NONE": (False, False)},
         "industry_top20": ({"Software", "Banks"}, {"Software", "Gold"})}


def test_shadow_marks_old_only_and_new_only():
    got = {(r["panel"], r["ticker"]): (r["old"], r["new"])
           for r in S.shadow_rows([_row("X")], date="2026-10-05", exact=EXACT)}
    assert got[("liquid_leader", "OLD")] == (1, 0)
    assert got[("liquid_leader", "NEW")] == (0, 1)
    assert got[("liquid_leader", "BOTH")] == (1, 1)
    assert ("liquid_leader", "NONE") not in got
    assert got[("industry_top20", "Banks")] == (1, 0)
    assert got[("industry_top20", "Gold")] == (0, 1)


def test_vcs_and_4pct_use_the_watchlist_panels_both_ways():
    rows = [_row("V_OLD", rs_3m=90, rs_rating=50), _row("V_NEW", rs_3m=50, rs_rating=90),
            _row("B_OLD", rs_21d=70, rs_rating=40, vcs=10), _row("B_NEW", rs_21d=40, rs_rating=70, vcs=10)]
    got = {(r["panel"], r["ticker"]): (r["old"], r["new"]) for r in S.shadow_rows(rows, date="d", exact={})}
    assert got[("vcs", "V_OLD")] == (1, 0)
    assert got[("vcs", "V_NEW")] == (0, 1)
    assert got[("4pct_bullish", "B_OLD")] == (1, 0)
    assert got[("4pct_bullish", "B_NEW")] == (0, 1)
    assert rs_leg.UNIFIED is True                       # the flip is restored


def test_archive_is_idempotent_per_date(tmp_path):
    p = tmp_path / "s.csv"
    rows = [_row("X")]
    n1 = S.archive(rows, date="2026-10-05", path=p, exact=EXACT)
    S.archive(rows, date="2026-10-05", path=p, exact=EXACT)
    S.archive(rows, date="2026-10-06", path=p, exact=EXACT)
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 1 + 2 * n1
    rep = S.report(p)
    assert rep["sessions"] == ["2026-10-05", "2026-10-06"]
    assert rep["liquid_leader"]["keep_mean"] == 0.5


def test_exact_new_reading_is_the_published_liquid_leader():
    """Positive control: the shadow's `new` list is the column the page shows,
    and its `old` list is what the page showed before the switch."""
    import logging
    import numpy as np
    import pandas as pd
    from pipeline.screeners.run_all import compute_universe_scores
    logging.disable(logging.CRITICAL)
    rng = np.random.default_rng(7)
    rows = [{"ticker": f"T{i}", "market_cap": 5e9, "close": 50.0, "avg_volume": 3e6,
             "industry": f"Ind{i % 25}", "sector": "Technology",
             "perf_1w": 0.01, "perf_1m": float(rng.normal(0, .1)), "perf_3m": float(rng.normal(0, .2)),
             "perf_6m": float(rng.normal(0, .3)), "perf_1y": float(rng.normal(0, .4)), "atr": 1.0,
             "sma20_dist": 0.0, "sma50_dist": 0.05, "high_52w": -0.05} for i in range(200)]
    df = compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")
    logging.disable(logging.NOTSET)
    ll = S.EXACT["liquid_leader"]
    assert {t for t, (_, n) in ll.items() if n} == set(df.index[df["liquid_leader"]])
    assert {t for t, (o, _) in ll.items() if o} != {t for t, (_, n) in ll.items() if n}   # the two readings differ
    old_i, new_i = S.EXACT["industry_top20"]
    assert set(new_i) == set(df.loc[df["industry_rank"] <= 20, "industry"])
