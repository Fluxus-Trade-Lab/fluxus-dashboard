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
