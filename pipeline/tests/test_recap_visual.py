"""Visual review page: short-line JSON, page-text gates, schematic specs, and the type-area check."""
import json
import pathlib
import re

import pytest

from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import check_state_row, margin_overflow
from pipeline.content.recap.visual import html_text, jdump, strings, unjoin
from pipeline.content.recap.visual_figs import FIGS


def test_html_text_drops_script_and_style_but_keeps_svg_labels():
    frag = ('<style>.x{color:red}</style><script>var Andy=1</script>'
            '<p class="prose">Four down days</p><svg class="tell"><text x="1" y="2">pop sold at the 20</text></svg>')
    t = html_text(frag)
    assert "Four down days" in t and "pop sold at the 20" in t
    assert "Andy" not in t and "color:red" not in t


def test_gates_red_on_page_text_injections():
    base = '<p class="prose">SPY +0.85% reclaimed the 50-day</p>'
    assert run_gates(html_text(base))["ok"]
    for inj in ("<b>Andy</b> at 08:33", "<li>we wait for the coil</li>", "<td>300 shares</td>", "<p>今天 Revere 说</p>", "<p>我们等</p>"):
        assert not run_gates(html_text(base + inj))["ok"], inj


def test_jdump_keeps_every_line_short_and_round_trips():
    long_zh = "跌了四天，周五跳空高开，没被砸回去。" * 40
    obj = {"text": long_zh, "scores": list(range(400)), "pairs": [[i, i * 0.5] for i in range(5)],
           "nested": {"quote": 'He said "hold 715" ' * 30}}
    out = jdump(obj)
    assert max(len(ln) for ln in out.splitlines()) <= 300
    back = unjoin(json.loads(out))
    assert back == obj


def test_jdump_positive_control_plain_json_would_break_the_cap():
    obj = {"text": "x" * 1000}
    assert max(len(ln) for ln in json.dumps(obj).splitlines()) > 300  # the cap is not vacuous
    assert max(len(ln) for ln in jdump(obj).splitlines()) <= 300


def test_jdump_escapes_script_close():
    assert "</script>" not in jdump({"a": "</script><b>x</b>"})


@pytest.mark.parametrize("name", sorted(FIGS))
@pytest.mark.parametrize("lang", ["EN", "ZH"])
def test_every_schematic_spec_builds_with_its_checks(name, lang):
    spec = FIGS[name](lang)  # the §5 checks are asserts inside the builder
    kinds = {it[0] for it in spec["items"]}
    assert "path" in kinds and ({"text", "callout"} & kinds)
    assert all(len(it[2]) % 2 == 0 for it in spec["items"] if it[0] == "path")
    assert run_gates("\n".join(strings(spec)))["ok"]


BBOX = """<doc><page width="595.276000" height="841.890000">
<word xMin="40.000000" yMin="100.0" xMax="120.000000" yMax="110.0">SPX</word>
<word xMin="500.000000" yMin="100.0" xMax="590.500000" yMax="110.0">多空线 / bu</word>
</page><page width="595.276000" height="841.890000">
<word xMin="45.000000" yMin="100.0" xMax="540.000000" yMax="110.0">inside</word>
</page></doc>"""


def test_margin_overflow_red_on_text_past_the_right_margin():
    bad = margin_overflow(BBOX, 14, 14)
    assert len(bad) == 1 and bad[0]["page"] == 1 and bad[0]["word"].startswith("多空线")


def test_margin_overflow_green_inside_the_type_area():
    inside = BBOX.replace('xMin="500.000000" yMin="100.0" xMax="590.500000"', 'xMin="500.000000" yMin="100.0" xMax="550.000000"')
    assert margin_overflow(inside, 14, 14) == []


# ---------------------------------------------------------------- last-page legal line (Andy 09-13)
def test_legal_line_exists_in_both_languages_and_passes_the_gates():
    from pipeline.content.recap.visual import CHROME_LABELS
    for lang in ("EN", "ZH"):
        ch = CHROME_LABELS[lang]
        assert ch["handle"] == "@Fluxus_Z" and ch["site"] == "fluxus-capital.com"
        g = run_gates(ch["legal"])
        assert g["ok"], (lang, g)          # no proprietary name, no first person, no money
    assert "advice" in CHROME_LABELS["EN"]["legal"] and "Measure your own water" in CHROME_LABELS["EN"]["legal"]
    zh = CHROME_LABELS["ZH"]["legal"]
    assert "量好自己的水" in zh and "我" not in zh
    assert not re.search(r"[A-Za-z]", zh)  # ZH carries no English duplicate


