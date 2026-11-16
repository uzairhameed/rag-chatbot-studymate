from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME="all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load one shared CPU model instance for the running app"""
    return SentenceTransformer(MODEL_NAME, device="cpu")

def get_embedding_dimension() -> int:
    """Return the vector size required when creating the Qdrant collection."""
    dimension = get_embedder().get_embedding_dimension()
    if dimension is None:
        raise RuntimeError("Could not determine embedding dimensions")
    return dimension

def embed_texts(texts:list[str]) -> list[list[float]]:
    """Convert text strings into normalized embedding vectors"""
    if not texts:
        return []

    vectors=get_embedder().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.tolist()