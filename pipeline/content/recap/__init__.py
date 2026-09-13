"""Daily market recap toolchain (fetch_transcript → build_pack → render).

Private-by-construction: every artifact these tools write (transcripts, packs,
HTML, PDF) goes under ``RECAP_ROOT`` on the local disk, never into the repo —
the repo is public. See ``.claude/skills/daily-recap/SKILL.md``.
"""
from pathlib import Path
import os

RECAP_ROOT = Path(os.environ.get(
    "FLUXUS_RECAP_ROOT",
    str(Path.home() / "Documents" / "Trading" / "01_Market_Reports_Daily"),
))


def month_dir(date_iso: str, sample: bool = False) -> Path:
    """~/Documents/Trading/01_Market_Reports_Daily/YYYY-MM[/samples]."""
    d = RECAP_ROOT / date_iso[:7]
    return d / "samples" if sample else d


def pack_dir(date_iso: str, sample: bool = False) -> Path:
    return month_dir(date_iso, sample) / f"pack_{date_iso}"
