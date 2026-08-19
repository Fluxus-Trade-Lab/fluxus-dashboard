"""Run ledger -- one JSON line per pipeline run, in the repo, forever.

GitHub Actions logs expire after 90 days; the questions that matter ("did
08-17 score 87.5 because of the data or the model?", "how often does Yahoo
throttle us?") need the run-level facts kept next to the data. Each run
appends a line to `data/history/run_ledger.jsonl`: which session it labelled,
when it started and finished, what every guard said, and what it wrote.

Append-only on purpose: a same-session re-run adds a second line rather than
replacing the first -- both happened. `audit_archives` does not key this
file by session, so duplicates are the record, not a violation.

    from pipeline.run_ledger import Ledger
    L = Ledger(session="2026-08-18")
    L.note("universe_quality", "degraded", fields=[...])
    L.write()
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

LEDGER = Path("data/history/run_ledger.jsonl")


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, timeout=5).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


class Ledger:
    def __init__(self, session: str, path: Path = LEDGER):
        self.path = path
        self.row: Dict[str, Any] = {
            "session": session,
            "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "finished_utc": None,
            "code_sha": _git_sha(),
            "trigger": os.environ.get("GITHUB_EVENT_NAME") or "local",
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "guards": {},
            "wrote": [],
            "errors": [],
        }

    def note(self, guard: str, status: Any, **detail: Any) -> None:
        """Record what one guard / stage concluded. Never raises."""
        try:
            self.row["guards"][guard] = {"status": status, **{k: _jsonable(v) for k, v in detail.items()}}
        except Exception:  # noqa: BLE001
            pass

    def wrote(self, name: str) -> None:
        self.row["wrote"].append(name)

    def error(self, where: str, msg: str) -> None:
        self.row["errors"].append({"where": where, "msg": str(msg)[:300]})

    def write(self) -> None:
        self.row["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(self.row, default=str) + "\n")
        except Exception:  # noqa: BLE001 -- the ledger must never cost a run
            pass


def _jsonable(v: Any) -> Any:
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in list(v.items())[:50]}
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in list(v)[:50]]
    return str(v)
