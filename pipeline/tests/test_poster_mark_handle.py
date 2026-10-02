"""海报/数据卡署名角标必须是 @Fluxus_Z，不许回退到 FLUXUS（T-1002-85，Andy 2026-10-02 原话：
「署名对外一致用 twitter handle @Fluxus_Z 而不是Fluxus」）。只查模板字符串，不起 Chrome 渲染。"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_make_poster_mark_is_handle():
    m = _mod("make_poster")
    assert '<span class="mark">@Fluxus_Z</span>' in m.TEMPLATE
    assert ">FLUXUS<" not in m.TEMPLATE


def test_make_data_card_mark_is_handle():
    m = _mod("make_data_card")
    assert '<span class="mark">@Fluxus_Z</span>' in m.TEMPLATE
    assert ">FLUXUS<" not in m.TEMPLATE
