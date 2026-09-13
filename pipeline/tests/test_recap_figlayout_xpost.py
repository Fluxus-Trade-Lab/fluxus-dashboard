"""F1 (schematic labels never overlap) and P1 (X post rules): each proven red on an injected sample first."""
import pytest

from pipeline.content.recap import figlayout
from pipeline.content.recap.visual_figs import FIGS
from pipeline.content.recap.xpost import LIMIT, P2_MAX, compose, p1, p2, x_length

OVERLAP_SVG = ('<svg class="tell" viewBox="0 0 1000 380">'
               '<text class="lab-acc" x="113.6" y="71.6" text-anchor="start">20 EMA · falling</text>'
               '<text x="279.2" y="81.2" text-anchor="middle">pop sold at the 20</text></svg>')


def test_f1_red_on_the_measured_0911_overlap_shape():
    r = figlayout.check_svg_labels(OVERLAP_SVG)
    assert not r["ok"] and r["overlaps"] == [("20 EMA · falling", "pop sold at the 20")]


def test_f1_green_when_labels_are_apart():
    apart = OVERLAP_SVG.replace('y="81.2"', 'y="120.0"')
    assert figlayout.check_svg_labels(apart)["ok"]


def test_f1_red_when_no_schematic_is_found():
    assert not figlayout.check_svg_labels("<p>no figure</p>")["ok"]


def test_cjk_counts_full_width():
    assert figlayout.text_width("左边", 13) == 26 and figlayout.text_width("ab", 10) == 12


@pytest.mark.parametrize("name", sorted(FIGS))
@pytest.mark.parametrize("lang", ["EN", "ZH"])
def test_every_schematic_resolves_to_no_overlaps(name, lang):
    assert figlayout.check_spec_labels(FIGS[name](lang))["ok"], figlayout.check_spec_labels(FIGS[name](lang))


def test_without_resolve_the_left_side_of_v_labels_do_collide(monkeypatch):
    monkeypatch.setattr(figlayout, "resolve", lambda spec, gap=4.0: spec)
    raw = FIGS["left_side_of_v"]("EN")
    assert not figlayout.check_spec_labels(raw)["ok"]  # positive control: avoidance is doing real work


CONTENT = {"big_picture": "Four down days ended with a gap up that stuck: <b>SPY +0.85%, QQQ +0.87%, both back above the 50-day</b> ◇. "
                          "Net advances +641.",
           "led": [["AI hardware", "+12.4%", "HPE"]],
           "x_posts": {"lead": "SPY and QQQ reclaimed the 50-day; RSP and IWM did not.", "cashtags": ["HPE", "DELL"]}}
GOOD = "SPY +0.85% and QQQ +0.87% reclaimed the 50-day.\n\n$HPE $DELL"
BP_0910 = ("A fourth straight down day, and the first close under the 50-day for both <b>SPY (−0.60%) and QQQ (−1.06%)</b>. "
           "Producer prices ran hot on the headline.")
BP_0911 = ("Four down days ended with a gap up that stuck: <b>SPY +0.85%, QQQ +0.87%, both back above the 50-day</b> — on a CPI print "
           "that ran hot, core +0.3% m/m against 0.2% expected. Bad data, higher prices.")


def test_p1_green_on_a_clean_post():
    r = p1(GOOD, CONTENT)
    assert r["ok"], r


def test_long_post_is_lead_then_big_picture_verbatim_then_cashtags():
    post = compose(CONTENT)
    lead, body, tags = post["text"].split("\n\n")
    assert lead == CONTENT["x_posts"]["lead"]
    assert body == "Four down days ended with a gap up that stuck: SPY +0.85%, QQQ +0.87%, both back above the 50-day. Net advances +641."
    assert tags == "$HPE $DELL"
    assert p1(post["text"], CONTENT)["ok"]


def test_null_lead_starts_with_big_picture():
    post = compose({**CONTENT, "x_posts": {"lead": None, "cashtags": ["HPE", "DELL"]}})
    assert post["text"].startswith("Four down days") and post["lead"] is None


def test_p2_red_on_the_0910_control():
    r = p2("SPY and QQQ closed under the 50-day together for the first time in the slide.", BP_0910)
    assert not r["ok"] and r["similarity"] == pytest.approx(0.46, abs=0.01) and P2_MAX == 0.4


def test_p2_green_on_the_0911_control():
    r = p2("SPY and QQQ reclaimed the 50-day; RSP and IWM did not.", BP_0911)
    assert r["ok"] and r["similarity"] == pytest.approx(0.28, abs=0.01)


def test_p2_does_not_apply_without_a_lead():
    assert p2(None, BP_0910) == {"ok": True, "similarity": None}


@pytest.mark.parametrize("inject, expect", [
    (" Andy said so.", "names Andy"),
    (" We like it.", "first person"),
    (" Worth $12,400 now.", "dollar"),
    (" #stocks", "hashtag"),
    (" 🚀", "emoji"),
    (" https://example.com", "link"),
    (" Subscribe for more.", "call to action"),
    (" Per the Revere roundup.", "Revere"),
    (" Breadth 77.7% strong.", "numbers not in content"),
    (" <b>SPY</b>", "leftover"),
    (" held ◇", "leftover"),
    (" $SWKS $SMTC $NVDA", "cashtags"),
])
def test_p1_red_on_each_injection(inject, expect):
    r = p1(GOOD + inject, CONTENT)
    assert not r["ok"] and any(expect in h for h in r["hits"]), r


def test_p1_red_on_a_single_cashtag():
    r = p1("SPY +0.85% reclaimed the 50-day.\n\n$HPE", CONTENT)
    assert not r["ok"] and any("cashtags" in h for h in r["hits"])


def test_p1_red_over_1500_and_counts_minus_sign_double():
    assert LIMIT == 1500
    long = "SPY +0.85% and QQQ +0.87% reclaimed the 50-day. " * 32 + "\n\n$HPE $DELL"
    assert x_length(long) > LIMIT and not p1(long, CONTENT)["ok"]
    assert p1("SPY +0.85% and QQQ +0.87% reclaimed the 50-day. " * 20 + "\n\n$HPE $DELL", CONTENT)["ok"]  # ~1,000 chars passes now
    assert x_length("−") == 2 and x_length("—") == 1 and x_length("https://a.b/c") == 23
    assert x_length("a" * LIMIT) == LIMIT


def test_p1_cashtags_are_not_dollar_amounts():
    assert p1("SPY +0.85%.\n\n$HPE $DELL $SWKS $SMTC", CONTENT)["ok"]
