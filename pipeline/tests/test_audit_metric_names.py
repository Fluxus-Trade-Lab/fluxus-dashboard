"""Naming-collision regression tests (pipeline/tools/audit_metric_names.py).

Fixtures replay the 三次律-fourth-occurrence shape from 2026-09-06: a
self-invented field wearing a standard's own name. `wk_band_3` and `rs_ibd`
(now `rs_rating`) are the two that were actually renamed; `sp_phase` and
`vcs` are the two Andy named as the mechanism-triggering repeat
(「候选行批了，Power Trend 改判定对齐 Webster，撞名立机制」). None of these
four collide under the real, live METRIC_SOURCES.md today -- that IS the
fix. What this file proves is narrower and forward-looking: if the exact
collision shape from each precedent were reintroduced, the checker catches
it. That is what "guards against the next one" has to mean for a rename
that already happened.
"""
from __future__ import annotations

from pathlib import Path

from pipeline.tools import audit_metric_names as M

HEADER = "| 我们发的 | 标准名 | 标准口径 | 状态 |\n|---|---|---|---|\n"


def _fixture(*rows: str) -> str:
    body = "\n".join(rows)
    return f"# fixture\n\n## 登记表\n\n{HEADER}{body}\n\n## 已登记的债\n\n(not part of the table)\n"


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "METRIC_SOURCES.md"
    p.write_text(text, encoding="utf-8")
    return p


# --------------------------------------------------------------------------
# Structural failures: loud, never a silent green.
# --------------------------------------------------------------------------

def test_missing_file_is_a_violation_not_a_silent_pass():
    out = M.run(Path("/definitely/does/not/exist/METRIC_SOURCES.md"))
    assert not out["ok"]
    assert any("not found" in v for v in out["violations"]), out["violations"]


def test_missing_登记表_heading_is_a_violation(tmp_path):
    p = _write(tmp_path, "# no table here\njust prose, no heading at all\n")
    out = M.run(p)
    assert not out["ok"]
    assert any("登记表" in v for v in out["violations"]), out["violations"]


def test_table_with_no_rows_is_a_violation(tmp_path):
    p = _write(tmp_path, "# fixture\n\n## 登记表\n\nno pipe rows follow this heading.\n")
    out = M.run(p)
    assert not out["ok"]
    assert any("no '|' table rows" in v for v in out["violations"]), out["violations"]


def test_wrong_header_shape_is_a_violation(tmp_path):
    p = _write(tmp_path, "# fixture\n\n## 登记表\n\n| a | b |\n|---|---|\n| x | y |\n")
    out = M.run(p)
    assert not out["ok"]
    assert any("table header" in v for v in out["violations"]), out["violations"]


def test_malformed_row_cell_count_is_a_violation(tmp_path):
    p = _write(tmp_path, _fixture("| `only_two` | 标准名 |"))
    out = M.run(p)
    assert not out["ok"]
    assert any("expected 4" in v for v in out["violations"]), out["violations"]


# --------------------------------------------------------------------------
# Clean content: real rows from the live registry must not false-positive.
# --------------------------------------------------------------------------

def test_clean_table_has_zero_violations(tmp_path):
    """Real shapes from data/reference/METRIC_SOURCES.md: an ordinary ✅ row,
    the two already-fixed historical precedents (标准名 uses plain
    `*(...)*` italics, not `**bold**`, so no canonical token exists to
    collide with), and a distinct, deliberately-chosen new name (`vcs`,
    `power_trend`) whose 标准名 IS bolded but whose field name does not
    reproduce it."""
    rows = _fixture(
        "| `mcclellan_osc` | McClellan Oscillator | RANA = net/(adv+dec)×1000 | ✅ **一致** |",
        "| `wk_band_3` | *(无标准)* | — | ⚠️ **自造**：三根周收盘的全域带宽 ≤1.5%。原名 `wk_tight_3`，冒充了 IBD 的形态名 |",
        "| `rs_rating` | *(IBD 专有；社区复刻)* | 加权超额排 1-99 | ⚠️ **社区重建不是 IBD 一手**。原名 `rs_ibd` 冒充了 IBD |",
        "| `vcs` | oratnek **Volatility Contraction Score v2**（**不是 VCP**） | 三个比值加权 | ✅ 一致。它测的是压缩程度，不是收缩次数——与 VCP 同源不同物 |",
        "| `power_trend`（`signals.json` 五项） | **Mike Webster / IBD Market School — Power Trend** | 四条同时成立才开启 | ⚠️ **五项检查与标准口径无一条对上**（逐条对照见下） |",
    )
    p = _write(tmp_path, rows)
    out = M.run(p)
    assert out["ok"], out["violations"]
    assert out["checked_rows"] == 0


