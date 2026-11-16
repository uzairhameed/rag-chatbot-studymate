from pathlib import Path


def extract_markdown(file_path: str | Path) -> list[str]:
    """Read Markdown while preserving headings, lists, and other formatting."""
    text = Path(file_path).read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError("The Markdown file is empty")

    return [text]
