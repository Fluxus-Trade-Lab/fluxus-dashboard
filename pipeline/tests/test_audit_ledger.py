"""Run-ledger invariants (pipeline/tools/audit_ledger.py).

The fixtures are the real shapes out of data/history/run_ledger.jsonl: the
08-19 blackout line (breadth ok / regime_score null / no enriched blocks) and
the healthy re-run of that same session four hours later.
"""
from __future__ import annotations

import datetime as dt
import json

from pipeline.tools import audit_ledger as L

LAST = dt.date(2026, 8, 21)


def _guards(**over):
    g = {
        "fundamentals":     {"status": "ok", "due": 400, "ok": 400, "failed": 0, "walled": False, "store": 5630},
        "breadth":          {"status": "ok", "reason": None, "regime_score": 71.9,
                             "enriched": ["conditions", "regime", "state_board", "verdict"]},
        "ticker_events":    {"status": "ok", "reason": None, "rows_today": 2303, "event_date": "2026-08-21"},
        "asset_signals":    {"status": "ok", "count": 26},
        "universe_quality": {"status": "ok", "rows": 5627, "degraded": ["perf_ytd"]},
        "watchlist":        {"status": "ok", "gated": 2053, "panels": {"true_market_leaders": 58}},
        "shortlist":        {"status": "ok", "cards": 6},
        "site_quality":     {"status": "ok", "sources": {"etf_data": "ok", "signals": "ok"}},
        "screeners":        {"status": "ok", "counts": {"momentum_97": 169}},
    }
    g.update(over)
    return g


def _row(session, **over):
    r = {"session": session, "started_utc": f"{session}T21:52:55+00:00",
         "finished_utc": f"{session}T22:10:42+00:00", "code_sha": "c637fe1",
         "trigger": "schedule", "run_id": "1", "guards": _guards(), "wrote": [], "errors": []}
    r.update(over)
    return r


def _write(tmp_path, rows):
    p = tmp_path / "run_ledger.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def test_healthy_run_passes(tmp_path):
    out = L.run(_write(tmp_path, [_row("2026-08-20"), _row("2026-08-21")]), window=0, last_done=LAST)
    assert out["ok"] and out["violations"] == 0, out["runs"]


def test_the_0819_blackout_line_is_an_L3_violation(tmp_path):
    """status ok + null evidence: the shape nothing read on the night."""
    blackout = _row("2026-08-21", guards=_guards(
        breadth={"status": "ok", "reason": None, "regime_score": None}))
    out = L.run(_write(tmp_path, [blackout]), window=0, last_done=LAST)
    assert not out["ok"]
    v = out["runs"][0]["violations"]
    assert any(x.startswith("L3 breadth") and "regime_score" in x for x in v), v
    assert any(x.startswith("L3 breadth") and "enriched" in x for x in v), v


