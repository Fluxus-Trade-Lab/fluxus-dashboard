"""L2's body tier must be measured on prose, not on table text in the same face.

Chinese table cells are PingFang, exactly like Chinese prose. Once a sheet carries
more table text than prose — which it did as soon as the 2026-09-24 type rule put
every table at 9.5pt — the unfiltered "most common size in the body font" reported
9.5 and reddened a correctly set page.

Both directions are exercised: the fix must not report a healthy page red, and it
must still report a genuinely shrunken body red.
"""
from pipeline.content.recap.pages import check_true_size

BODY = "PingFangSC-Regular"
MONO = "IBMPlexMono-Regular"


def test_table_text_in_the_body_face_no_longer_masks_the_body_size():
    """The shape that broke: 9.5pt table CJK outnumbers 10.5pt prose CJK."""
    tiers = {(BODY, 10.5): 400, (BODY, 9.5): 900, (MONO, 9.5): 500}
    r = check_true_size(tiers, "ZH")
    assert r["body_pt"] == 10.5, r
    assert r["ok"], r["hits"]


def test_a_body_that_really_shrank_still_reds():
    """Positive control: no glyph of the body face is above the floor at all."""
    tiers = {(BODY, 9.5): 1300, (MONO, 9.5): 500}
    r = check_true_size(tiers, "ZH")
    assert not r["ok"] and any("body" in h for h in r["hits"]), r


def test_a_body_set_slightly_wrong_still_reds():
    tiers = {(BODY, 11.5): 900, (BODY, 9.5): 400, (MONO, 9.5): 500}
    r = check_true_size(tiers, "ZH")
    assert not r["ok"] and r["body_pt"] == 11.5, r


def test_a_table_under_the_minimum_still_reds():
    tiers = {(BODY, 10.5): 900, (MONO, 7.9): 800}
    r = check_true_size(tiers, "ZH")
    assert not r["ok"] and any("table" in h for h in r["hits"]), r


def test_english_is_unaffected_because_its_faces_differ():
    tiers = {("IBMPlexSans-Regular", 10.5): 800, (MONO, 9.5): 900}
    r = check_true_size(tiers, "EN")
    assert r["ok"] and r["body_pt"] == 10.5 and r["table_pt"] == 9.5, r
