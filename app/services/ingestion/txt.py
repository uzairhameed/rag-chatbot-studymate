from pathlib import Path


def extract_txt(file_path: str | Path) -> list[str]:
    """Read a plain-text file and return its content as one text section."""
    text = Path(file_path).read_text(encoding="utf-8-sig").strip()

    if not text:
        raise ValueError("The text file is empty")

    return [text]
