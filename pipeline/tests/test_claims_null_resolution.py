"""A NULL claim must say how big an effect it could have seen.

"We found nothing" is two different sentences -- "there is nothing" and
"we could not have seen it" -- and the registry could not tell them apart.
This is the third time the same shape reached a write-up (三次律 ②, so it
becomes a check instead of another memory):

  1. block sign-flip under Holm could not report a positive at all
     (floor p = 0.219) -- pitfall_a_stricter_test_can_be_blind;
  2. an 8-date sign test's smallest possible p was 0.0078, 0.1875 after
     Bonferroni -- pitfall_compute_the_minimum_possible_p_first;
  3. 2026-09-12 reversal_checklist: I reported the spread of a permutation
     null's point estimate (+-0.14%) as the test's resolution; the real
     week-clustered interval was +-0.5%, 3.5x wider, and the adversarial
     verifier caught it.

So a claim whose status is `null` carries `evidence.resolution`:

    {"mde": "<smallest effect it could have reported>",
     "method": "<how that was measured: injection / 2.8 x clustered SE / ...>"}

or, when a detectable-effect size is meaningless for that claim,
    {"na": "<why>"}

`method` is required next to `mde` because the third incident above HAD a
number; it was the wrong kind of number. Detection is by structure, not by
grepping prose for words like 分辨率 -- a vocabulary list only measures the
vocabulary of whoever wrote it.

Runs in tests.yml, NOT in claim_registry --check: that one sits in the
nightly data job before the commit step, and a docs-shaped violation there
would cost a night of market data.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from pipeline.tools.claim_registry import REGISTRY, load

ROOT = Path(__file__).resolve().parents[2]

# Registered before this rule existed; each lacks evidence.resolution.
# RATCHET: this set may only shrink. Backfilling one (or retiring it) makes
# N2/N3 fire until its entry is deleted here.  (owner, declared_on)
LEGACY: dict[str, tuple[str, str]] = {
    "tightness-compression-no-standalone-edge": ("Nighty Zac", "2026-09-12"),
    "tightness-rmv-below-baseline": ("Nighty Zac", "2026-09-12"),
    "ma-reclaim-no-volume": ("Nighty Zac", "2026-09-12"),
    "oratnek-width-not-universe": ("Nighty Zac", "2026-09-12"),
    "adr-floor-no-selection-edge": ("Nighty Zac", "2026-09-12"),
    "theme-ladder-window-mismatch": ("Nighty Zac", "2026-09-12"),
}


def resolution_of(row: dict) -> str | None:
    res = (row.get("evidence") or {}).get("resolution")
    if not isinstance(res, dict):
        return None
    if str(res.get("mde") or "").strip() and str(res.get("method") or "").strip():
        return "mde"
    if str(res.get("na") or "").strip():
        return "na"
    return None


def violations(rows: list[dict], legacy: dict) -> list[str]:
    out = []
    by_id = {r.get("id"): r for r in rows}
    for r in rows:
        if r.get("status") != "null":
            continue
        rid, has = r.get("id"), resolution_of(r)
        if has is None and rid not in legacy:
            out.append(f"N1 {rid}: status null without evidence.resolution "
                       f"({{mde, method}} or {{na}})")
        if has is not None and rid in legacy:
            out.append(f"N2 {rid}: carries a resolution now -- delete it from LEGACY")
    for rid in legacy:
        r = by_id.get(rid)
        if r is None:
            out.append(f"N3 {rid}: in LEGACY but not in the registry")
        elif r.get("status") != "null":
            out.append(f"N3 {rid}: in LEGACY but status is {r.get('status')!r} now")
    return out


@pytest.fixture(scope="module")
def real_rows():
    return load(ROOT / REGISTRY)


def _null(rid="x-null", **res):
    row = {"id": rid, "status": "null", "direction": "null", "claim": "c",
           "evidence": {}}
    if res:
        row["evidence"]["resolution"] = res
    return row


def test_real_registry_is_clean(real_rows):
    assert violations(real_rows, LEGACY) == []


def test_real_registry_has_nulls_at_all(real_rows):
    # guards the test above against passing because it looked at nothing
    nulls = [r for r in real_rows if r.get("status") == "null"]
    assert len(nulls) >= 9
    assert sum(resolution_of(r) is not None for r in nulls) >= 3


def test_positive_control_on_the_real_file(real_rows):
    # a new null claim without a resolution, appended to the real ledger, must be red
    rows = copy.deepcopy(real_rows) + [_null("new-null-claim")]
    v = violations(rows, LEGACY)
    assert v and v[0].startswith("N1 new-null-claim")


def test_mde_without_method_is_not_a_resolution():
    # the 09-12 incident had a number; it was the wrong kind of number
    assert violations([_null(mde="0.14%")], {}) != []
    assert violations([_null(mde="0.74%", method="2.8 x week-cluster SE")], {}) == []


def test_blank_strings_do_not_count():
    assert violations([_null(mde="  ", method="x")], {}) != []
    assert violations([_null(na="")], {}) != []


def test_na_with_reason_counts():
    assert violations([_null(na="descriptive shape comparison, no effect size")], {}) == []


def test_non_null_status_is_not_asked():
    row = {"id": "c1", "status": "candidate", "direction": "positive", "evidence": {}}
    assert violations([row], {}) == []


def test_ratchet_backfilled_legacy_must_leave_the_list():
    v = violations([_null("old", mde="1pp", method="injection")], {"old": ("Z", "d")})
    assert v == ["N2 old: carries a resolution now -- delete it from LEGACY"]


def test_ratchet_legacy_that_vanished_or_changed_status():
    assert violations([], {"gone": ("Z", "d")})[0].startswith("N3 gone")
    row = {"id": "moved", "status": "retracted", "evidence": {}}
    assert violations([row], {"moved": ("Z", "d")})[0].startswith("N3 moved")


def test_legacy_entries_name_an_owner():
    for rid, meta in LEGACY.items():
        assert len(meta) == 2 and meta[0].strip() and meta[1].strip(), rid
