def chunk_text(
        text: str,
        chunk_size: int=500,
        overlap: int =50,
) -> list[str]:
    """Split text into character-sizer pieces wiht shared overlap"""

    if chunk_size <=0:
        raise ValueError ("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError ("overlap must be between zero and chunk_size -1")

    # Normalize whitespace but retain readable seperation between sections.

    text ="".join(text.split())
    if not text:
        return []

    chunks: list[str]= []
    start=0

    while start < len(text):
        end= min(start + chunk_size, len(text))
        chunk= text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end ==len(text):
            break

        # Start the next chunk before the previous one ended.

        start= end - overlap

    return chunks

def chunk_texts(
    text_parts: list[str],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Combine extracted sections and split them into RAG chunks."""
    combined_text = "\n\n".join(part.strip() for part in text_parts if part.strip())
    return chunk_text(combined_text, chunk_size, overlap)