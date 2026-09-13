"""L2: true printed size read from glyph font sizes. Tier counts below are the pdfminer readings of real PDFs
(pages 1–2): the shrunk W37 EN (0.849) must go red, the 12pt dailies green."""
import sys

import pytest

from pipeline.content.recap import pages
from pipeline.content.recap.pages import check_true_size, check_true_size_pdf

W37_EN_SHRUNK = {("IBMPlexSans-Regular", 10.2): 843, ("IBMPlexMono-Regular", 9.8): 595, ("IBMPlexSans-Regular", 9.8): 216,
                 ("IBMPlexMono-Regular", 8.2): 181, ("IBMPlexMono-Regular", 9.7): 60}
D0911_EN = {("IBMPlexSans-Regular", 12.0): 721, ("IBMPlexMono-Regular", 11.5): 445, ("IBMPlexSans-Regular", 11.5): 216,
            ("IBMPlexMono-Regular", 9.6): 172, ("IBMPlexMono-Regular", 9.7): 60}
D0911_ZH = {("PingFangSC-Regular", 12.0): 216, ("IBMPlexSans-Regular", 11.5): 216, ("IBMPlexMono-Regular", 11.5): 178,
            ("IBMPlexSans-Regular", 12.0): 104, ("PingFangSC-Regular", 11.5): 84}


def test_l2_red_on_the_shrunk_w37_en():
    r = check_true_size(W37_EN_SHRUNK, "EN")
    assert not r["ok"] and r["body_pt"] == 10.2 and r["table_pt"] == 9.8 and len(r["hits"]) == 2


def test_l2_green_on_the_12pt_dailies():
    assert check_true_size(D0911_EN, "EN") == {"ok": True, "body_pt": 12.0, "table_pt": 11.5, "hits": []}
    assert check_true_size(D0911_ZH, "ZH")["ok"]


def test_l2_zh_body_is_read_from_pingfang_not_latin():
    zh_shrunk = {**D0911_ZH, ("PingFangSC-Regular", 12.0): 0, ("PingFangSC-Regular", 10.2): 300}
    assert not check_true_size(zh_shrunk, "ZH")["ok"]


def test_l2_red_when_only_the_table_tier_is_small():
    r = check_true_size({("IBMPlexSans-Regular", 12.0): 700, ("IBMPlexMono-Regular", 10.4): 400}, "EN")
    assert not r["ok"] and r["hits"] == ["table 10.4pt (< 10.5)"]


def test_l2_body_tolerance_is_a_tenth_of_a_point():
    assert check_true_size({("IBMPlexSans-Regular", 11.9): 9, ("IBMPlexMono-Regular", 11.5): 9}, "EN")["ok"]
    assert not check_true_size({("IBMPlexSans-Regular", 11.8): 9, ("IBMPlexMono-Regular", 11.5): 9}, "EN")["ok"]


def test_l2_fails_closed_without_a_reader(monkeypatch):
    def boom(*a, **k):
        raise ImportError("no pdfminer")
    monkeypatch.setattr(pages, "size_tiers", boom)
    r = check_true_size_pdf("missing.pdf", "EN")
    assert not r["ok"] and "not installed" in r["hits"][0]
