"""data/output/*.json 日期键闸 (T-0926-56).

Every top-level object in data/output must carry a recognized date key so a
human or a gate can tell whether the file is stale -- etf_data.json shipped
for a long time with none at all and nothing could have caught that. A new
file that lands with an 8th, unrecognized key name should fail loudly here
rather than silently join the pile (that is how the 09-26 audit's own first
scan misjudged 11 files: it only knew 6 of the 7 names in use).
"""

import json
from pathlib import Path

import pytest

from pipeline.reference.output_date_keys import EXEMPT_FILES, RECOGNIZED_DATE_KEYS

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "output"


def _output_files():
    if not OUTPUT_DIR.is_dir():
        return []
    return sorted(
        p for p in OUTPUT_DIR.glob("*.json") if p.name not in EXEMPT_FILES
    )


@pytest.mark.parametrize("path", _output_files(), ids=lambda p: p.name)
def test_top_level_has_recognized_date_key(path):
    data = json.loads(path.read_text())
    assert isinstance(data, dict), (
        f"{path.name}: top-level is a {type(data).__name__}, not an object -- "
        "wrap it like etf_data.json (T-0926-56), or add it to EXEMPT_FILES in "
        "pipeline/reference/output_date_keys.py if it genuinely carries no date"
    )
    present = RECOGNIZED_DATE_KEYS & data.keys()
    assert present, (
        f"{path.name}: no recognized date key at top level (looked for "
        f"{sorted(RECOGNIZED_DATE_KEYS)}). New files must set "
        "`as_of` (pipeline.reference.output_date_keys.CANONICAL_DATE_KEY); "
        "a genuinely dateless file goes in EXEMPT_FILES with a reason."
    )
