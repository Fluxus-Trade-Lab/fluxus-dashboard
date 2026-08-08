"""The centaur layer: what each of the three properties refuses to do."""
import pytest

from pipeline.centaur import blend as B
from pipeline.centaur import log as L
from pipeline.centaur import skill as S


def mv(**kw):
    base = dict(asof="2026-08-06T08:00:00-04:00", session="2026-08-06",
                source="machine", direction="up", conviction=2)
    base.update(kw)
    return L.view(**base)


def hv(**kw):
    return mv(source="human", **kw)


# ---------------------------------------------------- property 1: d_human

def test_stand_aside_is_a_real_direction_not_a_missing_value():
    # "I have no view" is information about calibration and must survive.
    v = hv(direction="stand_aside", conviction=1)
    assert v["direction"] == "stand_aside"


def test_a_view_without_asof_is_refused_because_it_would_be_a_memory():
    with pytest.raises(ValueError, match="asof"):
        mv(asof="")


def test_conviction_is_coarse_on_purpose():
    with pytest.raises(ValueError, match="conviction"):
        mv(conviction=7)
    with pytest.raises(ValueError, match="conviction"):
        mv(conviction=2.5)


def test_one_view_per_party_per_session_per_horizon(tmp_path):
    p = tmp_path / "v.jsonl"
    assert L.append(mv(), p) is True
    assert L.append(mv(direction="down"), p) is False   # no revising after the tape moved
    assert L.append(hv(), p) is True                    # the other party still may
    assert L.append(mv(horizon="swing"), p) is True     # a different horizon is a different call
    assert len(L.read(p)) == 3


def test_paired_needs_both_parties():
    rows = [mv(), hv(session="2026-08-05")]
    assert L.paired(rows) == []                         # different sessions
    assert len(L.paired([mv(), hv()])) == 1


def test_disagreements_are_isolated_because_they_carry_the_information():
    rows = [mv(session="2026-08-03", direction="up"), hv(session="2026-08-03", direction="up"),
            mv(session="2026-08-04", direction="up"), hv(session="2026-08-04", direction="down")]
    d = L.disagreements(rows)
    assert [x["session"] for x in d] == ["2026-08-04"]


# ------------------------------------------------- property 3: measurement

def test_a_close_in_the_middle_of_its_range_is_range_not_a_small_move():
    assert S.outcome(100, 110, 90, 100) == "range"
    assert S.outcome(100, 110, 99, 109) == "up"


def test_abstentions_are_never_counted_as_hits_or_misses():
    rows = [hv(session="2026-08-03", direction="stand_aside"),
            hv(session="2026-08-04", direction="up")]
    s = S.skill(rows, "human", {"2026-08-03": "down", "2026-08-04": "up"})
    assert s["n_scored"] == 1 and s["n_abstained"] == 1 and s["hits"] == 1


def test_a_thin_record_reports_not_enough_rather_than_a_hit_rate():
    days = ["2026-08-03", "2026-08-04", "2026-08-05"]
    rows = [hv(session=d, direction="up") for d in days]
    s = S.skill(rows, "human", {d: "up" for d in days})
    assert s["hit_rate"] == 1.0          # the raw number is still there...
    assert s["enough"] is False          # ...but it is not a skill estimate
    assert "20 needed" in s["note"]


def test_conviction_weighted_rate_separates_a_confident_judge_from_a_lucky_one():
    # Right when committed, wrong when hedging: better than the flat rate shows.
    rows = [hv(session="2026-08-03", direction="up", conviction=3),
            hv(session="2026-08-04", direction="up", conviction=1)]
    s = S.skill(rows, "human", {"2026-08-03": "up", "2026-08-04": "down"})
    assert s["hit_rate"] == 0.5
    assert s["conviction_weighted_rate"] == pytest.approx(0.75)


def test_edge_is_measured_against_chance_not_against_zero():
    s = {"hit_rate": 0.40}
    assert S.edge_over_chance(s) == pytest.approx(0.40 - 1 / 3)


# ----------------------------------------------------- property 2: the merge

def _sk(hr, n=40):
    return {"enough": n >= S.MIN_SCORED, "hit_rate": hr, "note": "thin"}


def test_neither_party_can_be_silenced_or_take_over():
    # The Mayo result exists because the weaker judge KEPT influence.
    assert B.weight_from_skill(_sk(0.0))["weight"] >= B.MIN_WEIGHT
    assert B.weight_from_skill(_sk(1.0))["weight"] <= B.MAX_WEIGHT


def test_an_unproven_party_is_not_treated_as_average():
    w = B.weight_from_skill(_sk(0.9, n=3))
    assert w["basis"] == "unproven" and w["weight"] == B.UNPROVEN_WEIGHT
    assert w["weight"] < 0.5


def test_agreement_is_reported_as_agreement():
    out = B.centaur_view(mv(direction="up"), hv(direction="up"),
                         _sk(0.5), _sk(0.5))
    assert out["direction"] == "up" and out["agreed"] is True


def test_on_disagreement_the_better_measured_party_carries_it():
    out = B.centaur_view(mv(direction="up", conviction=2),
                         hv(direction="down", conviction=2),
                         machine_skill=_sk(0.60), human_skill=_sk(0.20))
    assert out["direction"] == "up" and out["agreed"] is False
    assert out["margin"] > 0


def test_a_committed_human_can_outvote_a_hedging_machine():
    # Conviction multiplies weight; presence alone is not a vote.
    out = B.centaur_view(mv(direction="up", conviction=1),
                         hv(direction="down", conviction=3),
                         machine_skill=_sk(0.45), human_skill=_sk(0.45))
    assert out["direction"] == "down"


def test_a_party_standing_aside_contributes_no_score_but_is_still_reported():
    out = B.centaur_view(mv(direction="up", conviction=2),
                         hv(direction="stand_aside", conviction=1),
                         _sk(0.5), _sk(0.5))
    assert out["direction"] == "up"
    aside = [c for c in out["contributions"] if not c["counted"]]
    assert len(aside) == 1 and aside[0]["source"] == "human"


def test_both_standing_aside_yields_stand_aside_not_a_fabricated_call():
    out = B.centaur_view(mv(direction="stand_aside", conviction=1),
                         hv(direction="stand_aside", conviction=1),
                         _sk(0.5), _sk(0.5))
    assert out["direction"] == "stand_aside" and out["scores"] == {}


def test_the_merge_reports_every_input_so_it_can_be_argued_with():
    out = B.centaur_view(mv(), hv(direction="down"), _sk(0.6), _sk(0.4))
    assert set(out["weights"]) == {"machine", "human"}
    assert all("basis" in w for w in out["weights"].values())
    assert len(out["contributions"]) == 2


def test_a_view_cannot_be_filed_against_a_day_that_never_traded():
    # 2026-08-08 is a Saturday. A view there can never be scored, and would sit
    # in the record as a call nobody made. This guard exists because the first
    # row ever written to the log was exactly that.
    with pytest.raises(ValueError, match="not a trading session"):
        mv(session="2026-08-08")
    assert L.is_trading_session("2026-08-07") is True
    assert L.is_trading_session("not-a-date") is False
