"""L2: true printed size read from glyph font sizes. Tier counts below are pdfminer readings of real PDFs
(pages 1–2): the shipped 10.5pt/9.5pt build green, the shrunk W37 EN and the earlier 12pt build red."""
from pipeline.content.recap import pages
from pipeline.content.recap.pages import check_true_size, check_true_size_pdf

W37_EN_SHRUNK = {("IBMPlexSans-Regular", 10.2): 843, ("IBMPlexMono-Regular", 9.8): 595, ("IBMPlexSans-Regular", 9.8): 216,
                 ("IBMPlexMono-Regular", 8.2): 181, ("IBMPlexMono-Regular", 9.7): 60}
BUILD_12PT_EN = {("IBMPlexSans-Regular", 12.0): 721, ("IBMPlexMono-Regular", 11.5): 445, ("IBMPlexSans-Regular", 11.5): 216,
                 ("IBMPlexMono-Regular", 9.6): 172}
SHIPPED_EN = {("IBMPlexSans-Regular", 10.5): 721, ("IBMPlexMono-Regular", 9.5): 445, ("IBMPlexSans-Regular", 9.5): 216,
              ("IBMPlexMono-Regular", 8.4): 172}
SHIPPED_ZH = {("PingFangSC-Regular", 10.5): 216, ("IBMPlexSans-Regular", 9.5): 216, ("IBMPlexMono-Regular", 9.5): 178,
              ("PingFangSC-Regular", 9.5): 84}


def test_l2_green_on_the_shipped_size():
    assert check_true_size(SHIPPED_EN, "EN") == {"ok": True, "body_pt": 10.5, "table_pt": 9.5, "hits": []}
    assert check_true_size(SHIPPED_ZH, "ZH")["ok"]


def test_l2_red_on_the_shrunk_w37_en():
    r = check_true_size(W37_EN_SHRUNK, "EN")
    assert not r["ok"] and r["body_pt"] == 10.2 and "body 10.2pt" in r["hits"][0]


def test_l2_red_on_the_earlier_12pt_build():
    r = check_true_size(BUILD_12PT_EN, "EN")
    assert not r["ok"] and r["body_pt"] == 12.0


def test_l2_zh_body_is_read_from_pingfang_not_latin():
    zh_shrunk = {**SHIPPED_ZH, ("PingFangSC-Regular", 10.5): 0, ("PingFangSC-Regular", 9.0): 300}
    assert not check_true_size(zh_shrunk, "ZH")["ok"]


def test_l2_red_when_only_the_table_tier_is_small():
    r = check_true_size({("IBMPlexSans-Regular", 10.5): 700, ("IBMPlexMono-Regular", 9.4): 400}, "EN")
    assert not r["ok"] and r["hits"] == ["table 9.4pt (< 9.5)"]


def test_l2_body_tolerance_is_a_tenth_of_a_point():
    assert check_true_size({("IBMPlexSans-Regular", 10.4): 9, ("IBMPlexMono-Regular", 9.5): 9}, "EN")["ok"]
    assert not check_true_size({("IBMPlexSans-Regular", 10.3): 9, ("IBMPlexMono-Regular", 9.5): 9}, "EN")["ok"]


def test_l2_fails_closed_without_a_reader(monkeypatch):
    def boom(*a, **k):
        raise ImportError("no pdfminer")
    monkeypatch.setattr(pages, "size_tiers", boom)
    r = check_true_size_pdf("missing.pdf", "EN")
    assert not r["ok"] and "not installed" in r["hits"][0]
