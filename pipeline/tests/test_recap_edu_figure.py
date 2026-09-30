"""A lesson's picture must be its own, or the reuse must be stated.

2026-09-23 shipped the concept `leaders_vs_index_on_a_red_day` drawing
`equal_weight_split` — cap-weighted against equal-weight breaking a 50-day, over
weeks. The lesson was about one session, and none of the figure's four labels
appear in its text. The reuse was argued in a commit message and never checked
against the paragraph, so nothing caught it until Andy looked at the page.
"""
import pytest

from pipeline.content.recap.visual import pick_edu
from pipeline.content.recap.visual_figs import FIGS


def _edu(**over):
    o = {"key": "A", "concept": "three_tight_closes", "figure": "three_tight_closes",
         "title": "t", "why": "w", "body": "b"}
    o.update(over)
    return {"chosen": "A", "options": [o]}


def test_a_matching_figure_passes():
    assert pick_edu(_edu(), "A")["figure"] == "three_tight_closes"


def test_a_borrowed_figure_reds():
    with pytest.raises(SystemExit) as e:
        pick_edu(_edu(concept="leaders_vs_index_on_a_red_day", figure="equal_weight_split"), "A")
    assert "not this concept's" in str(e.value)


def test_a_borrowed_figure_passes_once_the_reuse_is_stated():
    out = pick_edu(_edu(concept="leaders_vs_index_on_a_red_day", figure="equal_weight_split",
                        figure_reuse_reason="the lesson names cap-weighted and equal-weight"), "A")
    assert out["figure"] == "equal_weight_split"


def test_the_red_day_lesson_now_has_its_own_builder():
    assert "leaders_vs_index_on_a_red_day" in FIGS
    for lang in ("EN", "ZH"):
        spec = FIGS["leaders_vs_index_on_a_red_day"](lang)
        assert spec["items"], lang


def test_every_registered_builder_still_draws_in_both_languages():
    """The asserts inside each builder are its real contract; run them all."""
    for name, fn in FIGS.items():
        for lang in ("EN", "ZH"):
            assert fn(lang)["items"], (name, lang)


# ---------------------------------------------------------------- 2026-09-30 (T-0930-30)
# Andy, looking at the 09-29 issue: 「教学图和教学好像有点重复。」 The lesson there borrowed
# `left_side_of_v` and justified it by saying every label on the diagram was a phrase the
# lesson used — which satisfied the 2026-09-24 judgement and still printed the same
# paragraph twice. The half of that judgement that allowed "the body uses the label" is
# retired; the body now has to say it in its own words or the figure is an echo.
from pipeline.content.recap.visual import echoed_labels  # noqa: E402


def test_the_body_may_not_read_the_diagram_labels_back_out():
    """Positive control: the retired 09-29 pairing, in both languages."""
    en = {"figure": "left_side_of_v", "title": "t", "why": "w",
          "body": "On the left side the pop sold at the 20 is the first form of it."}
    assert echoed_labels(en, "EN") == ["pop sold at the 20"]
    zh = {"figure": "base_before_the_catalyst", "title": "t", "why": "w",
          "body": "这一课讲的是右侧向均线收紧这件事。"}
    assert echoed_labels(zh, "ZH") == ["右侧向均线收紧"]


def test_one_word_panel_names_are_chrome_not_recitation():
    """`pivot` / `TIGHT` / 紧 appear in any lesson about bases; only phrases count."""
    en = {"figure": "right_side_quality", "title": "The tight handle",
          "why": "same pivot", "body": "A tight right side under the pivot."}
    assert echoed_labels(en, "EN") == []


def test_pick_edu_reds_when_the_lesson_narrates_its_own_figure():
    with pytest.raises(SystemExit) as e:
        pick_edu(_edu(concept="left_side_of_v", figure="left_side_of_v",
                      body="the pop sold at the 20 is the first form of it"), "A", "EN")
    assert "reads the diagram's own labels back out" in str(e.value)


def test_pick_edu_without_a_language_still_skips_the_echo_check():
    """Call sites that have no language (unit fixtures, older callers) keep working."""
    assert pick_edu(_edu(concept="left_side_of_v", figure="left_side_of_v",
                         body="the pop sold at the 20"), "A")["figure"] == "left_side_of_v"


def test_the_two_2026_09_29_builders_exist_and_are_their_own_concepts():
    for name in ("base_before_the_catalyst", "right_side_quality"):
        assert name in FIGS
        for lang in ("EN", "ZH"):
            assert FIGS[name](lang)["items"], (name, lang)
