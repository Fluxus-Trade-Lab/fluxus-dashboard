"""蹭位榜「前 8 名里挂得上的前 5」空帖闸。

取件账 09-18·3，三次律到期（09-22 四格 · 09-23 速报一格 · 09-23 主班两格）。
自造口径见 `thin_caption.py` 模块 docstring：去掉链接后的正文有没有数字。

⭐ 阳性对照按「能坏的方式」分类造，两个方向各一条：
  1. 漏改（is_thin_caption 永远返回 False，或 top5_from_pool 不剔任何东西）
     → test_gate_must_actually_drop_a_thin_caption 红
  2. 改了但接错（把带具体点位的真信号也当空帖剔掉）
     → test_a_real_signal_with_a_number_survives 红（Linda 债券位原句）
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/thin_caption.py"
_spec = importlib.util.spec_from_file_location("x_watch_thin_caption", _SRC)
tcap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tcap)


def _row(handle, text, density):
    return {"h": handle, "text": text, "density": density}


def test_gate_must_actually_drop_a_thin_caption():
    """漏改的阳性对照：纯图配标题、正文没有数字的帖必须被判空帖并被剔出前 5。"""
    assert tcap.is_thin_caption("MCD chart update https://t.co/abc") is True

    rows = [
        _row("adloop", "Subscribers get the next chart first https://t.co/1", 20000),
        _row("real_one", "Bonds: 106'27 key swing low. https://t.co/2", 9121),
        _row("thin1", "MCD chart update https://t.co/3", 8000),
        _row("thin2", "SPY setup https://t.co/4", 7500),
        _row("thin3", "QQQ watching https://t.co/5", 7000),
        _row("thin4", "NVDA levels https://t.co/6", 6500),
        _row("thin5", "AMD chart https://t.co/7", 6000),
        _row("thin6", "TSLA update https://t.co/8", 5500),
    ]
    kept = tcap.top5_from_pool(rows)
    kept_handles = [r["h"] for r in kept]
    # 8 个候选里只有 real_one 带数字，其余 7 个（含广告帖 adloop）全是空帖——
    # 漏改的话 kept 会有 5 个，且 thin1..thin4 这类空帖会混进来。
    assert "thin1" not in kept_handles
    assert "thin2" not in kept_handles
    assert kept_handles == ["real_one"]


def test_a_real_signal_with_a_number_survives():
    """剔过头的阳性对照：Linda 的债券位（真实原句，具体点位 106'27）不许被当空帖剔掉。"""
    bonds_text = "Bonds: 106'27 key swing low. https://t.co/8JGrHmDBwz"
    assert tcap.is_thin_caption(bonds_text) is False

    rows = [
        _row("a", "Some ad with no numbers at all https://t.co/1", 20000),
        _row("LindaRaschke", bonds_text, 9121),
        _row("b", "Another wordy caption but zero digits here https://t.co/2", 8000),
        _row("c", "Chart chart chart no data point https://t.co/3", 7500),
        _row("d", "Just watching this setup closely https://t.co/4", 7000),
        _row("e", "No numbers in this one either https://t.co/5", 6500),
        _row("f", "Still nothing numeric to report https://t.co/6", 6000),
        _row("g", "Caption without a single digit https://t.co/7", 5500),
    ]
    kept = tcap.top5_from_pool(rows)
    assert "LindaRaschke" in [r["h"] for r in kept]


def test_short_real_signal_is_not_flagged_by_length_alone():
    """判据是「有没有数字」，不是长度——短但带点位的一句话不该被按长度误伤。"""
    assert tcap.is_thin_caption("MCD 150.20") is False


def test_not_enough_survivors_does_not_pad_from_rank_nine():
    """前 8 名挂得上的不够 5 个时，照实只出剩下的几个，不去补第 9 名。"""
    rows = [
        _row("real1", "SPY broke 650.10 on volume https://t.co/1", 9000),
        _row("thin1", "SPY chart https://t.co/2", 8000),
        _row("thin2", "QQQ watching https://t.co/3", 7000),
        _row("thin3", "NVDA levels https://t.co/4", 6000),
        _row("thin4", "AMD chart https://t.co/5", 5000),
        _row("thin5", "TSLA update https://t.co/6", 4000),
        _row("thin6", "MSFT setup https://t.co/7", 3000),
        _row("thin7", "META watching https://t.co/8", 2000),
        _row("real2_rank9", "IWM broke 210.50 support https://t.co/9", 1000),
    ]
    kept = tcap.top5_from_pool(rows)
    kept_handles = [r["h"] for r in kept]
    assert kept_handles == ["real1"]
    assert "real2_rank9" not in kept_handles
