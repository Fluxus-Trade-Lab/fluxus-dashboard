"""Regression: a regime_ledger failure must not take tick_cycle.json with it.

2026-09-11 (Plumber Joe): in `run_all.main()` the regime_ledger block binds
`lrow` inside its own try (`lrow, lerrs = build_row(refresh=True)`). When the
import or `build_row` raised -- or `build_row` returned something that does
not unpack -- `lrow` was never bound, that except logged and moved on, and the
very next block, tick_cycle, read `lrow` in
`write_tick_cycle_json(lrow["date"] if lrow else last_completed_session()...)`.
UnboundLocalError, swallowed by tick_cycle's own except: tick_cycle.json went
stale in silence. The `else` fallback the author wrote was unreachable -- two
"own failure domain" blocks that were in fact one.

`main()` is one long function with no smaller entry point, and driving the
whole orchestrator is the slow end-to-end smoke test (not run in CI). So this
test lifts the REAL statements out of `main()` -- the ledger try, any plain
setup statements directly above it, and the tick_cycle try -- compiles them
into a function of their own and runs them with the network-facing callees
stubbed. It executes main's code, not a copy of it: edit either block and the
test runs the edit.
"""

from __future__ import annotations

import ast
import logging
import textwrap
from datetime import date
from pathlib import Path

import pytest

import pipeline.screeners.run_all as RA

SRC = Path(RA.__file__)
FAKE_SESSION = date(2026, 9, 10)


def _calls_named(node, name) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == name) or \
               (isinstance(f, ast.Attribute) and f.attr == name):
                return True
    return False


def _segment_source() -> tuple[str, int]:
    tree = ast.parse(SRC.read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    body = main.body
    ledger_i = next(i for i, s in enumerate(body)
                    if isinstance(s, ast.Try) and _calls_named(s, "build_row"))
    tick_i = next(i for i, s in enumerate(body)
                  if isinstance(s, ast.Try) and _calls_named(s, "write_tick_cycle_json"))
    assert tick_i > ledger_i, "tick_cycle block no longer follows the regime_ledger block"
    # include the plain setup statements directly above the ledger try (e.g. a
    # `lrow = None` initialiser) -- stop at the previous try / compound block
    start = ledger_i
    while start > 0 and isinstance(body[start - 1], (ast.Assign, ast.AnnAssign)):
        start -= 1
    lines = SRC.read_text().splitlines()
    first = body[start].lineno - 1
    last = body[tick_i].end_lineno
    return textwrap.dedent("\n".join(lines[first:last])), first + 1


class _RecLedger:
    def __init__(self):
        self.paths = []

    def wrote(self, path):
        self.paths.append(Path(path).name)


def _run_segment(tmp_path, monkeypatch, *, build_row):
    import pipeline.risk.regime_ledger as RL

    calls = []

    def fake_write_tick_cycle_json(ledger_date):
        calls.append(ledger_date)
        return None                      # "no reading" path: no log formatting needed

    monkeypatch.setattr(RL, "build_row", build_row)
    monkeypatch.setattr(RL, "append", lambda row: True)
    monkeypatch.setattr(RL, "report_problems", lambda row, errs: [])
    monkeypatch.setattr(RL, "write_tick_cycle_json", fake_write_tick_cycle_json)

    seg, lineno = _segment_source()
    # pad so tracebacks point at run_all.py's real line numbers
    src = "\n" * (lineno - 2) + "def _segment(ledger, logger):\n" + textwrap.indent(seg, "    ") + "\n"
    ns = dict(vars(RA))                  # run_all's own globals: _mtime_ns, _record_external, ...
    ns["OUTPUT_DIR"] = tmp_path
    ns["last_completed_session"] = lambda: FAKE_SESSION
    exec(compile(src, str(SRC), "exec"), ns)

    logger = logging.getLogger("test_run_all_tick_cycle_isolation")
    ns["_segment"](_RecLedger(), logger)
    return calls


def _boom(refresh=True):
    raise RuntimeError("regime_ledger upstream down")


@pytest.mark.parametrize("build_row", [
    _boom,                                   # build_row raises
    lambda refresh=True: None,               # returns None -> tuple unpack fails (what the smoke test stubs)
], ids=["build_row_raises", "build_row_returns_none"])
def test_ledger_failure_falls_back_to_last_completed_session(tmp_path, monkeypatch, caplog, build_row):
    with caplog.at_level(logging.INFO, logger="test_run_all_tick_cycle_isolation"):
        calls = _run_segment(tmp_path, monkeypatch, build_row=build_row)

    msgs = [r.getMessage() for r in caplog.records]
    assert not any("tick_cycle failed" in m for m in msgs), \
        f"tick_cycle was taken down by the ledger failure: {msgs}"
    assert calls == [FAKE_SESSION.isoformat()], \
        f"write_tick_cycle_json should fall back to last_completed_session(); got calls={calls}"
    # and the ledger failure itself is still reported, not swallowed silently
    assert any("Regime ledger failed" in m for m in msgs), msgs


def test_ledger_success_passes_its_own_date(tmp_path, monkeypatch):
    """The other branch of the same conditional -- proves the harness really
    reaches write_tick_cycle_json with main's arguments, not a constant."""
    row = {"date": "2026-09-09", "lamps_on": 1, "lamps_available": 4, "prob_3d": 0.1}
    calls = _run_segment(tmp_path, monkeypatch, build_row=lambda refresh=True: (row, []))
    assert calls == ["2026-09-09"]
