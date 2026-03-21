"""Audio -> Daily brief pipeline.

Usage:
    python -m pipeline.content.audio_to_brief --file premarket.mp3
    python -m pipeline.content.audio_to_brief --file talk.m4a --append

Environment variables required:
    OPENAI_API_KEY, ANTHROPIC_API_KEY
"""
import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

from pipeline.content.processor import process_to_brief

BRIEFS_PATH = Path("data/output/briefs.json")
MAX_FILE_SIZE_MB = 25


def transcribe_audio(file_path: str, api_key: str | None = None) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"Audio file is {size_mb:.1f}MB — exceeds Whisper's {MAX_FILE_SIZE_MB}MB limit. "
            f"Split the file first: ffmpeg -i {file_path} -t 1200 -c copy part1.mp3"
        )

    client = OpenAI(api_key=api_key)

    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
        )

    return transcript


def main():
    parser = argparse.ArgumentParser(description="Convert pre-market talk audio into a daily brief")
    parser.add_argument("--file", type=str, required=True, help="Path to audio file (.mp3, .m4a, .wav)")
    parser.add_argument("--append", action="store_true", help=f"Append the new brief to {BRIEFS_PATH}")
    args = parser.parse_args()

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("Error: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Transcribing {args.file}...")
    transcript = transcribe_audio(args.file, api_key=openai_key)
    print(f"Transcript: {len(transcript)} characters")

    print("Generating daily brief with Claude...")
    brief = process_to_brief(transcript)

    print("\n" + json.dumps(brief, indent=2))

    if args.append:
        briefs = []
        if BRIEFS_PATH.exists():
            briefs = json.loads(BRIEFS_PATH.read_text())
        briefs.insert(0, brief)
        briefs = briefs[:30]
        BRIEFS_PATH.write_text(json.dumps(briefs, indent=2) + "\n")
        print(f"\nAppended to {BRIEFS_PATH} ({len(briefs)} total briefs)")


if __name__ == "__main__":
    main()
