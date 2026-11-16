from pathlib import Path

from pptx import Presentation


def extract_pptx(file_path: str | Path) -> list[str]:
    """Extract slide text and table rows from a PowerPoint presentation."""
    presentation = Presentation(str(file_path))
    text_parts: list[str] = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        for shape in slide.shapes:
            # Read titles and text boxes.
            if shape.has_text_frame:
                text = shape.text.strip()
                if text:
                    text_parts.append(f"Slide {slide_number}: {text}")

            # Keep each table row together and preserve its slide number.
            if shape.has_table:
                for row in shape.table.rows:
                    cells = [
                        cell.text.strip().replace("\n", " ")
                        for cell in row.cells
                    ]
                    if any(cells):
                        text_parts.append(
                            f"Slide {slide_number} table: " + " | ".join(cells)
                        )

    if not text_parts:
        raise ValueError("No extractable text found in the PowerPoint file")

    return text_parts
