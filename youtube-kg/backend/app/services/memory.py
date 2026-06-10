"""
Chunks transcripts and stores embeddings in Qdrant.
Uses paraphrase-multilingual-MiniLM-L12-v2 (384-dim, supports Arabic + 50 langs).
"""
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()

COLLECTION_TRANSCRIPTS = "transcripts"
COLLECTION_CONCEPTS = "concepts"
COLLECTION_CLAIMS = "claims"
CHUNK_SIZE = 512      # target tokens
CHUNK_OVERLAP = 64


@lru_cache
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


@lru_cache
def get_qdrant() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collections():
    client = get_qdrant()
    dim = settings.embedding_dim
    for name in [COLLECTION_TRANSCRIPTS, COLLECTION_CONCEPTS, COLLECTION_CLAIMS]:
        existing = [c.name for c in client.get_collections().collections]
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )


def _split_transcript_into_chunks(transcript: dict) -> list[dict]:
    """
    Splits Whisper segments into overlapping chunks by approximate word count.
    Each chunk: {text, start_time, end_time, word_count}
    """
    segments = transcript.get("segments", [])
    chunks: list[dict] = []
    current_words: list[str] = []
    current_start: float = 0.0
    current_end: float = 0.0
    word_count = 0

    for seg in segments:
        seg_words = seg["text"].split()
        if not current_words:
            current_start = seg["start"]

        current_words.extend(seg_words)
        current_end = seg["end"]
        word_count += len(seg_words)

        if word_count >= CHUNK_SIZE:
            chunks.append({
                "text": " ".join(current_words),
                "start_time": current_start,
                "end_time": current_end,
                "word_count": word_count,
            })
            # Overlap: keep last CHUNK_OVERLAP words
            overlap_words = current_words[-CHUNK_OVERLAP:]
            current_words = overlap_words
            current_start = current_end
            word_count = len(overlap_words)

    if current_words:
        chunks.append({
            "text": " ".join(current_words),
            "start_time": current_start,
            "end_time": current_end,
            "word_count": word_count,
        })

    return chunks


def embed_transcript(
    transcript: dict,
    video_id: str,
    project_id: str,
    youtube_id: str,
    domain: str,
    language: str = "auto",
) -> list[str]:
    """
    Chunks transcript, generates embeddings, upserts into Qdrant.
    Returns list of chunk_ids.
    """
    ensure_collections()
    chunks = _split_transcript_into_chunks(transcript)
    if not chunks:
        return []

    texts = [c["text"] for c in chunks]
    embedder = get_embedder()
    vectors = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    chunk_ids: list[str] = []
    points: list[PointStruct] = []

    for chunk, vector in zip(chunks, vectors):
        chunk_id = str(uuid.uuid4())
        chunk_ids.append(chunk_id)
        points.append(PointStruct(
            id=chunk_id,
            vector=vector.tolist(),
            payload={
                "chunk_id": chunk_id,
                "video_id": video_id,
                "project_id": project_id,
                "youtube_id": youtube_id,
                "domain": domain,
                "language": language,
                "text": chunk["text"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "word_count": chunk["word_count"],
            },
        ))

    get_qdrant().upsert(collection_name=COLLECTION_TRANSCRIPTS, points=points)
    return chunk_ids


def embed_claim(claim_id: str, claim_text: str, project_id: str, domain: str, metadata: dict | None = None) -> None:
    ensure_collections()
    vector = get_embedder().encode([claim_text], normalize_embeddings=True)[0]
    payload = {
        "claim_id": claim_id,
        "project_id": project_id,
        "domain": domain,
        "text": claim_text,
        **(metadata or {}),
    }
    get_qdrant().upsert(
        collection_name=COLLECTION_CLAIMS,
        points=[PointStruct(id=claim_id, vector=vector.tolist(), payload=payload)],
    )


def search_similar_claims(claim_id: str, project_id: str, limit: int = 50, score_threshold: float = 0.75) -> list[dict]:
    """Returns claims similar to the given claim_id within the same project."""
    client = get_qdrant()
    # Fetch the claim's vector
    results = client.retrieve(collection_name=COLLECTION_CLAIMS, ids=[claim_id], with_vectors=True)
    if not results:
        return []
    vector = results[0].vector

    hits = client.search(
        collection_name=COLLECTION_CLAIMS,
        query_vector=vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter={
            "must": [{"key": "project_id", "match": {"value": project_id}}]
        },
        with_payload=True,
    )
    return [
        {"claim_id": h.payload["claim_id"], "score": h.score, "text": h.payload["text"]}
        for h in hits
        if h.payload["claim_id"] != claim_id
    ]
