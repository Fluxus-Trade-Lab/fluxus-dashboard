"""T-0920-12: backfill_preset_hits already rejects a snapshot whose OWN clock
(timestamp/bar_date) names a different session than the archive date --
`payload_disagrees()`. That catches F1 (premarket) in practice, because a
premarket generation timestamp resolves to the PRIOR completed session.

It does not catch F2 (avg_volume outage): the timestamp and bar_date are
correct for that session, only avg_volume is dead, so `payload_disagrees`
sees no disagreement. Per audit_universe_freshness's own numbers this has not
happened yet for a date already in the archive (0 preset:* dup keys, the 9
F4 sessions have zero preset:* rows) -- but nothing stops it happening next
time an avg_volume outage lands on a day the seven core screeners accepted.
`payload_is_unfresh()` closes that gap for the future.
"""
from __future__ import annotations


def _rows_outage(n=2_999):
    rows = [{'volume': 500_000, 'avg_volume': None} for _ in range(n)]
    rows.append({'volume': 500_000, 'avg_volume': 5_000})
    return rows


def _rows_clean(n=3_000):
    return [{'volume': 980, 'avg_volume': 1_000} for _ in range(n)]


class TestPayloadIsUnfresh:
    def test_an_avg_volume_outage_payload_is_flagged(self):
        from pipeline.tools.backfill_preset_hits import payload_is_unfresh

        why = payload_is_unfresh({'rows': _rows_outage()})
        assert why is not None
        assert why.startswith('F2')

    def test_a_premarket_shaped_payload_is_flagged(self):
        from pipeline.tools.backfill_preset_hits import payload_is_unfresh

        rows = [{'volume': 241, 'avg_volume': 10_000} for _ in range(5_618)]
        why = payload_is_unfresh({'rows': rows})
        assert why is not None
        assert why.startswith('F1')

    def test_a_normal_session_is_not_flagged(self):
        from pipeline.tools.backfill_preset_hits import payload_is_unfresh

        assert payload_is_unfresh({'rows': _rows_clean()}) is None
