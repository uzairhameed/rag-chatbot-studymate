from uuid import uuid4

from qdrant_client import QdrantClient, models
from pathlib import Path

from app.services.embedder import embed_texts, get_embedding_dimension

COLLECTION_NAME = "studymate_chunks"

# Store vectors on disk so they remain available after the app restarts.
QDRANT_STORAGE_PATH = Path(__file__).resolve().parents[2] / "qdrant_storage"
qdrant_client = QdrantClient(path=str(QDRANT_STORAGE_PATH))


def ensure_collection() -> None:
    """Create the chunk collection once, using the model's vector size."""
    if qdrant_client.collection_exists(COLLECTION_NAME):
        return

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=get_embedding_dimension(),
            distance=models.Distance.COSINE,
        ),
    )


def embed_and_store(
    chunks: list[str],
    *,
    room_id: int,
    file_id: int,
    filename: str,
    file_type: str,
) -> int:
    """Embed chunks and store them with source metadata in Qdrant."""
    if not chunks:
        return 0

    ensure_collection()
    vectors = embed_texts(chunks)

    points = [
        models.PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={
                "text": chunk,
                "room_id": room_id,
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": chunk_index,
            },
        )
        for chunk_index, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )
    return len(points)


def delete_file_chunks(file_id: int) -> None:
    """Remove a file's vectors if later processing fails."""
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        return

    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_id",
                        match=models.MatchValue(value=file_id),
                    )
                ]
            )
        ),
        wait=True,
    )

def get_file_chunks(file_id: int) -> list[models.Record]:
    """Return every stored chunk for a file, ordered by chunk index."""
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        return []

    all_points: list[models.Record] = []
    offset = None

    while True:
        points, next_offset = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="file_id",
                        match=models.MatchValue(value=file_id),
                    )
                ]
            ),
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(points)

        if next_offset is None:
            break
        offset = next_offset

    return sorted(
        all_points,
        key=lambda point: int((point.payload or {}).get("chunk_index", 0)),
    )

def search_chunks(
    query: str,
    *,
    room_id: int,
    limit: int = 5,
) -> list[models.ScoredPoint]:
    """Search Qdrant only within the specified room."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    ensure_collection()
    query_vector = embed_texts([query])[0]

    result = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="room_id",
                    match=models.MatchValue(value=room_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
    )
    return result.points