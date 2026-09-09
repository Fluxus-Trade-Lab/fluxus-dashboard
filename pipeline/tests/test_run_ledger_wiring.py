"""The run ledger's evidence fields must be wired to the thing they measure.

Two fields in `data/history/run_ledger.jsonl` were structurally incapable of
carrying evidence, and both failures looked exactly like "nothing happened":

* `wrote` was `[]` on every row from the file's creation to 2026-09-10.
  `Ledger.wrote` had one caller in the whole repo -- its own unit test.
  A night that wrote nineteen JSON files and a night that wrote none were
  byte-identical in the ledger.
* `guards.screeners.counts.stockbee_ratio` was `null` on every row, because
  that screener's payload was the only one without a `count` key. Its output
  file was healthy the whole time (2026-09-09: ratio_5d 0.6335, 200 gainers).
  "the screener produced nothing" and "we read the wrong key" printed the
  same `null`.

So these tests are about the *wiring*, not about the numbers: each one fails
if the call that feeds a field is removed, and none of them takes its expected
value from the code under test.
"""

import ast
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from pipeline import run_ledger as RL
from pipeline.run_ledger import Ledger
from pipeline.screeners import run_all as RA
from pipeline.screeners.stockbee_ratio import run as run_stockbee


# --------------------------------------------------------------------------
# `wrote`: recorded, verified, and impossible to bypass
# --------------------------------------------------------------------------

def test_emit_writes_the_file_and_records_it_in_the_ledger(tmp_path):
    """POSITIVE CONTROL. Delete `ledger.wrote(path)` from `run_all._emit`
    and this goes red -- that call is the whole repair."""
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    out = tmp_path / 'breadth.json'

    RA._emit(led, out, json.dumps({'hello': 'world'}))

    assert json.loads(out.read_text()) == {'hello': 'world'}
    assert led.row['wrote'] == ['breadth.json']


def test_emit_passes_write_kwargs_through(tmp_path):
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    out = tmp_path / 'market_health.json'
    RA._emit(led, out, 'café', encoding='utf-8')
    assert out.read_text(encoding='utf-8') == 'café'
    assert led.row['wrote'] == ['market_health.json']


def test_every_output_write_in_run_all_goes_through_emit():
    """POSITIVE CONTROL. Revert any `_emit(ledger, OUTPUT_DIR / 'x.json', ...)`
    back to `(OUTPUT_DIR / 'x.json').write_text(...)` and this goes red.

    `_emit` is only a repair if it is the single door: an output written
    beside it would be missing from `wrote`, and a missing name is the exact
    failure this file exists to stop.
    """
    src = Path(RA.__file__).read_text()
    tree = ast.parse(src)

    inside_emit = {
        n.lineno
        for fn in ast.walk(tree)
        if isinstance(fn, ast.FunctionDef) and fn.name == '_emit'
        for n in ast.walk(fn)
        if hasattr(n, 'lineno')
    }
    assert inside_emit, '_emit disappeared from run_all.py'
    strays = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ('write_text', 'write_bytes')
        and node.lineno not in inside_emit
    ]
    assert not strays, (
        f'run_all.py writes files outside _emit at lines {strays}; those '
        f'files will be missing from the run ledger\'s "wrote" list'
    )


def test_ledger_wrote_refuses_a_name_whose_file_is_not_on_disk(tmp_path):
    """`wrote` must under-report rather than over-report.

    A list naming a file the run did not produce is worse than the empty
    list it replaces: an empty list at least looks empty, while a fabricated
    name would be read as proof.
    """
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    led.wrote(tmp_path / 'never_written.json')
    assert led.row['wrote'] == []


def test_ledger_wrote_does_not_list_the_same_file_twice(tmp_path):
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    real = tmp_path / 'universe.json'
    real.write_text('{}')
    led.wrote(real)
    led.wrote(real)
    assert led.row['wrote'] == ['universe.json']


def test_ledger_wrote_survives_a_bad_argument(tmp_path):
    """The ledger must never cost a run, however it is called."""
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    led.wrote(object())
    assert led.row['wrote'] == []


def test_wrote_reaches_the_jsonl_row(tmp_path, monkeypatch):
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    RA._emit(led, tmp_path / 'rotation.json', '{}')
    led.write()
    row = json.loads((tmp_path / 'run_ledger.jsonl').read_text().splitlines()[0])
    assert row['wrote'] == ['rotation.json']


# --------------------------------------------------------------------------
# Files another module writes: recorded only when this run moved them
# --------------------------------------------------------------------------

