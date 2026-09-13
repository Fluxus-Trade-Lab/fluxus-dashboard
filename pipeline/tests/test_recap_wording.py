"""W1: "week" shorthand that reads as "weak" — red on injected samples first, green on the allowed forms."""
import pytest

from pipeline.content.recap.wording import w1_hits, w1_text_hits, week_weak_review


@pytest.mark.parametrize("text", [
    "theme week, the worst on the board",
    "industry week; Uranium & Nuclear theme to Lagging",
    "IBIT week; CRCL −11.2%, HOOD −7.8%",
    "week −9.4% · Weakening → Lagging",
    "Rare Earth week −10.5%; Coal −2.0%",
    "Semis Broad theme +2.2%. week; more",
])
def test_w1_red(text):
    assert w1_text_hits(text), text


@pytest.mark.parametrize("text", [
    "worst Dow week since March this week",
    "next week the Fed decides",
    "the week closed lower",
    "down 1.5% on the week",
    "−10.5% over the week (theme)",
    "week of September 8–11",
    "1-week −9.4% · Weakening → Lagging",
    "18.7% above its 10-week EMA",
    "Weekly consolidation, daily pullback",
    "software was weak",
])
def test_w1_green(text):
    assert w1_text_hits(text) == [], (text, w1_text_hits(text))


def test_w1_walks_content_but_skips_labels():
    content = {"led": [["Uranium", "−9.4%", "industry week; to Lagging"]], "labels": {"x": "Next Week · Sep 14"}}
    hits = w1_hits(content)
    assert len(hits) == 1 and "industry week" in hits[0]["matches"][0]


def test_week_weak_review_flags_transcript_lines():
    md = "**[00:02]** Russell continues to be weak on the week. Gold held.\n"
    content = {"big_picture": "Russell continues to be weak. Breadth improved."}
    r = week_weak_review(content, md)
    assert r["transcript_week_weak"] == 1
    assert r["content"] and r["content"][0]["from_transcript"]
