"""One-command check of the first TML night (Moglen 2020, merged 2026-09-18).

Answers three things off the published outputs: did the nightly run under the
NEW definition yet (weinstein_stage present), how many TMLs today, and does the
panel agree with leaders_log. profit_margin / roe coverage is reported because a
low share is why the first ~8 nights under-report.
"""
import csv
import json
from pathlib import Path

import pytest

from pipeline.tools import audit_tml as A


def _write(tmp, universe_rows, panel, log_rows, ts="2026-09-18T23:10:00+00:00"):
    out = tmp / "data" / "output"; out.mkdir(parents=True)
    hist = tmp / "data" / "history"; hist.mkdir(parents=True)
    (out / "universe.json").write_text(json.dumps({"timestamp": ts, "rows": universe_rows}))
    (out / "watchlist.json").write_text(json.dumps(
        {"date": "2026-09-18", "zones": [{"panels": [dict(panel, key="true_market_leaders")]}]}))
    with (hist / "leaders_log.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "ticker", "tml"])
        w.writeheader()
        for r in log_rows:
            w.writerow(r)
    return out, hist


def _rows(n, **over):
    base = {"weinstein_stage": 2, "profit_margin": 0.3, "roe": 0.2}
    base.update(over)
    return [dict(base, ticker=f"T{i}") for i in range(n)]


def test_new_definition_live_and_panel_matches_log(tmp_path):
    out, hist = _write(
        tmp_path,
        _rows(100),
        {"count": 2, "tickers": [{"ticker": "DELL"}, {"ticker": "HPE"}]},
        [{"date": "2026-09-18", "ticker": t, "tml": "True"} for t in ("DELL", "HPE")]
        + [{"date": "2026-09-18", "ticker": "X", "tml": "False"}],
    )
    r = A.audit(out, hist)
    assert r["live"] is True
    assert r["count"] == 2 and r["tickers"] == ["DELL", "HPE"]
    assert r["consistent"] is True
    assert r["exit"] == 0


def test_not_live_when_weinstein_stage_absent(tmp_path):
    out, hist = _write(
        tmp_path,
        [{"ticker": f"T{i}", "rs_1m": 90} for i in range(50)],   # old universe, no new fields
        {"count": 0, "tickers": []}, [],
    )
    r = A.audit(out, hist)
    assert r["live"] is False and r["exit"] == 2


def test_panel_log_mismatch_is_flagged(tmp_path):
    out, hist = _write(
        tmp_path, _rows(80),
        {"count": 1, "tickers": [{"ticker": "DELL"}]},
        [{"date": "2026-09-18", "ticker": "DELL", "tml": "True"},
         {"date": "2026-09-18", "ticker": "HPE", "tml": "True"}],   # log has 2, panel 1
    )
    r = A.audit(out, hist)
    assert r["consistent"] is False and r["exit"] == 1


def test_reports_fundamental_coverage(tmp_path):
    rows = _rows(10, profit_margin=None)                 # margins missing on all
    for r in rows[:4]:
        r["profit_margin"] = 0.3                          # 4/10 covered
    out, hist = _write(tmp_path, rows, {"count": 0, "tickers": []}, [])
    r = A.audit(out, hist)
    assert r["coverage"]["profit_margin"] == (4, 10)
    assert r["coverage"]["weinstein_stage"] == (10, 10)


def test_the_real_outputs_parse(tmp_path):
    """Smoke: the command runs on whatever is in data/output today without raising."""
    repo = Path(__file__).resolve().parents[2]
    if not (repo / "data/output/watchlist.json").exists():
        pytest.skip("no outputs in checkout")
    r = A.audit(repo / "data/output", repo / "data/history")
    assert "live" in r and "count" in r and r["exit"] in (0, 1, 2)


# ---------------------------------------------------------------------------
# `_fmt` and `main` (2026-10-02, T-1002-10).
#
# The first mutation sweep of this guard read 24/44 = 55%, the weakest of the
# seven measured that night, and 12 of its 20 survivors sat in these two
# functions -- because all five tests above call `audit()` and nothing had ever
# entered the path that REPORTS its verdict. Same shape as audit_event_agreement
# on 09-27: the judging function was pinned while the lines that caught its
# verdict had no coverage at all. A guard's exit code and its printed line are
# what a person acts on.
#
# Every test below names the survivor it kills and was run against that mutant
# first. A test written against a line it cannot fail on raises the kill rate
# and pins nothing (09-25).
# ---------------------------------------------------------------------------

def _live(tmp_path, panel_tickers, log_tickers, n=4):
    """A live night: `n` universe rows, a panel, and a log."""
    return _write(
        tmp_path, _rows(n),
        {"count": len(panel_tickers), "tickers": [{"ticker": t} for t in panel_tickers]},
        [{"date": "2026-09-18", "ticker": t, "tml": "True"} for t in log_tickers])


def test_missing_outputs_exits_2_and_never_reports_ok(tmp_path):
    """Kills L124 `2 -> 3` and L122 `drop not`.

    `drop not` is the one that matters: inverted, the audit runs only when
    `watchlist.json` is ABSENT, so a complete set of outputs exits 2 ("no
    outputs here") and a missing one proceeds. An exit code nothing pins is an
    exit code a wrapper can misread forever."""
    empty = tmp_path / "nothing"
    empty.mkdir()
    assert A.main([str(empty), str(empty)]) == 2


def test_present_outputs_do_not_take_the_missing_outputs_branch(tmp_path):
    """The other side of L122. Both sides of a boolean judgement need a test or
    the sweep keeps finding the line (09-27 rule)."""
    out, hist = _live(tmp_path, ["DELL", "HPE"], ["DELL", "HPE"])
    assert A.main([str(out), str(hist)]) == 0


def test_main_returns_the_audits_exit_code_not_its_own(tmp_path):
    """`main` is a pass-through for `r["exit"]`; nothing pinned that it stays
    one. Here the audit says 1 (mismatch) and `main` must not flatten it to 0."""
    out, hist = _live(tmp_path, ["DELL", "HPE"], ["ZZZZ"])
    assert A.audit(out, hist)["exit"] == 1
    assert A.main([str(out), str(hist)]) == 1


def test_not_live_says_not_live_and_stops_before_the_count(tmp_path):
    """Kills L94 `drop not`. Inverted, the NOT-LIVE notice prints on a live
    night and a genuinely not-yet-run night is reported as a count of TMLs --
    the guard's most misleading possible output."""
    out, hist = _write(tmp_path, [{"ticker": f"T{i}", "rs_1m": 90} for i in range(5)],
                       {"count": 0, "tickers": []}, [])
    text = A._fmt(A.audit(out, hist))
    assert "NOT LIVE" in text
    assert "TML today" not in text


def test_a_live_night_does_not_print_the_not_live_notice(tmp_path):
    """The other side of L94."""
    out, hist = _live(tmp_path, ["DELL", "HPE"], ["DELL", "HPE"])
    text = A._fmt(A.audit(out, hist))
    assert "NOT LIVE" not in text
    assert "TML today: 2" in text


def test_a_mismatch_names_which_side_each_ticker_is_only_on(tmp_path):
    """Kills L104 `drop not`: inverted, the side-by-side diff prints only when
    the two sides AGREE -- where both sets are empty, so it prints nothing --
    and is silent on the mismatch it exists to explain. Counts match here (2
    and 2) so the only evidence of the disagreement IS this diff."""
    out, hist = _live(tmp_path, ["DELL", "HPE"], ["DELL", "ZZZZ"])
    r = A.audit(out, hist)
    assert r["count"] == r["log_count"] and r["consistent"] is False
    text = A._fmt(r)
    assert "MISMATCH" in text
    assert "only on panel: HPE" in text
    assert "only in log:   ZZZZ" in text


def test_coverage_percent_is_a_percent(tmp_path):
    """Kills L113 `100 -> 101`: 4/4 must read 100%, not 101%."""
    out, hist = _live(tmp_path, ["DELL"], ["DELL"])
    assert "profit_margin          4/4 (100%)" in A._fmt(A.audit(out, hist))


def test_a_zero_denominator_prints_a_dash_instead_of_dividing():
    """The `if d else "—"` arm of L113.

    Reached through `_fmt` directly and not through `audit()` on purpose: the
    live branch is only entered when `weinstein_stage` has a hit, which means
    the universe is non-empty, which means every denominator is non-zero. The
    arm is unreachable from the audit and reachable from the renderer, so the
    renderer is where it gets its test."""
    assert "—" in A._fmt({"date": "2026-09-18", "live": True, "count": 0, "tickers": [],
                          "truncated": 0, "log_count": 0, "log_tickers": [],
                          "consistent": True, "coverage": {"profit_margin": (0, 0)}})


def test_no_date_renders_the_placeholder_not_a_blank(tmp_path):
    """Kills L93 `Or -> And`: with `and`, a present date renders as the empty
    string and the header loses the day the check is about."""
    out, hist = _live(tmp_path, ["DELL"], ["DELL"])
    r = A.audit(out, hist)
    assert "TML check -- 2026-09-18" in A._fmt(r)
    assert "TML check -- (no date)" in A._fmt(dict(r, date=""))


def test_the_two_positional_arguments_land_on_argv_0_and_argv_1(tmp_path, monkeypatch):
    """Kills L120 `0 -> 1` and L121 `1 -> 2`. Shifted by one, the tool audits
    `data/output` while the caller believes it audited the directory it named --
    a guard reporting on a tree nobody asked about."""
    out, hist = _live(tmp_path, ["DELL"], ["DELL"])
    seen = {}
    monkeypatch.setattr(A, "audit", lambda o, h: seen.update(out=o, hist=h) or
                        {"date": "", "live": False, "coverage": {}, "exit": 0})
    A.main([str(out), str(hist)])
    assert seen == {"out": Path(str(out)), "hist": Path(str(hist))}
