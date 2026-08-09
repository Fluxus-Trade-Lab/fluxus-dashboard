"""Anchoring — measured, not assumed."""
from pipeline.centaur import anchoring as A


def hv(session="2026-08-03", asof="2026-08-03T08:00:00-04:00", source="human"):
    return {"session": session, "asof": asof, "source": source}


def push(session="2026-08-03", at="2026-08-03T07:30:00-04:00", kind="full"):
    return {"session": session, "pushed_at": at, "kind": kind}


def test_a_view_filed_after_the_brief_went_out_is_anchored():
    assert A.classify(hv(asof="2026-08-03T08:00:00-04:00"), [push()]) == A.ANCHORED


def test_a_view_filed_before_it_is_independent():
    assert A.classify(hv(asof="2026-08-03T07:00:00-04:00"), [push()]) == A.INDEPENDENT


def test_with_no_brief_published_there_was_nothing_to_anchor_to():
    assert A.classify(hv(), []) == A.INDEPENDENT


def test_the_prompt_only_card_does_not_anchor_because_it_carries_no_answer():
    assert A.classify(hv(), [push(kind="prompt")]) == A.INDEPENDENT


def test_a_missing_timestamp_is_unknown_never_quietly_clean():
    assert A.classify({**hv(), "asof": None}, [push()]) == A.UNKNOWN


def test_the_machine_cannot_be_anchored_by_its_own_brief():
    assert A.classify(hv(source="machine"), [push()]) == A.INDEPENDENT


def test_the_earliest_full_push_is_the_one_that_could_have_anchored():
    ps = [push(at="2026-08-03T16:30:00-04:00"), push(at="2026-08-03T07:30:00-04:00")]
    assert A.first_full_push(ps)["2026-08-03"] == "2026-08-03T07:30:00-04:00"


def test_recording_a_push_is_idempotent_per_session_and_kind(tmp_path):
    p = tmp_path / "pushes.jsonl"
    assert A.record_push("2026-08-03", "2026-08-03T07:30:00-04:00", path=p) is True
    assert A.record_push("2026-08-03", "2026-08-03T09:00:00-04:00", path=p) is False
    assert A.record_push("2026-08-03", "2026-08-03T07:00:00-04:00", "prompt", path=p) is True
    assert len(A.read(p)) == 2


def test_split_groups_only_human_views():
    rows = [hv(), hv(source="machine"), hv(asof="2026-08-03T06:00:00-04:00")]
    s = A.split(rows, [push()])
    assert len(s[A.ANCHORED]) == 1 and len(s[A.INDEPENDENT]) == 1