def test_partial_enriched_blocks_still_fail(tmp_path):
    """three of the four blocks is not four -- ok has to mean all of them."""
    row = _row("2026-08-21", guards=_guards(
        breadth={"status": "ok", "regime_score": 71.9, "enriched": ["conditions", "regime", "verdict"]}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any("enriched" in x for x in out["runs"][0]["violations"])


def test_missing_session_is_L1(tmp_path):
    """no line for the last completed session = the run never happened."""
    out = L.run(_write(tmp_path, [_row("2026-08-20")]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any(t.startswith("L1") and "2026-08-21" in t for t in out["top"]), out["top"]


def test_empty_ledger_is_L1(tmp_path):
    p = tmp_path / "run_ledger.jsonl"
    p.write_text("", encoding="utf-8")
    out = L.run(p, window=0, last_done=LAST)
    assert not out["ok"] and any(t.startswith("L1") for t in out["top"])


def test_non_ok_status_and_errors(tmp_path):
    row = _row("2026-08-21",
               guards=_guards(breadth={"status": "fail", "reason": "stale store"},
                              universe_quality={"status": "degraded", "rows": 5627}),
               errors=[{"where": "screeners", "msg": "yfinance 429"}])
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    rep = out["runs"][0]
    assert any(x.startswith("L2 breadth status='fail'") for x in rep["violations"]), rep["violations"]
    assert any(x.startswith("L4 error in screeners") for x in rep["violations"]), rep["violations"]
    assert any(x.startswith("L2 universe_quality degraded") for x in rep["warnings"]), rep["warnings"]
    # a failed guard is not asked for evidence -- L2 already said it
    assert not any(x.startswith("L3 breadth") for x in rep["violations"])


def test_guard_dropout_is_a_warning(tmp_path):
    g = _guards()
    g.pop("shortlist")
    out = L.run(_write(tmp_path, [_row("2026-08-20"), _row("2026-08-21", guards=g)]),
                window=0, last_done=LAST)
    assert out["ok"]                       # a dropout is a warning, not a violation
    assert any("L5" in x and "shortlist" in x for x in out["runs"][-1]["warnings"])


def test_same_session_rerun_is_reported_not_fatal(tmp_path):
    out = L.run(_write(tmp_path, [_row("2026-08-21"), _row("2026-08-21", code_sha="894fccc")]),
                window=0, last_done=LAST)
    assert out["ok"]
    assert any(t.startswith("L6") and "2 lines" in t for t in out["top"])


def test_a_rate_limit_wall_warns_and_does_not_block_the_night(tmp_path):
    """2026-08-27, live: `fundamentals status='walled'` exited 1, `Commit and
    push` was skipped, and the dashboard sat on a four-day-old session because
    an OPTIONAL enrichment hit a rate limit. `walled` is the fundamentals
    guard's own word for partial coverage; `partial` was already a warning.
    Only the vocabulary disagreed."""
    row = _row("2026-08-27", guards=_guards(
        fundamentals={"status": "walled", "due": 400, "ok": 138, "failed": 0,
                      "walled": True, "store": 5634}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done="2026-08-27")
    assert out["ok"], out["runs"][0]["violations"]     # the night still ships
    assert any("L2 fundamentals walled" in x for x in out["runs"][0]["warnings"])
    # and it is not silent: a warning still prints and still lands in the JSON
    assert not out["runs"][0]["violations"]


def test_an_unknown_status_word_is_still_fatal(tmp_path):
    """The list is a list, not a shrug. A word nobody has classified must stop
    the publish -- that is what caught the 08-27 gap in the first place."""
    row = _row("2026-08-21", guards=_guards(
        fundamentals={"status": "wedged", "due": 400, "ok": 400, "failed": 0, "store": 5630}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any("L2 fundamentals status='wedged'" in x for x in out["runs"][0]["violations"])


def test_fundamentals_failure_rate_warns(tmp_path):
    row = _row("2026-08-21", guards=_guards(
        fundamentals={"status": "ok", "due": 400, "ok": 277, "failed": 123, "store": 5630}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert out["ok"]                                   # a warning, not a gate
    assert out["runs"][0]["fund_fail_rate"] == 0.307                # 123/400 = 0.3075, banker's rounding
    assert any("L6 fundamentals failed 123/400" in x for x in out["runs"][0]["warnings"])


def test_window_limits_what_is_audited(tmp_path):
    bad = _row("2026-08-19", guards=_guards(breadth={"status": "ok", "regime_score": None}))
    p = _write(tmp_path, [bad, _row("2026-08-20"), _row("2026-08-21")])
    assert L.run(p, window=0, last_done=LAST)["violations"] == 2      # sees the old bad line
    assert L.run(p, window=1, last_done=LAST)["ok"]                   # newest session only


class TestSupersededAttempts:
    """A recorded failure is history, not a current defect.

    2026-08-29 the workflow started committing the ledger line of runs a gate
    had stopped (`if: failure()`) -- the change that finally made failed
    nights visible. It immediately made THIS auditor fail every session that
    contained a caught-and-recovered failure, blocking the very publish the
    recovery had earned. The gate worked, a later attempt succeeded, and the
    data on main is the good one; judging the session by its worst attempt
    turns a working plan B into an outage.
    """

    def _ledger(self, tmp_path, rows):
        import json
        p = tmp_path / "led.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return p

    def _run(self, session, *, ok, sha="abc1234"):
        """A ledger line that either passes or trips an L2 guard."""
        return {"session": session, "code_sha": sha, "trigger": "schedule",
                "universe_rows": 5600,
                "guards": {"universe_quality": {"status": "ok" if ok else "severe",
                                                "rows": 5600},
                           "breadth": {"status": "ok", "regime_score": 50,
                                       "enriched": ["regime", "state_board",
                                                    "verdict", "conditions"]}}}

    def test_a_failed_attempt_followed_by_a_good_one_is_not_a_violation(self, tmp_path):
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["violations"] == 0, rep
        assert rep["ok"] is True

    def test_the_failure_is_still_reported_as_a_warning(self, tmp_path):
        """Demoted, never swallowed -- the record is the whole point."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["warnings"] >= 1
        text = " ".join(w for r in rep["runs"] for w in r["warnings"])
        assert "superseded attempt" in text
        assert any(r.get("superseded") for r in rep["runs"])

    def test_the_LAST_attempt_failing_is_still_a_violation(self, tmp_path):
        """The positive control: if the newest attempt of the session is the
        broken one, nothing was recovered and the gate must still bite."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=True), self._run(s, ok=False)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["violations"] >= 1, "a session whose last run failed must fail"
        assert rep["ok"] is False

    def test_every_run_report_keeps_its_violations_key(self, tmp_path):
        """Demotion emptied the list; an earlier version popped the key and
        crashed the printer (KeyError: 'violations')."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert all("violations" in r for r in rep["runs"])


# ============================================================================
# 2026-09-03（Nighty Zac）· 存活清单驱动的补测
#
# 普查读数 42/80 = 52%。按 `data/research/sop/read_a_survivor_list.md` 第 2 步
# 先看簇：38 个存活里 **10 个挤在 `_holds` 一个函数里**（L116–L124 的每一个
# 比较符和布尔连接词全部裸着）——第一种簇「一整个函数的判据没被测过」。
#
# 为什么它是最贵的那一簇：`_holds` 就是 L3。EVIDENCE 表的注释亲手区分了
# `num+`（"> 0"）和 `num0+`（">= 0"，注释原话「0 is a real answer, None is not」），
# 而 `Gt -> GtE` / `GtE -> Gt` 两个变异体**双双存活** —— 这条被写进注释的语义差别，
# 此前没有任何测试钉着。一个把 rows_today=0 读成 ok 的 L3，正是 08-19 那晚的形状。
#
# 下面每条都在真代码上绿、在对应变异体上红（逐条实测，见 09-03 晨报）。
# ============================================================================

class TestHoldsPredicateBoundaries:
    """`_holds` 的每个谓词，钉在它自己的边界上。"""

    def test_num_plus_rejects_zero_but_num0_plus_accepts_it(self):
        """`num+` 与 `num0+` 的全部区别就是 0 —— 这是 EVIDENCE 表注释声明的语义。"""
        assert L._holds({"v": 1}, "v", "num+") is True
        assert L._holds({"v": 0}, "v", "num+") is False      # Gt -> GtE 会翻这条
        assert L._holds({"v": 0}, "v", "num0+") is True      # GtE -> Gt 会翻这条
        assert L._holds({"v": -1}, "v", "num0+") is False

    def test_none_is_never_a_number(self):
        """08-19 的形状：字段在、值是 null。两个数值谓词都必须拒。"""
        for pred in ("num+", "num0+"):
            assert L._holds({"v": None}, "v", pred) is False
            assert L._holds({}, "v", pred) is False

    def test_bool_is_not_a_number(self):
        """True 会通过 `> 0`，所以 isinstance-bool 那半个 and 必须在。

        L116/L118 的 `and not isinstance(v, bool)` 是 And -> Or 变异体的家。
        """
        for pred in ("num+", "num0+"):
            assert L._holds({"v": True}, "v", pred) is False
            assert L._holds({"v": False}, "v", pred) is False

    def test_a_string_that_looks_like_a_number_is_still_not_one(self):
        assert L._holds({"v": "5"}, "v", "num+") is False

    def test_list4_needs_all_four_blocks_not_just_some(self):
        four = ["conditions", "regime", "state_board", "verdict"]
        assert L._holds({"v": four}, "v", "list4") is True
        assert L._holds({"v": four + ["extra"]}, "v", "list4") is True
        for drop in range(4):
            partial = [b for i, b in enumerate(four) if i != drop]
            assert L._holds({"v": partial}, "v", "list4") is False, partial
        assert L._holds({"v": []}, "v", "list4") is False
        assert L._holds({"v": None}, "v", "list4") is False

    def test_dict_plus_rejects_the_empty_mapping(self):
        """空 dict 是「这一格什么都没有」，不是「检查过了」。L122 的 And -> Or 之家。"""
        assert L._holds({"v": {"a": 1}}, "v", "dict+") is True
        assert L._holds({"v": {}}, "v", "dict+") is False
        assert L._holds({"v": []}, "v", "dict+") is False

    def test_allok_rejects_empty_and_any_non_ok_value(self):
        """L124 有三个存活（And->Or / Gt->GtE / 0->1），全部在这条上。"""
        assert L._holds({"v": {"a": "ok", "b": True}}, "v", "allok") is True
        assert L._holds({"v": {}}, "v", "allok") is False           # 空 = 没检查过
        assert L._holds({"v": {"a": "ok", "b": "stale"}}, "v", "allok") is False
        assert L._holds({"v": {"a": "degraded"}}, "v", "allok") is False

    def test_an_unknown_predicate_raises_instead_of_passing(self):
        """谓词名打错时必须炸，不能默默返回 falsy 让整张表失效。"""
        import pytest
        with pytest.raises(ValueError):
            L._holds({"v": 1}, "v", "num++")


# ---------------------------------------------------------------------------
# SOP 第 4 步：不追那张常量表，改问「这张表本身对不对」
#
# 问题：**ledger 里真实出现过的每个 guard，都登记在 EVIDENCE 里了吗？**
# 没登记的 guard 说 "ok" 时，L3 一个字段都不看 —— 它有一格状态，但那格背后没有证据。
#
# 实测（2026-09-03，`data/history/run_ledger.jsonl` 17 行 / 10 个 session）：
#   **`shortlist_feedback` 出现 12 次，12 次都说 ok，12 次都零证据检查。**
#
# ⚠️ 我没有把它登记进 EVIDENCE。登记会改变夜间闸检查什么、可能当场变红挡住数据发布，
# 那是数据端的决定，不该由 05:00 的无人值守夜班替他做（同 09-02 那三份未登记归档的处理）。
# 这里只加守卫：**第二个不登记的 guard 就红**，已知的那个具名豁免并带防腐断言。
# ---------------------------------------------------------------------------

# 已知未登记、已投递给数据端待判的 guard。登记或退役之后，本行必须删掉。
KNOWN_UNCOVERED_GUARDS = {"shortlist_feedback"}


class TestEveryLedgerGuardIsCovered:

    def _guards_in_real_ledger(self):
        from pathlib import Path
        p = Path("data/history/run_ledger.jsonl")
        if not p.exists():
            return None
        seen = set()
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            seen |= set((row.get("guards") or {}))
        return seen

    def test_no_new_guard_slips_in_without_evidence(self):
        """第 N+1 个不登记的 guard 就红 —— 从「看不见」变成「写在那儿」。"""
        seen = self._guards_in_real_ledger()
        if seen is None:
            import pytest
            pytest.skip("no real ledger in this tree")
        uncovered = seen - set(L.EVIDENCE) - KNOWN_UNCOVERED_GUARDS
        assert not uncovered, (
            f"这些 guard 会写进 ledger 但 EVIDENCE 表里没有，说 ok 时零证据检查：{sorted(uncovered)}。"
            f"要么登记进 EVIDENCE，要么写进 KNOWN_UNCOVERED_GUARDS 并投递给数据端。")

    def test_the_exemption_list_does_not_rot(self):
        """豁免清单的防腐断言：某个已被登记或已退役的名字，必须从清单里删掉。"""
        seen = self._guards_in_real_ledger()
        if seen is None:
            import pytest
            pytest.skip("no real ledger in this tree")
        stale = {g for g in KNOWN_UNCOVERED_GUARDS if g in L.EVIDENCE or g not in seen}
        assert not stale, (
            f"KNOWN_UNCOVERED_GUARDS 里这些名字已经不需要豁免了（已登记或已不再出现），"
            f"请删掉该行：{sorted(stale)}")

    def test_an_uncovered_guard_saying_ok_really_does_pass_unchecked(self):
        """阳性对照：证明「不在 EVIDENCE 里」这件事真的让 L3 失明，不是我推理出来的。"""
        row = _row("2026-08-21", guards=_guards(
            shortlist_feedback={"status": "ok"}))          # 零证据字段
        rep = L.audit_run(row)
        assert not [v for v in rep["violations"] if "shortlist_feedback" in v], rep["violations"]
        # 对照：同样零证据，但名字在 EVIDENCE 里 -> 必须报 L3
        row2 = _row("2026-08-21", guards=_guards(shortlist={"status": "ok"}))
        rep2 = L.audit_run(row2)
        assert [v for v in rep2["violations"] if v.startswith("L3 shortlist")], rep2["violations"]
