"""T-0920-55 -- data/output must never be copied back into the Vercel build.

2026-09-20 incident: buildCommand did `cp -r data/output frontend/public/data/...`,
so every production deployment stored a fresh ~102 MB copy of data/output (it
changes daily), blowing past the 10 GB Deployment Storage cap in under a week.
The fix serves /data/output/* via a server-side rewrite to raw.githubusercontent.com
(the repo is public, so the pipeline's normal `git push` to main is already the
publish step -- no new deploy step needed) and drops the cp from buildCommand.

This guards against someone re-adding the copy the next time data/output needs
to reach the frontend, and against the rewrite being deleted/misdirected.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VERCEL_JSON = json.loads((REPO / "vercel.json").read_text())


def test_build_command_does_not_copy_data_output():
    build = VERCEL_JSON.get("buildCommand", "")
    assert "data/output" not in build, (
        f"buildCommand copies data/output back into the deploy artifact: {build!r}"
    )


def test_data_output_requests_are_rewritten_to_an_external_host():
    rewrites = VERCEL_JSON.get("rewrites", [])
    match = next((r for r in rewrites if r.get("source", "").startswith("/data/output/")), None)
    assert match is not None, "no rewrite rule for /data/output/* -- it would 404 or hit the SPA fallback"
    dest = match["destination"]
    assert re.match(r"^https://", dest), f"/data/output/* rewrite must proxy to an external URL, got {dest!r}"
    assert dest.endswith("/data/output/$1"), f"rewrite destination path must mirror the request: {dest!r}"


def test_data_output_rewrite_is_ordered_before_the_generic_data_rewrite():
    """Vercel takes the first matching rule; a generic /data/(.*) rule before the
    specific /data/output/(.*) one would swallow output requests and serve them
    as (missing) local static files instead of proxying them."""
    rewrites = VERCEL_JSON.get("rewrites", [])
    sources = [r.get("source", "") for r in rewrites]
    output_idx = next((i for i, s in enumerate(sources) if s.startswith("/data/output/")), None)
    generic_idx = next((i for i, s in enumerate(sources) if s == "/data/(.*)"), None)
    assert output_idx is not None
    if generic_idx is not None:
        assert output_idx < generic_idx
