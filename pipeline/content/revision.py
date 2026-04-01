"""Revision tracking for the content pipeline.

Stores draft→final pairs and loads the most recent examples
for few-shot learning in the prompt.
"""
from pathlib import Path

MAX_EXAMPLES = 3  # Number of revision pairs to include in prompts


def save_final(threads_dir: Path, date_str: str, final_text: str) -> Path:
    """Save the revised final version alongside the draft."""
    date_dir = threads_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    final_path = date_dir / "final.txt"
    final_path.write_text(final_text)
    return final_path


def load_style_examples(threads_dir: Path, max_examples: int = MAX_EXAMPLES) -> str:
    """Load recent draft→final pairs as few-shot examples for the prompt.

    Scans threads_dir for date folders that have both draft.txt and final.txt.
    Returns formatted text to inject into the system prompt.
    """
    if not threads_dir.exists():
        return ""

    pairs = []
    # Sort by date (folder name), most recent first
    for date_dir in sorted(threads_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        draft = date_dir / "draft.txt"
        final = date_dir / "final.txt"
        if draft.exists() and final.exists():
            draft_text = draft.read_text().strip()
            final_text = final.read_text().strip()
            # Only include if they're actually different
            if draft_text != final_text:
                pairs.append({
                    "date": date_dir.name,
                    "draft": draft_text,
                    "final": final_text,
                })
        if len(pairs) >= max_examples:
            break

    if not pairs:
        return ""

    sections = []
    for p in pairs:
        sections.append(
            f"--- REVISION EXAMPLE ({p['date']}) ---\n"
            f"DRAFT:\n{p['draft']}\n\n"
            f"REVISED BY AUTHOR:\n{p['final']}\n"
            f"--- END EXAMPLE ---"
        )

    header = (
        "STYLE LEARNING — The author has revised previous drafts. "
        "Study the differences between DRAFT and REVISED versions below. "
        "Apply the same patterns to new content: tone adjustments, "
        "structural preferences, level of detail, what gets cut, what gets expanded.\n\n"
    )

    return header + "\n\n".join(sections)
