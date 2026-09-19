"""oratnek_diff picks the earliest universe.json commit after `--asof` --
but "earliest committed" and "a completed session" are different claims.
T-0920-12: linda's freshness audit (pipeline/tools/audit_universe_freshness.py,
156 snapshots) found 13 that are not: 5 premarket (F1), 8 an avg_volume outage
(F2). The old selection took whichever commit landed first with no freshness
check, so on a night the cron's real post-close commit is missing it would
silently grab next morning's premarket snapshot instead.
"""
from __future__ import annotations


def _payload(rows):
    return {'rows': rows}


def _premarket_rows(n=5_618):
    """F1 shape: 2026-08-10 05:31, real rvol 0.0241."""
    return [{'volume': 241, 'avg_volume': 10_000} for _ in range(n)]


def _clean_rows(n=5_618):
    """A normal closed session, rvol ~0.98."""
    return [{'volume': 980, 'avg_volume': 1_000} for _ in range(n)]


class TestPickUsableCommit:
    def test_skips_a_premarket_commit_for_the_next_one(self):
        """The old code (`sorted(cands)[0][1]`) would return 'bad' here --
        that is the exact bug. The new selector must not."""
        from pipeline.tools.oratnek_diff import pick_usable_commit

        cands = [('2026-08-11T05:31:00+00:00', 'bad'),
                 ('2026-08-11T21:03:00+00:00', 'good')]
        payloads = {'bad': _payload(_premarket_rows()), 'good': _payload(_clean_rows())}

        picked = pick_usable_commit(sorted(cands), lambda sha: payloads[sha])
        assert picked == 'good'

    def test_a_clean_first_candidate_is_used_as_before(self):
        from pipeline.tools.oratnek_diff import pick_usable_commit

        cands = [('2026-08-11T21:03:00+00:00', 'good')]
        payloads = {'good': _payload(_clean_rows())}

        picked = pick_usable_commit(sorted(cands), lambda sha: payloads[sha])
        assert picked == 'good'

    def test_all_candidates_bad_returns_none(self):
        """Nothing usable -- caller must error out, not silently use a bad one."""
        from pipeline.tools.oratnek_diff import pick_usable_commit

        cands = [('2026-08-11T05:31:00+00:00', 'premarket'),
                 ('2026-08-12T05:31:00+00:00', 'also_premarket')]
        payloads = {'premarket': _payload(_premarket_rows()),
                    'also_premarket': _payload(_premarket_rows())}

        picked = pick_usable_commit(sorted(cands), lambda sha: payloads[sha])
        assert picked is None

    def test_an_avg_volume_outage_commit_is_also_skipped(self):
        """F2 shape: denominator died, not just F1's premarket shape."""
        from pipeline.tools.oratnek_diff import pick_usable_commit

        outage_rows = [{'volume': 500_000, 'avg_volume': None} for _ in range(2_999)]
        outage_rows.append({'volume': 500_000, 'avg_volume': 5_000})
        cands = [('2026-07-16T21:03:00+00:00', 'outage'),
                 ('2026-07-17T21:03:00+00:00', 'good')]
        payloads = {'outage': _payload(outage_rows), 'good': _payload(_clean_rows())}

        picked = pick_usable_commit(sorted(cands), lambda sha: payloads[sha])
        assert picked == 'good'


class TestSnapshotCommitRaisesWhenAllCandidatesAreBad(object):
    def test_snapshot_commit_raises_systemexit_when_only_premarket_is_available(self, monkeypatch):
        """Wiring test: snapshot_commit() must call the freshness gate, not
        just return sorted(cands)[0][1] like it used to."""
        import subprocess
        import json as json_mod
        from pipeline.tools import oratnek_diff

        log_line = "bad 2026-08-11T05:31:00+00:00\n"

        def fake_run(args, capture_output=True, text=True, check=True):
            class R:
                pass
            r = R()
            if args[:2] == ['git', 'log']:
                r.stdout = log_line
            elif args[:2] == ['git', 'show']:
                r.stdout = json_mod.dumps(_payload(_premarket_rows()))
            else:
                raise AssertionError(args)
            return r

        monkeypatch.setattr(subprocess, 'run', fake_run)
        try:
            oratnek_diff.snapshot_commit('2026-08-10')
            assert False, 'expected SystemExit'
        except SystemExit as e:
            assert 'F1' in str(e) or 'no usable' in str(e)
