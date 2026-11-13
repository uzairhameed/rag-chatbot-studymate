from pathlib import Path

import pymupdf4llm

def extract_pdf(file_path: str | Path) -> list[str]:
    """Extract non-empty page text from a PDF as Markdown strings."""
    pages = pymupdf4llm.to_markdown(str(file_path), page_chunks=True)

    # Keep each page separate so later chunks retain page-level context.
    page_texts = [
        page["text"].strip()
        for page in pages
        if page.get("text", "").strip()
    ]

    if not page_texts:
        raise ValueError("No extractable text found in the PDF")

    return page_texts