def test_record_external_records_a_file_this_run_changed(tmp_path):
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    groups = tmp_path / 'groups.json'
    groups.write_text('{"old": 1}')
    os.utime(groups, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
    before = RA._mtime_ns(groups)

    groups.write_text('{"new": 1}')          # stand-in for save_groups()
    os.utime(groups, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
    RA._record_external(led, groups, before)

    assert led.row['wrote'] == ['groups.json']


def test_record_external_stays_silent_when_the_writer_did_nothing(tmp_path):
    """NEGATIVE CONTROL: yesterday's groups.json is on disk too.

    `save_groups` can fail without removing the previous file, so mere
    existence is not evidence. Only a moved mtime is.
    """
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    groups = tmp_path / 'groups.json'
    groups.write_text('{"yesterday": 1}')
    os.utime(groups, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))

    before = RA._mtime_ns(groups)
    RA._record_external(led, groups, before)   # writer crashed; file untouched

    assert led.row['wrote'] == []


def test_record_external_records_a_file_created_during_the_run(tmp_path):
    led = Ledger(session='2026-09-10', path=tmp_path / 'run_ledger.jsonl')
    tick = tmp_path / 'tick_cycle.json'
    before = RA._mtime_ns(tick)               # None -- not there yet
    assert before is None
    tick.write_text('{}')
    RA._record_external(led, tick, before)
    assert led.row['wrote'] == ['tick_cycle.json']


def test_the_delegated_outputs_are_all_wired():
    """The writes `_emit` cannot cover, because they happen inside the module
    run_all calls. If a fourth one is added without a `_record_external`, its
    file silently drops out of `wrote`."""
    src = Path(RA.__file__).read_text()
    for name in ('groups_history.json', 'correction_risk.json',
                 'tick_cycle.json'):
        assert f"_record_external(ledger, OUTPUT_DIR / '{name}'" in src, name
    # groups.json is wired differently: build_groups.save() returns the path
    # it wrote, so run_all records that instead of naming the file again.
    assert 'ledger.wrote(save_groups(' in src


# --------------------------------------------------------------------------
# `screeners.counts`: an int for every screener, never a bare null
# --------------------------------------------------------------------------

def test_screener_counts_never_contain_none():
    """The field's old shape (`d.get('count')`) turned a missing key into the
    same `null` a dead screener would produce."""
    results = {
        'momentum_97': {'count': 41, 'tickers': []},
        'vcp': {'count': 0, 'results': []},
        'no_count_key': {'signal': 'NEUTRAL'},
        'not_a_dict': [1, 2, 3],
        'count_is_a_string': {'count': '41'},
    }
    counts = RA._screener_counts(results)

    assert None not in counts.values()
    assert counts['momentum_97'] == 41
    assert counts['vcp'] == 0
    # The three broken shapes each say what is wrong instead of printing null.
    assert counts['no_count_key'] == 'no-count-key'
    assert counts['not_a_dict'].startswith('not-a-dict:')
    assert counts['count_is_a_string'].startswith('count-not-int:')


def test_stockbee_ratio_payload_reports_an_int_count(tmp_path):
    """The screener that spent eight nights as `null` in the ledger.

    Expected value is arithmetic done here, not a constant read out of the
    module: five names, two of them up double digits, two down double digits.
    """
    universe = pd.DataFrame({
        'ticker': ['AAA', 'BBB', 'CCC', 'DDD', 'EEE'],
        'change_pct': [0.12, 0.09, 0.002, -0.09, -0.12],
    })
    payload = run_stockbee(universe, str(tmp_path / 'breadth_history.json'),
                           today=date(2026, 9, 9))

    # Asserted through the derivation main uses, so dropping the key fails
    # with "no-count-key != 2" rather than a KeyError from the test itself.
    assert RA._screener_counts({'stockbee_ratio': payload})['stockbee_ratio'] == 2
    assert isinstance(payload['count'], int)
    assert payload['count'] == 2
    assert payload['count'] == payload['gainers_today']


def test_stockbee_ratio_empty_universe_still_answers_count():
    payload = run_stockbee(pd.DataFrame({'ticker': [], 'change_pct': []}),
                           'unused.json')
    assert payload['count'] == 0
    assert RA._screener_counts({'stockbee_ratio': payload})['stockbee_ratio'] == 0


def test_stockbee_count_did_not_disturb_the_published_numbers(tmp_path):
    """`count` is an alias, not a new measurement -- the ratio, the signal and
    the gainer/loser counts must be exactly what they were."""
    universe = pd.DataFrame({
        'ticker': [f'T{i}' for i in range(10)],
        'change_pct': [0.12] * 6 + [-0.12] * 3 + [0.0],
    })
    hist = tmp_path / 'breadth_history.json'
    hist.write_text(json.dumps([
        {'date': '2026-09-08', 'gainers': 6, 'losers': 3},
    ]))
    payload = run_stockbee(universe, str(hist), today=date(2026, 9, 9))

    assert payload['gainers_today'] == 6 and payload['losers_today'] == 3
    assert payload['gainers_5d'] == 12 and payload['losers_5d'] == 6
    assert payload['ratio_5d'] == 2.0
    assert payload['signal'] == 'NEUTRAL'
