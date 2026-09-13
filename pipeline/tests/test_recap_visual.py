"""Visual layout helpers: page-text extraction feeds the gates, and every schematic passes its own checks."""
import pytest

from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.visual import html_text
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


@pytest.mark.parametrize("name", sorted(FIGS))
@pytest.mark.parametrize("lang", ["EN", "ZH"])
def test_every_schematic_builds_with_its_checks(name, lang):
    svg = FIGS[name](lang)  # the §5 checks are asserts inside the builder
    assert svg.startswith('<svg class="tell"') and svg.count("<path") >= 1 and "<text" in svg
    assert run_gates(html_text(svg))["ok"]
