"""Regression: the breadth enrichment must run on the SUCCESS path.

2026-08-19 (760d7ca): an `if breadth_result is not None:` inserted between
the breadth try's except and its `else:` re-bound the else to the if --
legal Python, inverted meaning. signals / state_board / regime / verdict /
replay then only ran when breadth_result was None (where run_signals(None,..)
throws), so breadth.json shipped without its four enrichment blocks and
market_health.json went stale. This test pins the AST shape: the try that
calls run_breadth_metrics carries a non-empty orelse, and run_signals is
called inside that orelse -- an if-bound else or a de-indented block fails it.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "screeners" / "run_all.py"


def _calls(node, name):
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == name) or \
               (isinstance(f, ast.Attribute) and f.attr == name):
                yield n


def test_breadth_enrichment_is_the_trys_else_branch():
    tree = ast.parse(SRC.read_text())
    breadth_tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)
                     and any(True for _ in _calls(ast.Module(body=n.body, type_ignores=[]),
                                                  "run_breadth_metrics"))]
    assert len(breadth_tries) == 1, "expected exactly one try around run_breadth_metrics"
    t = breadth_tries[0]
    assert t.orelse, "the breadth try lost its else: -- enrichment no longer runs on success"
    orelse = ast.Module(body=t.orelse, type_ignores=[])
    assert any(True for _ in _calls(orelse, "run_signals")), \
        "run_signals must live in the try's else (success path)"
    # and the else must not be the failure path in disguise
    src_seg = ast.get_source_segment(SRC.read_text(), t) or ""
    assert "state_board" in src_seg and "build_regime" in ast.dump(orelse) or \
        any(True for _ in _calls(orelse, "build_regime"))
