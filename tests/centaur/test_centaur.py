"""The centaur layer: what each of the three properties refuses to do."""
import pytest

from pipeline.centaur import blend as B
from pipeline.centaur import log as L
from pipeline.centaur import skill as S
from pipeline.reference import power as PW


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
    assert f"{S.MIN_SCORED} needed" in s["note"]
    # The note must say not-enough FOR WHAT, or the gate is a bare number again.
    assert "60% edge" in s["note"] and "80% power" in s["note"]
    assert s["power"]["status"] == "underpowered"


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

def _sk(hr, n=None):
    """A skill dict at, by default, exactly the sample the gate demands.

    Pinned to S.MIN_SCORED rather than a literal. The gate is now derived from
    a named effect size, so it moves when that claim changes -- and a helper
    holding a stale literal would have silently turned every "measured" case in
    this file into an "unproven" one, which is how these tests started failing
    when MIN_SCORED went from an invented 20 to a computed 153.
    """
    return {"enough": (S.MIN_SCORED if n is None else n) >= S.MIN_SCORED,
            "hit_rate": hr, "note": "thin"}


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


# ------------------------------------------- the consultation ledger

def _pair(session, human, machine):
    return {"session": session, "human": hv(session=session, direction=human),
            "machine": mv(session=session, direction=machine)}


def test_a_merge_that_saves_a_wrong_human_call_is_a_positive_consultation():
    p = [_pair("2026-08-03", human="down", machine="up")]
    c = S.consultations(p, {"2026-08-03": "up"})
    assert c["n_positive"] == 1 and c["n_negative"] == 0


def test_a_merge_that_breaks_a_right_human_call_is_the_automation_bias_case():
    p = [_pair("2026-08-03", human="up", machine="down")]
    c = S.consultations(p, {"2026-08-03": "up"})
    assert c["n_negative"] == 1 and c["automation_bias_rate"] == 1.0


def test_agreement_is_not_a_consultation_either_way():
    p = [_pair("2026-08-03", human="up", machine="up"),
         _pair("2026-08-04", human="down", machine="down")]
    c = S.consultations(p, {"2026-08-03": "up", "2026-08-04": "up"})
    assert c["n_positive"] == c["n_negative"] == 0
    assert c["n_agreed_right"] == 1 and c["n_agreed_wrong"] == 1


def test_an_abstention_is_not_an_override_so_it_gets_no_verdict():
    p = [_pair("2026-08-03", human="stand_aside", machine="up")]
    assert S.consultations(p, {"2026-08-03": "up"})["n_scored_pairs"] == 0


def test_both_wrong_in_different_directions_is_not_scored_as_bias():
    # The merge did not break anything that was right.
    p = [_pair("2026-08-03", human="up", machine="down")]
    c = S.consultations(p, {"2026-08-03": "range"})
    assert c["n_negative"] == 0 and c["n_agreed_wrong"] == 1


def test_an_explicit_merged_direction_overrides_the_machine_stand_in():
    # The merge can land on the human even when it disagrees with the machine;
    # the ledger must score what the MERGE did, not what the machine said.
    p = [_pair("2026-08-03", human="up", machine="down")]
    c = S.consultations(p, {"2026-08-03": "up"}, merged={"2026-08-03": "up"})
    assert c["n_negative"] == 0 and c["n_agreed_right"] == 1


def test_pressure_split_records_the_condition_the_literature_flags():
    rows = [hv(asof="2026-08-03T08:00:00-04:00", session="2026-08-03"),
            hv(asof="2026-08-04T11:30:00-04:00", session="2026-08-04")]
    u = S.under_pressure(rows)
    assert u["calm"] == 1 and u["live"] == 1


# ------------------------------------------------- amendment, before the bell

def test_a_view_can_be_amended_before_the_open_and_the_original_is_kept(tmp_path):
    p = tmp_path / "v.jsonl"
    L.append(hv(direction="range", conviction=3), p)
    out = L.amend(hv(direction="range", conviction=2,
                     asof="2026-08-03T08:10:00-04:00"), "08:10", p)
    assert out["was_conviction"] == 3 and out["now_conviction"] == 2
    rows = L.read(p)
    assert len(rows) == 2                       # nothing deleted
    assert rows[0]["amended"] is True
    assert rows[1]["amends"] == rows[0]["asof"]


def test_amendment_is_refused_once_the_tape_has_moved(tmp_path):
    p = tmp_path / "v.jsonl"
    L.append(hv(direction="range", conviction=3), p)
    with pytest.raises(ValueError, match="opened at"):
        L.amend(hv(direction="up", conviction=3), "09:31", p)


def test_the_live_view_is_the_amendment_not_the_superseded_one(tmp_path):
    p = tmp_path / "v.jsonl"
    L.append(hv(direction="range", conviction=3), p)
    L.amend(hv(direction="range", conviction=2,
               asof="2026-08-03T08:10:00-04:00"), "08:10", p)
    # append must now see the amendment as the one on record
    assert L.append(hv(direction="down", conviction=1), p) is False
    live = [r for r in L.read(p) if not r.get("amended")]
    assert len(live) == 1 and live[0]["conviction"] == 2


def test_amending_something_that_was_never_logged_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="nothing on record"):
        L.amend(hv(), "08:00", tmp_path / "v.jsonl")


def test_the_thin_note_reads_as_a_sentence_at_every_sample_size():
    """A guard is only as good as the string that reports it.

    n=2 once produced "only an edge of no size is visible" -- the third time in
    this project a correct check was let down by its own prose.
    """
    for n in (1, 2, 3, 6, 20, 60):
        note = S._thin_note(n, PW.verdict(n, S.CLAIMED_EDGE, S.NULL_RATE))
        assert "edge of no size" not in note
        assert "and no edge of any size is visible" in note or "or better is visible" in note
        assert f"only {n} scored views" in note


def test_the_gate_is_derived_from_a_named_effect_not_a_bare_number():
    assert S.MIN_SCORED == PW.sessions_needed(S.CLAIMED_EDGE, S.NULL_RATE)
    # Claiming a smaller edge must cost more sessions, or the gate is backwards.
    assert PW.sessions_needed(0.55) > S.MIN_SCORED > PW.sessions_needed(0.70)
