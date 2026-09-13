"""Daily market recap toolchain (fetch_transcript → build_pack → content → run.py render).

Private-by-construction: every artifact these tools write (transcripts, packs, HTML, PDF, images,
ledger) goes under ``RECAP_ROOT`` on the local disk, never into the repo — the repo is public.
See ``.claude/skills/daily-recap/SKILL.md`` and ``CONTENT_SCHEMA.md``.

Layout per issue (issue = ``2026-09-11`` or ``2026-W37``; month = the issue's last session):
    RECAP_ROOT/YYYY-MM/<issue>/{pdf,img/EN,img/ZH,x,pack}/ + delivery.md
Samples keep their old home: RECAP_ROOT/YYYY-MM/samples/pack_<issue>/.
"""
from pathlib import Path
import os

RECAP_ROOT = Path(os.environ.get(
    "FLUXUS_RECAP_ROOT",
    str(Path.home() / "Documents" / "Trading" / "01_Market_Reports_Daily"),
))


def last_session(label: str) -> str:
    """Issue label → its last session (ISO date). Daily labels are already a date."""
    if "-W" in label:
        from pipeline.content.recap.weeks import week_sessions  # lazy: avoids import cycles at package init
        return week_sessions(label)[-1].isoformat()
    return label


def month_dir(date_iso: str, sample: bool = False) -> Path:
    """RECAP_ROOT/YYYY-MM[/samples]."""
    d = RECAP_ROOT / date_iso[:7]
    return d / "samples" if sample else d


def issue_dir(label: str) -> Path:
    return RECAP_ROOT / last_session(label)[:7] / label


def pack_dir(label: str, sample: bool = False) -> Path:
    """Where fetch/build_pack write and the writing session reads: <issue>/pack, or samples/pack_<issue>."""
    if sample:
        return month_dir(last_session(label), True) / f"pack_{label}"
    return issue_dir(label) / "pack"
