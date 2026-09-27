"""T-0927-35: session_commentary coverage self-check — Andy 09-27 「周五缺一格，是这周的个例，
那 ok，每周如此，那就是问题」. missing_dates (no export) is benign; a session with real messages
that never shows up in session_commentary is the shape he called a problem. Positive control built
by removing the one commentary sentence that actually carries a session's material (Gary 08-25: a
check that's never proven red is not proven at all)."""
from pipeline.content.recap.wording import (andy_coverage_review, coverage_streak, coverage_streak_for_issue,
                                             load_coverage_ledger, record_coverage)


def _pack(sessions: dict[str, list[str]], missing: list[str] | None = None) -> dict:
    messages = [{"session": d, "text": t} for d, texts in sessions.items() for t in texts]
    return {"andy": {"messages": messages, "missing_dates": missing or []}}


def test_all_sessions_covered_when_commentary_echoes_each_one():
    pack = _pack({"2026-09-21": ["Sellers stepped in right at the 50-day and got rejected"],
                  "2026-09-22": ["QQQ held the open range low all session"]})
    content = {"session_commentary": ["Sellers rejected at the 50-day.", "QQQ held its open range low."]}
    r = andy_coverage_review(pack, content)
    assert r["uncovered"] == []
    assert r["n_covered"] == 2 and r["n_total"] == 2


def test_missing_dates_are_not_counted_as_uncovered():
    pack = _pack({"2026-09-21": ["Sellers stepped in right at the 50-day and got rejected"]}, missing=["2026-09-23"])
    content = {"session_commentary": ["Sellers rejected at the 50-day."]}
    r = andy_coverage_review(pack, content)
    assert r["missing_dates"] == ["2026-09-23"]
    assert r["uncovered"] == []
    assert r["n_total"] == 2  # 1 real session + 1 missing-date session


def test_positive_control_removing_the_only_matching_sentence_flags_the_session():
    """W39 shape: Friday had 25 real messages, session_commentary said nothing about that session."""
    pack = _pack({"2026-09-24": ["Breadth turned negative into the close, laggards led"],
                  "2026-09-25": ["Dow made a new high on strong volume, BE broke out to the right side"]})
    content_with_friday = {"session_commentary": ["Breadth turned negative into the close.",
                                                   "Dow made a new high on strong volume."]}
    clean = andy_coverage_review(pack, content_with_friday)
    assert clean["uncovered"] == []

    content_missing_friday = {"session_commentary": ["Breadth turned negative into the close."]}
    dirty = andy_coverage_review(pack, content_missing_friday)
    assert dirty["uncovered"] == ["2026-09-25"]
    assert dirty["n_covered"] == 1 and dirty["n_total"] == 2


def test_session_with_no_messages_is_not_flagged():
    pack = _pack({})
    r = andy_coverage_review(pack, {"session_commentary": []})
    assert r["uncovered"] == [] and r["n_total"] == 0


def test_a_short_paraphrase_covers_a_long_casual_session():
    """Regression, root cause found on the real 2026-W39 pack: the old symmetric SequenceMatcher
    ratio compares one commentary sentence against one raw message at a time, so it misses coverage
    that's assembled from several messages — no single message alone echoes enough of the paraphrase.
    Verified against this exact fixture: the pre-fix algorithm (`difflib.SequenceMatcher` ratio,
    threshold 0.30) scores every message below threshold (max 0.267) and marks the session uncovered;
    containment scores it 0.818 and marks it covered. Each message below carries only a slice of the
    paraphrase's content words — none alone crosses the old ratio threshold, but their union does."""
    pack = _pack({"2026-09-21": [
        "it is monday and my stance today is pretty simple honestly nothing fancy going on",
        "semiconductors are honestly the only sector i even care to look at this week",
        "i would rather sit tight than initiate anything new into a gap like this one",
        "just watching for now, this whole thing is not worth forcing a trade over",
    ]})
    content = {"session_commentary": ["Monday's stance was to add rather than initiate, "
                                       "with semiconductors the only thing worth watching."]}
    r = andy_coverage_review(pack, content)
    assert r["uncovered"] == [], "content words assembled across messages must count as coverage"


def test_coverage_streak_needs_two_in_a_row():
    assert coverage_streak([], []) == 0
    assert coverage_streak([], ["2026-09-19"]) == 1, "a single issue is not a problem (Andy 09-27)"
    prior_one_bad = [{"issue": "2026-W38", "uncovered": ["2026-09-19"]}]
    assert coverage_streak(prior_one_bad, ["2026-09-26"]) == 2
    prior_two_bad = [{"issue": "2026-W37", "uncovered": ["2026-09-12"]},
                      {"issue": "2026-W38", "uncovered": ["2026-09-19"]}]
    assert coverage_streak(prior_two_bad, ["2026-09-26"]) == 3


def test_coverage_streak_resets_after_a_clean_issue():
    prior = [{"issue": "2026-W37", "uncovered": ["2026-09-12"]},
             {"issue": "2026-W38", "uncovered": []}]
    assert coverage_streak(prior, ["2026-09-26"]) == 1


def test_record_coverage_round_trips_and_is_idempotent_per_issue(tmp_path):
    path = tmp_path / "andy_coverage.jsonl"
    record_coverage("2026-W38", ["2026-09-19"], path)
    record_coverage("2026-W39", [], path)
    record_coverage("2026-W38", ["2026-09-19"], path)  # a re-render of the same issue updates in place
    entries = load_coverage_ledger(path)
    assert [e["issue"] for e in entries] == ["2026-W38", "2026-W39"], "re-render must not reorder the ledger"
    assert coverage_streak(entries, ["doesn't matter, only the shape counts"]) == 1, "W39 was clean, streak resets"


def test_coverage_streak_for_issue_ignores_a_rerun_of_the_same_issue():
    """Review finding (branch agent/ops/T-0927-35): record_coverage runs before any L1/L2 gate, so an
    L2 font-size retry or `--edu B` re-render sees its own already-recorded entry and would otherwise
    double-count a first-time individual issue as "streak 2" — exactly what Andy's ruling forbids."""
    entries = [{"issue": "2026-W40", "uncovered": ["2026-10-02"]}]  # W40's own first render, already logged
    assert coverage_streak_for_issue(entries, "2026-W40", ["2026-10-02"]) == 1


def test_coverage_streak_for_issue_only_compares_same_cadence():
    """A clean daily sitting between two dirty weeklies must not reset the weekly streak — Andy's
    ruling is about a weekly pattern (「每周如此」), not about whatever ran in between."""
    entries = [{"issue": "2026-W38", "uncovered": ["2026-09-19"]},
               {"issue": "2026-09-24", "uncovered": []}]  # a clean daily in between, wrong cadence
    assert coverage_streak_for_issue(entries, "2026-W39", ["2026-09-26"]) == 2, \
        "the clean daily must not reset the weekly streak"

    entries_dirty_daily = [{"issue": "2026-W38", "uncovered": []},
                           {"issue": "2026-09-24", "uncovered": ["2026-09-24"]}]  # dirty daily, wrong cadence
    assert coverage_streak_for_issue(entries_dirty_daily, "2026-W39", ["2026-09-26"]) == 1, \
        "a dirty daily must not inflate the weekly streak either"
