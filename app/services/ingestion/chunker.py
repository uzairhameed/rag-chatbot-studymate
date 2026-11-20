def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks at word boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1")

    text = " ".join(text.split())
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(start + 1, end - overlap)
        while next_start < text_length and text[next_start] != " ":
            next_start += 1

        start = next_start + 1

    return chunks


def chunk_texts(
    text_parts: list[str],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """Combine extracted sections and split them into overlapping chunks."""
    combined_text = "\n\n".join(
        part.strip() for part in text_parts if part.strip()
    )
    return chunk_text(combined_text, chunk_size, overlap)