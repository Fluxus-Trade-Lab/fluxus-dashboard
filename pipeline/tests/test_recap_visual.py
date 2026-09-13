"""Visual review page: short-line JSON, page-text gates, schematic specs, and the type-area check."""
import json

import pytest

from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import margin_overflow
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
