import datetime as dt
import json

import pipeline.tools.inbox_archive as ia

from pipeline.tools.doorbells import parse
from pipeline.tools.inbox_archive import archive, section_month

INBOX = """\
# 夜间组收件箱（append-only）

> 📦 **2026-08 的记录已归档**（旧格式指针，应被工具接管）

## 🔗 收藏夹
- 一条链接 08-30

## 📌 给 Andy 的待办（08-25 起）
- **[08-25 · status 待办]** 旧事

## 已裁决（读过打 ✅）
- 08-24 已读

## [2026-08-28] 老节，已了结
正文 A
🔔 [08-28] → OPS Fable: done · pending
  ↳ ✅ OPS 已取（08-28）

## [2026-09-02 夜班] 九月节，门铃还开着
🔔 [09-02] → DATA ALEX: still open · pending

## [2026-09-03] 九月节，已了结
### 子节
正文 B

## 没有日期的节
正文 C

## [2026-10-01] 十月节
正文 D

## [2026-08-30] 八月节，排在后面
正文 E
"""
CUT = dt.date(2026, 10, 1)


def _run(text, existing=None):
    return archive(text, CUT, dict(existing or {}))


def test_moves_only_dated_sections_before_the_cutoff():
    kept, files, report = _run(INBOX)
    assert "## [2026-08-28] 老节，已了结" in files["2026-08"]
    assert "## [2026-08-30] 八月节，排在后面" in files["2026-08"]   # 乱序也搬
    assert "## [2026-09-03] 九月节，已了结" in files["2026-09"]
    assert "### 子节" in files["2026-09"]                          # 子节跟着父节走
    for stays in ("## [2026-10-01] 十月节", "## 没有日期的节", "## 🔗 收藏夹",
                  "## 📌 给 Andy 的待办（08-25 起）", "## 已裁决（读过打 ✅）"):
        assert stays in kept


def test_a_section_with_an_open_doorbell_stays():
    kept, files, report = _run(INBOX)
    assert "## [2026-09-02 夜班] 九月节，门铃还开着" in kept
    assert "门铃还开着" not in files["2026-09"]
    assert report["kept_open"] == ["## [2026-09-02 夜班] 九月节，门铃还开着"]
    before = {(b.date, b.to) for b in parse(INBOX, 2026) if b.open}
    after = {(b.date, b.to) for b in parse(kept, 2026) if b.open}
    assert before == after


def test_nothing_is_lost_or_reordered():
    kept, files, report = _run(INBOX)
    one = lambda s: s[:-1] if s.endswith("\n") else s          # 去掉恰好一个结尾换行
    body = lambda s: [ln for ln in one(s).split("\n") if not ln.startswith("> 📦")]
    orig = body(INBOX)
    moved = [ln for m in sorted(files) for ln in one(files[m]).split("\n")[report["header_lines"]:]]
    rest = body(kept)
    assert sorted(orig) == sorted(rest + moved)
    # 保留下来的行保持原顺序
    it = iter(orig)
    assert all(any(ln == o for o in it) for ln in rest)


def test_pointer_lists_every_archive_month_once():
    kept, files, report = _run(INBOX)
    ptr = [ln for ln in kept.split("\n") if ln.startswith("> 📦")]
    assert len(ptr) == 1
    assert "INBOX_archive_2026-08.md" in ptr[0] and "INBOX_archive_2026-09.md" in ptr[0]
    assert "旧格式指针" not in kept


def test_second_run_changes_nothing():
    kept, files, _ = _run(INBOX)
    kept2, files2, report2 = archive(kept, CUT, dict(files))
    assert kept2 == kept and files2 == files and report2["moved_sections"] == 0


def test_appends_to_an_existing_archive_file():
    existing = {"2026-08": "# 夜间组收件箱 · 2026-08 归档（只读）\n\n旧内容\n## [2026-08-01] 早就在这里\n"}
    kept, files, _ = _run(INBOX, existing)
    assert files["2026-08"].startswith(existing["2026-08"])
    assert "## [2026-08-28] 老节，已了结" in files["2026-08"]


def test_section_month_reads_the_first_date_in_the_heading():
    assert section_month("## [2026-09-11 23:1x UTC / 19:1x ET] 数据哨兵", 2026) == "2026-09"
    assert section_month("## 📬 OPS 裁决（08-24，回应…）", 2026) == "2026-08"
    assert section_month("## [2026-09-06 夜班] Zac：08-07 那天的归档", 2026) == "2026-09"
    assert section_month("## 没有日期的节", 2026) is None


def _repo(tmp_path, text):
    box = tmp_path / "data/research/night_reports"
    box.mkdir(parents=True)
    (box / "INBOX.md").write_text(text, encoding="utf-8")
    return box


def test_cli_moves_and_writes(tmp_path, capsys):
    box = _repo(tmp_path, INBOX)
    assert ia.main(["--repo", str(tmp_path), "--before", "2026-10-01"]) == 0
    assert json.loads(capsys.readouterr().out)["moved_sections"] == 3
    assert (box / "INBOX_archive_2026-08.md").exists() and (box / "INBOX_archive_2026-09.md").exists()
    assert "老节，已了结" not in (box / "INBOX.md").read_text(encoding="utf-8")


def test_cli_refuses_when_a_line_would_be_lost(tmp_path, monkeypatch):
    box = _repo(tmp_path, INBOX)
    real = ia.archive

    def lossy(text, cutoff, existing):
        kept, files, report = real(text, cutoff, existing)
        files = {m: c.replace("正文 A\n", "") for m, c in files.items()}
        return kept, files, report

    monkeypatch.setattr(ia, "archive", lossy)
    assert ia.main(["--repo", str(tmp_path), "--before", "2026-10-01"]) == 1
    assert (box / "INBOX.md").read_text(encoding="utf-8") == INBOX
    assert not list(box.glob("INBOX_archive_*.md"))


def test_cli_refuses_when_an_open_doorbell_would_move(tmp_path, monkeypatch):
    box = _repo(tmp_path, INBOX)
    real_archive, real_parse = ia.archive, ia.parse

    def blind(text, cutoff, existing):                            # 只在搬运时看不见门铃
        monkeypatch.setattr(ia, "parse", lambda text, year: [])
        try:
            return real_archive(text, cutoff, existing)
        finally:
            monkeypatch.setattr(ia, "parse", real_parse)

    monkeypatch.setattr(ia, "archive", blind)
    assert ia.main(["--repo", str(tmp_path), "--before", "2026-10-01"]) == 1
    assert (box / "INBOX.md").read_text(encoding="utf-8") == INBOX


def test_several_old_pointers_collapse_to_one():
    text = INBOX.replace("> 📦 **2026-08 的记录已归档**（旧格式指针，应被工具接管）\n",
                         "> 📦 旧指针一\n> 📦 旧指针二\n")
    kept, _, _ = _run(text)
    assert [ln for ln in kept.split("\n") if ln.startswith("> 📦")] == \
        [ln for ln in _run(INBOX)[0].split("\n") if ln.startswith("> 📦")]


def test_a_yearless_december_heading_read_in_january_is_last_year():
    text = "# t\n\n## 已裁决\n\n## 📬 裁决（12-30，旧事）\n正文\n\n## 📬 新事（01-02）\n正文\n"
    kept, files, _ = archive(text, dt.date(2027, 1, 1), {})
    assert list(files) == ["2026-12"]
    assert "新事（01-02）" in kept
