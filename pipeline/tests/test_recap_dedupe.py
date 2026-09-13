"""R1 (topic ledger) and R2 (same-week text): each rule proven red on an injected sample before green is trusted."""
import difflib

import pytest

from pipeline.content.recap import dedupe as dd


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "edu_topics.jsonl"
    dd.seed(p)
    return p


def opt(key, concept, en, zh):
    return {"key": key, "concept": concept, "title_en": en, "title_zh": zh}


def test_seed_holds_the_eight_spec_topics_once(ledger):
    dd.seed(ledger)
    entries = dd.load_ledger(ledger)
    assert len([e for e in entries if e["issue"] == "spec§5"]) == 8


def test_r1_red_on_a_spec_concept(ledger):
    hits = dd.r1("2026-09-15", "2026-09-15", False, [opt("A", "vcp", "Coils", "收缩")], dd.load_ledger(ledger))
    assert hits and hits[0]["why"] == ["concept"]


def test_r1_red_on_a_similar_title_with_a_new_concept(ledger):
    hits = dd.r1("2026-09-15", "2026-09-15", False, [opt("B", "new_tag", "Failed Breakouts and Swing Failures", "别的")],
                 dd.load_ledger(ledger))
    assert hits and any(w.startswith("title_en") for w in hits[0]["why"])


def test_r1_red_inside_20_sessions_green_outside(ledger):
    dd.add_entry({"date": "2026-09-10", "issue": "2026-09-10", "key": "A", "title_en": "Track RS", "title_zh": "盯 RS",
                  "concept": "rs_before_price"}, ledger)
    L = dd.load_ledger(ledger)
    assert dd.r1("2026-09-15", "2026-09-15", False, [opt("A", "rs_before_price", "Other", "其它")], L)
    assert dd.sessions_between("2026-09-10", "2026-10-20") > 20
    assert not dd.r1("2026-10-20", "2026-10-20", False, [opt("A", "rs_before_price", "Other", "其它")], L)


def test_r1_weekly_A_red_on_same_week_daily_A_but_B_is_not_held_to_that(ledger):
    dd.add_entry({"date": "2026-09-11", "issue": "2026-09-11", "key": "A", "title_en": "Left side", "title_zh": "左边",
                  "concept": "left_side_of_v"}, ledger)
    L = dd.load_ledger(ledger)
    week = ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]
    assert dd.r1("2026-W37", "2026-09-11", True, [opt("A", "left_side_of_v", "Another", "别的")], L, week)
    assert not dd.r1("2026-W37", "2026-09-11", True, [opt("B", "left_side_of_v", "Another", "别的")], L, week)


def test_r1_ignores_the_issue_itself(ledger):
    dd.add_entry({"date": "2026-09-11", "issue": "2026-09-11", "key": "A", "title_en": "Left side", "title_zh": "左边",
                  "concept": "left_side_of_v"}, ledger)
    assert not dd.r1("2026-09-11", "2026-09-11", False, [opt("A", "left_side_of_v", "Left side", "左边")], dd.load_ledger(ledger))


def content(rules, tomorrow, bp="Stocks fell. More text."):
    return {"rules": rules, "tomorrow": tomorrow, "big_picture": bp}


BASE_RULES = ["Rule one about bonds", "Rule two about crude", "Rule three", "Rule four", "Rule five", "Rule six",
              "Never serious trouble until S&P breaks the 200-day — well above it"]


def test_r2_red_on_a_repeated_rule():
    prior = content(BASE_RULES, ["Watch CPI"])
    cur = content(["Rule one about bonds"] + ["x%d unique line" % i for i in range(5)]
                  + ["Never serious trouble until S&P breaks the 200-day — a different read"], ["FOMC"], "Different start.")
    hits = dd.r2({"EN": cur}, False, [("2026-09-10", False, {"EN": prior})])
    assert [h["item"] for h in hits] == ["rule 1"]


def test_r2_ignores_the_fixed_rule7_opening():
    prior = content(["p%d aaa" % i for i in range(6)] + ["Never serious trouble until S&P breaks the 200-day — below the 50"], [])
    cur = content(["c%d zzz" % i for i in range(6)] + ["Never serious trouble until S&P breaks the 200-day — weekly bar held"], [], "New.")
    assert dd.r2({"EN": cur}, False, [("d", False, {"EN": prior})]) == []


def test_r2_weekly_threshold_is_looser_than_daily():
    a = "p" * 40 + "q" * 10  # 40 shared of 50 → ratio exactly 0.80
    b = "p" * 40 + "z" * 10
    r = difflib.SequenceMatcher(None, dd.norm(a), dd.norm(b)).ratio()
    assert 0.75 <= r < 0.85, r  # precondition: the pair sits between the two thresholds
    prior = content(["p%d" % i for i in range(6)], [a])
    cur = content(["c%d" % i for i in range(6)], [b], "Other.")
    assert dd.r2({"EN": cur}, False, [("2026-09-11", False, {"EN": prior})])       # daily vs daily → red
    assert not dd.r2({"EN": cur}, True, [("2026-09-11", False, {"EN": prior})])    # weekly vs daily → green


def test_first_sentence_en_and_zh():
    assert dd.first_sentence("Four down days ended. Then more.") == "Four down days ended."
    assert dd.first_sentence("跌了四天。周五高开。") == "跌了四天。"
