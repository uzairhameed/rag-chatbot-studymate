from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def extract_docx(file_path: str | Path) -> list[str]:
    """Extract paragraphs and table rows from a Word document."""
    document = Document(str(file_path))
    text_parts: list[str] = []

    # Preserve the order of paragraphs and tables as they appear in Word.
    for block in document.iter_inner_content():
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                text_parts.append(text)

        elif isinstance(block, Table):
            # Keep each row together so values remain associated.
            for row in block.rows:
                cells = [
                    cell.text.strip().replace("\n", " ")
                    for cell in row.cells
                ]
                if any(cells):
                    text_parts.append(" | ".join(cells))

    if not text_parts:
        raise ValueError("No extractable text found in the DOCX file")

    return text_parts