def test_the_drop_line_caption_names_the_week_on_weeklies_and_the_day_on_dailies():
    js = (pathlib.Path(__file__).resolve().parents[1] / "content/recap/visual_assets/recap_page.js").read_text()
    reg = js[js.index("function regLine"):js.index("function condChart")]
    code = "\n".join(ln for ln in reg.splitlines() if not ln.strip().startswith(("/*", "*", "//")))
    # Andy 09-14: daily "1M DROP #09-11"; weekly "1M DROP Week37 2026-09-08 → 2026-09-11" (the week, not the data window)
    assert "Week" in code and "esc(is.W0)" in code and "esc(is.D0)" not in code
    assert "String(is.D || \"\").slice(5)" in code  # daily keeps the dash: #09-11
    assert "∫" not in code and "SPX" not in code  # Andy 09-14「删除啊！」: no SPX · ∫ tail
    from pipeline.content.recap import visual
    assert visual.DROP_SESSIONS == 5
    assert 'V.droparia, 6, 4.5, !is.weekly)' in js  # grey tail on dailies, all accent on weeklies
    # Visual Vera 09-14: one segment per session (daily 6 closes; weekly prior close + the week), span 10, 160px cap
    assert visual.DROP_BARS == "60m" and visual.DROP_SMOOTH_MIN == 195  # Andy 09-14: 60-minute bars, half-day smoothing
    assert "dropLine(is.spx, is.spx_smooth, is.spx_cut)" in js and "function smoothCloses" in js
    assert "var step = 10 / (closes.length - 1)" in js
    css = (pathlib.Path(visual.__file__).with_name("visual_assets") / "recap_visual.css").read_text()
    assert ".drop.thin{margin:18px auto 0;width:84%;height:auto;max-height:160px}" in css
    book = js[js.index("function book(is, c, V)"):]
    # the legal line rides the book section (window widened 2000->3600 when the
    # R ladder added the stop column and the trims/exits list, 2026-09-23)
    assert 'class="legal"' in book[:3600]


def test_l3_goes_red_when_the_state_row_breaks_across_pages():
    # pdftotext -layout excerpts from the real 09-14 renders
    split_0911_en = "MIXED\n                               FLUXUS CAPITAL · CONFIDENTIAL · 1 / 5\n\f                         0 / 12 votes\n−0.41\n"
    whole_0911_zh = "\n\nMIXED 0                 / 12    票\n"
    whole_0910_en = "BEARISH −7                            / 12 votes\n"
    whole_top_of_page = "\fMIXED 0                   / 12 votes\n"
    red = check_state_row(split_0911_en)
    assert not red["ok"] and red["split"] == ["0 / 12 votes"]
    for txt in (whole_0911_zh, whole_0910_en, whole_top_of_page):
        assert check_state_row(txt)["ok"], txt
    assert not check_state_row("no state row here\n")["ok"]


def test_the_state_row_is_on_the_print_break_inside_avoid_list():
    css = (pathlib.Path(__file__).resolve().parents[1] / "content/recap/visual_assets/recap_local.css").read_text()
    block = css[css.index("  .prose,\n  p,"):]
    block = block[:block.index("break-inside: avoid;")]
    assert ".state-row," in block


def test_the_drop_window_starts_every_session_from_its_prior_close():
    from pipeline.content.recap.visual import drop_series, drop_window
    assert drop_window("2026-09-11") == ("2026-09-03", ["2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"])
    week = ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]
    assert drop_window("2026-09-11", "2026-W37") == ("2026-09-04", week)
    cache = {"anchor": "2026-09-04", "anchor_close": 100.0,
             "sessions": {"2026-09-08": [101.0, 102.0], "2026-09-09": [103.0], "2026-09-10": [104.0, 105.0], "2026-09-11": [106.0, 107.0]}}
    spx, cut = drop_series(cache, "2026-09-04", week)
    assert spx == [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0]
    assert spx[cut] == 105.0  # the accent segment starts at 09-10's last bar
    with pytest.raises(AssertionError):
        drop_series(cache, "2026-09-03", week)  # a cache for another window never renders
