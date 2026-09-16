import datetime as dt

from pipeline.tools.doorbells import open_bells, parse

INBOX = """\
🔔 [09-12] → OPS Fable · 联邦运维: done, signed · pending
  ↳ ✅ OPS 已取（09-12）：merged
🔔 [09-13] → Marketing Steve · 编辑部/运营: done, unsigned receipt · pending
  ↳ 已取（09-13 · Marketing Steve 交互会话）· 未执行
  ↳ ✅ 已执行（09-13 · `54b98d1f`）
🔔 [09-13] → OPS Fable: still open · pending
🔔 [09-16] → OPS Fable · 联邦运维: open, another line's note underneath · pending
  ↳ ✅ Plumber Joe（09-16）早报数字抽查补做
🔔 [09-12] → Plumber Joe · 数据晨检: joe's own · pending
  ↳ 👀 已读（09-13 · X 日调研主班）
🔔 [09-11] → OPS Fable · 联邦运维: closed by its sender · done
"""
NOW = dt.datetime(2026, 9, 16, 12, 0)


def test_the_real_09_16_shapes():
    state = {b.lineno: b.open for b in parse(INBOX, 2026)}
    assert state == {1: False, 3: False, 6: True, 7: True, 9: True}


def test_filter_by_line_and_age():
    ops = open_bells(INBOX, "OPS", NOW)
    assert [b.lineno for b in ops] == [6, 7]
    assert [b.lineno for b in open_bells(INBOX, "OPS", NOW, older_than_hours=48)] == [6]
    assert [b.lineno for b in open_bells(INBOX, "Joe", NOW)] == [9]


def test_the_bare_grep_overcounts():
    grep = [ln for ln in INBOX.splitlines() if ln.startswith("🔔") and "OPS" in ln and "pending" in ln]
    assert len(grep) == 3 and len(open_bells(INBOX, "OPS", NOW)) == 2
