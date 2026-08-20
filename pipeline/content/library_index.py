"""data/output/library/index.json -- the Library's table of contents.

Why: `<page>_<topic>.json` is a CONVENTION, and a browser cannot list a
directory. Without an index the frontend reads a list compiled into the bundle
(`useLibrary.js` COMPILED_IN), so every new article needs a frontend deploy
before it is visible -- and until that deploy the page says "1 篇" while two
exist. DATA_CONTRACTS §七 (2026-08-20).

Grouping comes from each article's own `page` field, not from its filename
prefix: `portfolio-management` contains a hyphen and an underscore-prefix parse
cannot tell `portfolio-management_x.json` from a page called `portfolio`. A file
whose `page` is missing or unknown is reported, never guessed into a bucket.

The values are `.json` filenames because that is what the frontend fetches and
parses (the same-named `.md` is a human draft nothing renders). The §七 ask was
written with `.md` in its example; the shipped loader disagrees, and the loader
is what runs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

LIBRARY_DIR = Path("data/output/library")
INDEX = LIBRARY_DIR / "index.json"

# The five Library pages the frontend routes to. An empty list is meaningful:
# it says "measured, nothing here", which is not the same as a missing key.
PAGES: Tuple[str, ...] = (
    "offense", "defense", "psychology", "portfolio-management", "news",
)


def build(library_dir: Path = LIBRARY_DIR) -> Tuple[Dict[str, List[str]], List[str]]:
    """Return (index, problems). Every page key is always present."""
    index: Dict[str, List[str]] = {p: [] for p in PAGES}
    problems: List[str] = []

    for path in sorted(library_dir.glob("*.json")):
        if path.name == INDEX.name:
            continue
        try:
            doc = json.loads(path.read_text())
        except ValueError as exc:
            problems.append(f"{path.name}: unparsable ({exc})")
            continue
        if not isinstance(doc, dict):
            problems.append(f"{path.name}: not an object")
            continue
        page = doc.get("page")
        if page not in index:
            problems.append(f"{path.name}: page={page!r} is not one of {list(PAGES)}")
            continue
        index[page].append(path.name)

    return index, problems


def write(library_dir: Path = LIBRARY_DIR) -> Dict[str, List[str]]:
    """Build and write index.json; log anything that could not be placed."""
    # mkdir before write: a checkout with no articles yet has no library dir,
    # and a stage that throws there would be swallowed into a log line by the
    # orchestrator's try/except. The empty index is the correct answer -- it
    # says "five pages, nothing in them", which the compiled-in fallback
    # cannot say.
    library_dir.mkdir(parents=True, exist_ok=True)
    index, problems = build(library_dir)
    for p in problems:
        logger.warning("library index: %s", p)
    (library_dir / INDEX.name).write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return index


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    idx = write()
    print(json.dumps({k: len(v) for k, v in idx.items()}, indent=2))


if __name__ == "__main__":
    main()
