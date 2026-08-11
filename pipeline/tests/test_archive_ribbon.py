"""archive_ribbon -- global calendar blocks, stored values only, gaps explicit."""
from pipeline.themes.build_groups import archive_ribbon


def dates(n):
    return [f"2026-01-{i+1:02d}" for i in range(n)]


def rows(idx, group="X"):
    """Archive rows for this group on the given session indices."""
    return [{"date": f"2026-01-{i+1:02d}", "kind": "industry", "group": group,
             "state": f"S{i}", "excess_3m": str(i / 10), "rs_accel": str(-i / 100)}
            for i in idx]


def test_young_archive_yields_nothing():
    # 9 sessions: no complete fortnight, no cell — absence, not a zero cell
    assert archive_ribbon(rows(range(9)), dates(9)) == []


def test_partial_block_is_excluded():
    # 23 sessions = 2 complete blocks + 3 leftover oldest, which don't count
    out = archive_ribbon(rows(range(23)), dates(23))
    assert len(out) == 2
    # oldest-first; each cell is the group's last stored row in its block
    assert out[0]["state"] == "S12" and out[1]["state"] == "S22"
    assert out[1]["level"] == 2.2 and out[1]["accel"] == -0.22


def test_caps_at_five_cells():
    out = archive_ribbon(rows(range(70)), dates(70))
    assert len(out) == 5
    assert out[-1]["state"] == "S69"


def test_blocks_cut_on_the_calendar_not_the_group():
    # 20 global sessions; the group only has rows on the FIRST 10. Chunking
    # its own rows would stitch them into the "latest" fortnight; the calendar
    # puts them in the older block and leaves the recent block an explicit gap.
    out = archive_ribbon(rows(range(10)), dates(20))
    assert len(out) == 2
    assert out[0]["state"] == "S9"   # older fortnight: last row it had
    assert out[1] is None            # recent fortnight: the group was absent


def test_absent_mid_block_takes_last_present_session():
    # group missed the final 3 sessions of the block: cell = last one present
    out = archive_ribbon(rows(range(7)), dates(10))
    assert len(out) == 1 and out[0]["state"] == "S6"


def test_rerun_dates_do_not_double():
    doubled = rows(range(20)) + rows(range(20))
    assert len(archive_ribbon(doubled, dates(20))) == 2


def test_broken_stored_row_is_a_gap_not_a_zero():
    r = rows(range(10))
    r[-1]["excess_3m"] = ""
    out = archive_ribbon(r, dates(10))
    assert out[0]["level"] is None and out[0]["state"] == "S9"
