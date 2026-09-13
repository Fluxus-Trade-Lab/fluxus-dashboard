#!/usr/bin/env python3
"""Fetch the daily video transcript for one session → transcript.md (local only).

Usage:
    python3 -m pipeline.content.recap.fetch_transcript --date 2026-09-11 [--sample]
    python3 -m pipeline.content.recap.fetch_transcript --date 2026-09-11 --video-id 0_YeDfX1atU

Which video is "the daily for session T" (rule, tested in test_recap_transcript.py):
  1. List the channel's newest uploads (flat playlist, newest first).
  2. Drop anything whose title marks it as not-a-daily: "Your Money Podcast",
     "Weekend Review" / "Weekend" — those are weekly shows, not the session recap.
  3. Of what remains, the daily for T is the one whose upload_date == T
     (the recap is published the evening of the session, US time).
  4. Zero matches → no daily that day (holiday / skipped) → exit 3, no guess.
     Several matches → the longest one (shorts/clips are short) and say so.
The flat listing carries no upload_date, so step 3 asks yt-dlp per candidate,
newest first, and stops once it has walked past T.

Output never enters git: it lands in pack_<date>/ under RECAP_ROOT.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Optional

from pipeline.content.recap import pack_dir

CHANNEL_URL = "https://www.youtube.com/channel/UCV27KlSTS2zAidGEbu0HcZA/videos"

NOT_DAILY = re.compile(r"your\s+money\s+podcast|weekend", re.I)

_TAG = re.compile(r"<[^>]+>")
_CUE_TIME = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+-->")


# ---------------------------------------------------------------- selection
def is_daily_title(title: str) -> bool:
    return not NOT_DAILY.search(title or "")


def pick_daily(entries: Iterable[dict], date_iso: str,
               upload_date_of: Callable[[str], Optional[str]]) -> Optional[dict]:
    """entries: newest-first dicts with id/title/duration (flat playlist).
    upload_date_of(video_id) -> 'YYYYMMDD' (injected so tests need no network).
    Returns the chosen entry (with 'upload_date' filled) or None."""
    want = date_iso.replace("-", "")
    hits: list[dict] = []
    for e in entries:
        if not is_daily_title(e.get("title", "")):
            continue
        ud = e.get("upload_date") or upload_date_of(e["id"])
        if not ud:
            continue
        if ud == want:
            hits.append({**e, "upload_date": ud})
        elif ud < want:
            break  # newest-first: walked past T
    if not hits:
        return None
    return max(hits, key=lambda e: e.get("duration") or 0)


# ---------------------------------------------------------------- VTT dedupe
def dedupe_vtt(vtt: str, para_seconds: int = 60) -> list[tuple[int, str]]:
    """YouTube auto-subs roll: each cue repeats the previous line and adds one,
    plus 10ms 'transition' cues that repeat it again. Keep each distinct line
    once, in order; group into paragraphs of ~para_seconds.
    Returns [(start_seconds, paragraph_text)]."""
    lines_out: list[tuple[int, str]] = []
    last = None
    cue_start = 0
    for raw in vtt.splitlines():
        m = _CUE_TIME.match(raw)
        if m:
            h, mi, s, _ms = map(int, m.groups())
            cue_start = h * 3600 + mi * 60 + s
            continue
        if not raw.strip() or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        text = _TAG.sub("", raw).strip()
        text = re.sub(r"\s+", " ", text)
        if not text or text == last:
            continue
        # a rolling cue's first line equals the line we already kept two cues ago
        if lines_out and text == lines_out[-1][1]:
            continue
        lines_out.append((cue_start, text))
        last = text
    paras: list[tuple[int, str]] = []
    buf: list[str] = []
    start = None
    for t, text in lines_out:
        if start is None:
            start = t
        if t - start >= para_seconds and buf:
            paras.append((start, " ".join(buf)))
            buf, start = [], t
        buf.append(text)
    if buf:
        paras.append((start or 0, " ".join(buf)))
    return paras


def to_markdown(paras: list[tuple[int, str]], meta: dict) -> str:
    head = [f"# Transcript · {meta.get('date')}",
            "",
            f"- video: {meta.get('id')} · upload {meta.get('upload_date')} · {meta.get('duration')}s",
            f"- title: {meta.get('title')}",
            "- source: YouTube auto-captions, rolling duplicates removed (private, not for git)",
            ""]
    body = [f"**[{t // 60:02d}:{t % 60:02d}]** {p}\n" for t, p in paras]
    return "\n".join(head) + "\n".join(body)


# ---------------------------------------------------------------- yt-dlp I/O
def _ytdlp(args: list[str], timeout: int = 180) -> str:
    r = subprocess.run(["yt-dlp", *args], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {r.stderr.strip()[-300:]}")
    return r.stdout


def list_channel(n: int = 15) -> list[dict]:
    d = json.loads(_ytdlp(["--flat-playlist", "--playlist-end", str(n), "-J", CHANNEL_URL]))
    return [{"id": e["id"], "title": e.get("title", ""), "duration": e.get("duration")}
            for e in d.get("entries", [])]


def upload_date_of(video_id: str) -> Optional[str]:
    out = _ytdlp(["--skip-download", "--print", "upload_date",
                  f"https://www.youtube.com/watch?v={video_id}"]).strip()
    return out or None


def download_vtt(video_id: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    _ytdlp(["--skip-download", "--write-auto-subs", "--sub-langs", "en",
            "--sub-format", "vtt", "-P", str(dest), "-o", f"raw_{video_id}",
            f"https://www.youtube.com/watch?v={video_id}"])
    hits = sorted(dest.glob(f"raw_{video_id}*.vtt"))
    if not hits:
        raise RuntimeError("no English auto-captions downloaded")
    return hits[0]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--video-id", help="skip channel selection")
    ap.add_argument("--sample", action="store_true", help="write under samples/")
    a = ap.parse_args(argv)
    t0 = time.time()
    out_dir = pack_dir(a.date, a.sample)
    if a.video_id:
        meta = {"id": a.video_id, "title": "", "duration": None,
                "upload_date": upload_date_of(a.video_id)}
    else:
        meta = pick_daily(list_channel(), a.date, upload_date_of)
        if meta is None:
            print(f"[no-daily] no daily upload for {a.date}", file=sys.stderr)
            return 3
    meta["date"] = a.date
    vtt = download_vtt(meta["id"], out_dir)
    paras = dedupe_vtt(vtt.read_text(encoding="utf-8"))
    md = out_dir / "transcript.md"
    md.write_text(to_markdown(paras, meta), encoding="utf-8")
    (out_dir / "transcript_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    words = sum(len(p.split()) for _, p in paras)
    print(f"ok {md} · {len(paras)} paragraphs · {words} words · {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
