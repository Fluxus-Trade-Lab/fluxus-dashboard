"""The two-session bullish pattern — a checklist that never hides a near miss."""
from pipeline.profile import patterns as P


def d1(**kw):
    base = dict(date="2026-08-10", high=7800.0, low=7700.0, open=7780.0,
                close=7705.0, tpoc=7760.0, high_period=8,
                poor_extremes={"poor_high": True, "high_tpos": 2, "high": 7800.0},
                tails={"buying": None, "selling": None})
    base.update(kw)
    return {"date": base.pop("date"), "tpo": base}


def d2(vol_coincide=True, **kw):
    base = dict(date="2026-08-11", high=7810.0, low=7762.0, open=7710.0,
                close=7790.0, tpoc=7775.0,
                tails={"buying": {"low": 7762.0, "high": 7765.0, "length": 3,
                                  "significant": True}, "selling": None})
    base.update(kw)
    return {"date": base.pop("date"), "tpo": base,
            "volume": {"coincide": vol_coincide, "vpoc": 7775.0, "tpoc": 7775.0}}


def test_the_textbook_case_meets_every_condition():
    r = P.bullish_two_session(d1(), d2())
    assert r["n_met"] == r["n_total"] and r["complete"] is True


def test_a_near_miss_is_visible_rather_than_collapsed_to_false():
    # Value fails to migrate -- his stated invalidation. Nine of ten still hold,
    # and a bare boolean would throw that away.
    r = P.bullish_two_session(d1(), d2(tpoc=7755.0))
    assert r["complete"] is False
    assert r["n_met"] == 9 and r["n_failed"] == 1
    bad = [c for c in r["conditions"] if c["ok"] is False][0]
    assert bad["name"] == "value migrated up"
    assert "7,755" in bad["saw"]


def test_a_missing_input_is_unmeasurable_never_a_failed_condition():
    # A profile built before open/close were stored must not read as a rejection.
    old = d1()
    del old["tpo"]["close"]
    r = P.bullish_two_session(old, d2())
    assert r["n_unmeasurable"] >= 1
    assert all(c["measurable"] is False for c in r["conditions"] if c["ok"] is None)


def test_the_vpoc_tpoc_condition_reports_unmeasurable_without_one_instrument():
    r = P.bullish_two_session(d1(), d2(vol_coincide=None))
    c = [x for x in r["conditions"] if "VPOC" in x["name"]][0]
    assert c["ok"] is None and "one instrument" in c["saw"]


def test_a_day_one_that_closed_above_its_tpoc_fails_that_condition():
    r = P.bullish_two_session(d1(close=7790.0), d2())
    names = {c["name"]: c["ok"] for c in r["conditions"]}
    assert names["D1 closed below its own TPOC"] is False


def test_a_significant_buying_tail_on_day_one_breaks_the_no_excess_condition():
    tails = {"buying": {"low": 7700.0, "high": 7705.0, "length": 3,
                        "significant": True}, "selling": None}
    r = P.bullish_two_session(d1(tails=tails), d2())
    names = {c["name"]: c["ok"] for c in r["conditions"]}
    assert names["D1 no excess at the low"] is False


def test_a_poor_high_printed_early_does_not_count_as_made_late():
    r = P.bullish_two_session(d1(high_period=3), d2())
    names = {c["name"]: c["ok"] for c in r["conditions"]}
    assert names["D1 poor high made late"] is False


def test_the_reference_prices_are_his_four():
    r = P.bullish_two_session(d1(), d2())
    rp = r["reference_prices"]
    assert rp["entry"] == 7790.0            # D2 close
    assert rp["anchor_must_hold"] == 7760.0  # D1 TPOC
    assert rp["first_objective"] == 7800.0   # D1 poor high
    assert rp["invalidation_below"] == 7705.0  # D1 close
