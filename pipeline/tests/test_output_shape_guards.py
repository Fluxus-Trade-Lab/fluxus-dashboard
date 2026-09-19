"""Changing universe.json's fields must clear all three nightly guards at commit time.

`universe_cols` in run_all.py is the code's own list of the fields
universe.json ships. Three guards judge that shape, but only at night against
real output, so a shape change passes CI and fails hours later:

* 2026-09-16  a removed output was still expected by the schema baseline
              (`schema_snapshot --check` treats "removed" as fatal) -- night blocked.
* 2026-09-18  f_score dropped from `universe_cols` (421b2777) but still graded
              by the quality guard: "100% missing ... a feed that worked has died"
              -- runs 35399820824 and 35402553203 refused to publish.
* 2026-09-18  sb_avg_dollar_vol_20 added to `universe_cols` (7cc43aef); the
              public-JSON privacy test read `dollar` as an account amount -- tests
              red on main after the night commit (0b8e4195).

This test feeds the declared field list to each guard's own decision function
(no copy of their rules, so it cannot drift from them) and fails in the push
that changes the list, not the night after.
"""
import ast
import csv
import importlib.util
import json
from pathlib import Path

from pipeline import quality

REPO = Path(__file__).resolve().parents[2]
RUN_ALL = REPO / 'pipeline/screeners/run_all.py'
SCHEMA = REPO / 'data/reference/schema_snapshot.json'
QUALITY_HISTORY = REPO / 'data/history/universe_quality.csv'


def declared_universe_cols(source: str) -> list:
    """The literal list assigned to `universe_cols` in run_all.py."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'universe_cols' for t in node.targets):
            return list(ast.literal_eval(node.value))
    raise AssertionError('universe_cols not found in run_all.py -- update this test')


def _privacy():
    spec = importlib.util.spec_from_file_location(
        'privacy', REPO / 'pipeline/tests/test_public_output_privacy.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _quality_history() -> list:
    with QUALITY_HISTORY.open(newline='') as fh:
        return list(csv.DictReader(fh))


def privacy_hits(cols) -> list:
    p = _privacy()
    return [c for c in cols if p._is_banned_key(c) and not p._allowed(
        p.ALLOWED_KEYS, 'data/output/universe.json', f'.rows[].{c}')]


def quality_severe(cols, history) -> dict:
    """What quality.check would say about a night where every declared field is populated."""
    rows = [{c: 1 for c in cols}]
    rates = quality.null_rates(rows, quality.discovered_fields(rows, history))
    verdict = quality.assess(rates, history)
    return {f: v['evidence'] for f, v in verdict['fields'].items() if v['status'] == 'severe'}


def schema_removed(cols) -> list:
    base = set(json.loads(SCHEMA.read_text())['universe.json']['rows[]'])
    return sorted(base - set(cols))


COLS = declared_universe_cols(RUN_ALL.read_text())


def test_declared_fields_pass_the_public_privacy_guard():
    hits = privacy_hits(COLS)
    assert not hits, (
        f'universe_cols ships {hits}, which the public-JSON privacy test reads as '
        'share counts / account dollars. If it is market data, add an exact '
        'ALLOWED_KEYS entry with the reason in test_public_output_privacy.py; '
        'if it is an account amount it must not ship.')


def test_quality_guard_does_not_read_a_dropped_field_as_a_dead_feed():
    severe = quality_severe(COLS, _quality_history())
    assert not severe, (
        f'the quality guard would refuse to publish tonight: {severe}. A field '
        'dropped or renamed on purpose goes into quality.RETIRED_FIELDS with the '
        'commit that removed it.')


def test_schema_baseline_expects_nothing_the_code_no_longer_ships():
    gone = schema_removed(COLS)
    assert not gone, (
        f'data/reference/schema_snapshot.json still expects {gone} in '
        'universe.json rows[], which universe_cols no longer ships; '
        '`schema_snapshot --check` treats "removed" as fatal. Drop them from the baseline.')


# Positive controls: each check must go red on the failure it exists for,
# replayed from the real incidents above.

def test_control_privacy_flags_an_unlisted_dollar_field():
    assert privacy_hits(COLS + ['avg_dollar_vol_pnl']) == ['avg_dollar_vol_pnl']


def test_control_quality_flags_the_f_score_drop_without_its_retirement(monkeypatch):
    history = _quality_history()
    assert any((r.get('f_score') or '') != '' for r in history), \
        'control needs f_score history in universe_quality.csv'
    monkeypatch.setattr(quality, 'RETIRED_FIELDS', quality.RETIRED_FIELDS - {'f_score'})
    assert 'f_score' in quality_severe([c for c in COLS if c != 'f_score'], history)


def test_control_schema_flags_a_field_dropped_from_the_code():
    shipped = sorted(set(json.loads(SCHEMA.read_text())['universe.json']['rows[]']))
    assert schema_removed([c for c in COLS if c != shipped[0]]) == [shipped[0]]


def test_control_parser_reads_the_list_not_a_lookalike():
    src = "x = ['nope']\nuniverse_cols = ['a', 'b']\n"
    assert declared_universe_cols(src) == ['a', 'b']
