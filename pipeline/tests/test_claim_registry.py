"""Claim registry -- the checks that make RESEARCH_PROTOCOL.md enforceable.

Two halves: unit tests of the rules on synthetic rows, and one live test that
the committed registry itself is clean (this is the same check CI runs, so a
bad edit to claims.jsonl fails the suite locally first)."""
import json

import pytest

from pipeline.tools.claim_registry import REGISTRY, check, load


def row(**kw):
    base = {"id": "x-claim", "claim": "X beats Y", "direction": "positive",
            "status": "candidate", "spec_search_n": 5,
            "evidence": {"in_sample": {"n": 100}},
            "gates": [], "code_refs": [], "study": "data/reference/RESEARCH_PROTOCOL.md",
            "registered": "2026-08-23", "updated": "2026-08-23"}
    base.update(kw)
    return base


class TestRules:
    def test_clean_row_passes(self):
        assert check([row()]) == []

    def test_duplicate_ids_flagged(self):
        errs = check([row(), row()])
        assert any("duplicate" in e for e in errs)

    def test_positive_without_search_n_flagged(self):
        errs = check([row(spec_search_n=None)])
        assert any("R2" in e for e in errs)

    def test_null_claims_need_no_search_n(self):
        assert check([row(direction="null", status="null", spec_search_n=None)]) == []

    def test_validated_requires_holdout(self):
        errs = check([row(status="validated")])
        assert any("R3" in e for e in errs)
        ok = row(status="validated",
                 evidence={"in_sample": {}, "holdout": {"pool": "other", "p": 0.01}})
        assert check([ok]) == []

    def test_candidate_with_gates_is_the_capital_offense(self):
        """铁律 1: a claim that has not survived a holdout must not change
        which names Andy sees. This rule IS the mechanism."""
        errs = check([row(gates=["watchlist.py some_panel"])])
        assert any("R4" in e for e in errs)

    def test_null_may_carry_gates(self):
        """A null result guarding code OUT (e.g. a removed volume clause) is
        legitimate -- negative knowledge can gate."""
        assert check([row(direction="null", status="null",
                          spec_search_n=None, gates=["watchlist.py ma_reclaim no-volume"])]) == []

    def test_retraction_needs_a_reason(self):
        errs = check([row(status="retracted")])
        assert any("R5" in e for e in errs)

    def test_missing_study_file_flagged(self):
        errs = check([row(study="data/research/does_not_exist.md")])
        assert any("R6" in e for e in errs)

    def test_url_study_is_fine(self):
        assert check([row(study="https://claude.ai/code/artifact/x")]) == []


class TestLiveRegistry:
    def test_committed_registry_is_clean_except_known_debts(self):
        """The real claims.jsonl must parse and carry no violations other than
        the ones we knowingly registered as debts (notes must say so)."""
        rows = load(REGISTRY)
        assert len(rows) >= 5
        errs = check(rows)
        for e in errs:
            rid = e.split(":")[0]
            r = next(x for x in rows if x["id"] == rid)
            assert "违规待处理" in (r.get("notes") or ""), \
                f"unregistered violation: {e}"

    def test_every_line_is_one_json_object(self):
        for line in REGISTRY.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                assert isinstance(json.loads(line), dict)