def test_placeholder_unpublished_rows_are_skipped(tmp_path):
    """—（拟 `field`） rows with no live field yet still parse (the backtick
    proposal is checked too, harmlessly) and a bare `—` with nothing
    published at all must never crash the parser."""
    rows = _fixture(
        "| —（拟 `vcp_contractions`） | Minervini **Volatility Contraction Pattern (VCP)** | 2-6 次收缩 | ⚠️ **有可引定义，但只有作者本人的散文式描述** |",
        "| — | McClellan Summation Index | 累加 | 🔲 我们没有 |",
    )
    p = _write(tmp_path, rows)
    out = M.run(p)
    # vcp_contractions != vcp -- deliberately distinct, no collision
    assert out["ok"], out["violations"]


# --------------------------------------------------------------------------
# Positive control (task requirement): a fake self-invented row named
# identically to a standard token must fail.
# --------------------------------------------------------------------------

def test_positive_control_exact_acronym_collision_is_caught(tmp_path):
    """Inject a fake self-invented row using the standard's own acronym as
    the field name -- the checker must trip on it."""
    rows = _fixture(
        '| `vcp` | Minervini **Volatility Contraction Pattern (VCP)** | 2-6 次收缩 | ⚠️ **自造**：占用了 VCP 这个名字 |',
    )
    p = _write(tmp_path, rows)
    out = M.run(p)
    assert not out["ok"]
    assert out["checked_rows"] == 1
    assert any("vcp" in v.lower() for v in out["violations"]), out["violations"]


def test_a_consistent_row_using_the_standard_name_is_fine(tmp_path):
    """The rule is not "never match the standard's name" -- it's "don't
    match it while admitting 自造/冒充". A ✅ 一致 row is exempt."""
    rows = _fixture(
        '| `vcp` | Minervini **Volatility Contraction Pattern (VCP)** | 2-6 次收缩 | ✅ 一致 |',
    )
    p = _write(tmp_path, rows)
    out = M.run(p)
    assert out["ok"], out["violations"]


# --------------------------------------------------------------------------
# The four precedents, replayed as the exact-collision shape they warn
# against (task requirement: known historical cases as a fixture
# regression). None of these strings exist in the live file -- each
# independently proves the mechanism would have caught it.
# --------------------------------------------------------------------------

def test_wk_band_3_precedent_replayed_as_a_collision_is_caught(tmp_path):
    p = _write(tmp_path, _fixture(
        '| `3_tight_closes` | IBD **3 Tight Closes** | 三周收盘互差 ≤1.5% | ⚠️ **自造**：带宽阈值是我们定的，名字用了 IBD 的 |'))
    out = M.run(p)
    assert not out["ok"], "wk_tight_3-shaped collision must be caught"


def test_rs_ibd_precedent_replayed_as_a_collision_is_caught(tmp_path):
    p = _write(tmp_path, _fixture(
        '| `rs_rating` | IBD **RS Rating** | 官方六因子专有算法 | ⚠️ **冒充**：我们是社区复刻权重，不是 IBD 官方系数 |'))
    out = M.run(p)
    assert not out["ok"], "rs_ibd-shaped collision must be caught"


def test_sp_phase_precedent_replayed_as_a_collision_is_caught(tmp_path):
    p = _write(tmp_path, _fixture(
        '| `four_stages` | Weinstein **Four Stages** | 30 周均线斜率 + 价格位置判定四阶段 | ⚠️ **自造**：我们的字段挂的是 oratnek Structure Pivot 内部状态，不是 Weinstein 的判据 |'))
    out = M.run(p)
    assert not out["ok"], "sp_phase-shaped collision (borrowing Weinstein's stage name) must be caught"


def test_vcs_precedent_replayed_as_a_collision_is_caught(tmp_path):
    p = _write(tmp_path, _fixture(
        '| `vcp` | Minervini **Volatility Contraction Pattern (VCP)** | 2-6 次逐次变浅的回撤 | ⚠️ **自造**：我们测的是压缩程度不是收缩次数，字段名却用了 VCP |'))
    out = M.run(p)
    assert not out["ok"], "vcs-shaped collision (borrowing Minervini's VCP name) must be caught"


# --------------------------------------------------------------------------
# Ratchet: an allowlisted collision warns, does not fail.
# --------------------------------------------------------------------------

def test_allowlisted_row_is_a_warning_not_a_violation(tmp_path, monkeypatch):
    # keyed on the raw 我们发的 cell text, exactly as written in the table
    monkeypatch.setattr(M, "ALLOWLIST", {"`vcp`"})
    p = _write(tmp_path, _fixture(
        '| `vcp` | Minervini **Volatility Contraction Pattern (VCP)** | 2-6 次收缩 | ⚠️ **自造**：历史遗留，待改名 |'))
    out = M.run(p)
    assert out["ok"], out["violations"]
    assert any("grandfathered" in w for w in out["warnings"]), out["warnings"]


# --------------------------------------------------------------------------
# The real file: the actual merged registry must pass clean today (zero
# seeded allowlist entries needed).
# --------------------------------------------------------------------------

def test_the_real_metric_sources_file_passes_clean():
    out = M.run(M.METRIC_SOURCES)
    assert out["ok"], out["violations"]
