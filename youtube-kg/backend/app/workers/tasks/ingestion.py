"""
Task chain 2: Domain Approved → Download → Transcribe → Embed → Extract → Graph
"""
import uuid
from datetime import datetime, timezone

from celery import chain, chord, group
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.workers.celery_app import celery_app

settings = get_settings()


def _get_session() -> Session:
    from sqlalchemy import create_engine
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


def launch_ingestion_pipeline(project_id: str, video_ids: list[str], domain_map: dict[str, str]):
    """
    Called by the API after domain approval.
    Launches per-video chains and a final aggregation callback.
    """
    from app.workers.tasks.extraction import finalize_ingestion

    per_video_chains = [
        chain(
            # None is the placeholder prev_result for the chain-head task;
            # Celery won't inject one since there's no preceding task.
            download_audio_task.s(None, video_id, project_id),
            transcribe_task.s(video_id, project_id),
            embed_task.s(video_id, project_id),
            extract_task.s(video_id, project_id, domain_map.get(video_id, "general")),
            graph_write_task.s(video_id, project_id),
        )
        for video_id in video_ids
    ]

    if per_video_chains:
        chord(group(*per_video_chains), finalize_ingestion.s(project_id)).delay()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.download_audio",
    queue="ingestion",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def download_audio_task(self, prev_result, video_id: str, project_id: str):
    from app.models import Video
    from app.models.video import VideoStatus
    from app.services.ingestion import download_audio

    with _get_session() as session:
        video = session.get(Video, uuid.UUID(video_id))
        if not video:
            raise ValueError(f"Video {video_id} not found")

        video.status = VideoStatus.downloading
        session.commit()

        try:
            storage_key, _ = download_audio(video.youtube_id, project_id)
            video.audio_storage_key = storage_key
            video.status = VideoStatus.transcribing
            session.commit()
        except Exception as exc:
            video.status = VideoStatus.error
            video.error_message = str(exc)[:500]
            session.commit()
            raise

    return video_id


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.transcribe",
    queue="default",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def transcribe_task(self, video_id: str, _, project_id: str):
    from app.models import Video
    from app.models.video import VideoStatus
    from app.services.transcription import transcribe_video

    with _get_session() as session:
        video = session.get(Video, uuid.UUID(video_id))
        if not video or not video.audio_storage_key:
            raise ValueError(f"Video {video_id} has no audio yet")

        try:
            transcript_key = transcribe_video(
                video.audio_storage_key, project_id, video.youtube_id
            )
            video.transcript_storage_key = transcript_key
            video.status = VideoStatus.embedding
            session.commit()
        except Exception as exc:
            video.status = VideoStatus.error
            video.error_message = str(exc)[:500]
            session.commit()
            raise

    return video_id


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.embed",
    queue="default",
    max_retries=2,
    autoretry_for=(Exception,),
)
def embed_task(self, video_id: str, _, project_id: str):
    from app.models import Video
    from app.models.video import VideoStatus
    from app.services.memory import embed_transcript
    from app.services.transcription import load_transcript

    with _get_session() as session:
        video = session.get(Video, uuid.UUID(video_id))
        if not video:
            raise ValueError(f"Video {video_id} not found")

        try:
            transcript = load_transcript(project_id, video.youtube_id)
            detected_language = transcript.get("language", "auto")

            embed_transcript(
                transcript=transcript,
                video_id=str(video.id),
                project_id=project_id,
                youtube_id=video.youtube_id,
                domain=video.assigned_domains[0] if video.assigned_domains else "general",
                language=detected_language,
            )

            video.detected_language = detected_language
            video.status = VideoStatus.extracting
            session.commit()
        except Exception as exc:
            video.status = VideoStatus.error
            video.error_message = str(exc)[:500]
            session.commit()
            raise

    return video_id


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.extract",
    queue="extraction",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def extract_task(self, video_id: str, _, project_id: str, domain: str):
    from app.models import Video
    from app.models.video import VideoStatus
    from app.services.knowledge_extraction import extract_from_chunk
    from app.services.transcription import load_transcript

    with _get_session() as session:
        video = session.get(Video, uuid.UUID(video_id))
        if not video:
            raise ValueError(f"Video {video_id} not found")

        try:
            transcript = load_transcript(project_id, video.youtube_id)
            segments = transcript.get("segments", [])
            # Group segments into ~512-word chunks
            chunk_size = 512
            current_words = []
            current_start = 0.0
            current_end = 0.0
            results = []

            for seg in segments:
                words = seg["text"].split()
                if not current_words:
                    current_start = seg["start"]
                current_words.extend(words)
                current_end = seg["end"]

                if len(current_words) >= chunk_size:
                    text = " ".join(current_words)
                    result = extract_from_chunk(text, video.title, current_start, current_end, domain)
                    results.append((text, current_start, current_end, result))
                    current_words = current_words[-64:]
                    current_start = current_end

            if current_words:
                text = " ".join(current_words)
                result = extract_from_chunk(text, video.title, current_start, current_end, domain)
                results.append((text, current_start, current_end, result))

            # Store extraction results as metadata for graph_write_task
            video.metadata_json = {
                "extraction_results": [
                    {
                        "text": t,
                        "start_time": s,
                        "end_time": e,
                        "entities": [{"name": en.name, "type": en.entity_type, "desc": en.description} for en in r.entities],
                        "claims": [{"text": c.text, "entities": c.entities_mentioned, "confidence": c.raw_confidence} for c in r.claims],
                        "relationships": [{"s": rel.subject, "p": rel.predicate, "o": rel.object} for rel in r.relationships],
                    }
                    for t, s, e, r in results
                ]
            }
            video.status = VideoStatus.completed
            session.commit()
        except Exception as exc:
            video.status = VideoStatus.error
            video.error_message = str(exc)[:500]
            session.commit()
            raise

    return video_id


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingestion.graph_write",
    queue="default",
    max_retries=3,
    autoretry_for=(Exception,),
)
def graph_write_task(self, video_id: str, _, project_id: str):
    import uuid as _uuid
    from app.models import Video
    from app.services import graph_service as graph
    from app.services.memory import embed_claim, COLLECTION_CLAIMS, get_qdrant

    with _get_session() as session:
        video = session.get(Video, _uuid.UUID(video_id))
        if not video or not video.metadata_json:
            return video_id

        extraction_results = video.metadata_json.get("extraction_results", [])
        graph.upsert_video_node(
            youtube_id=video.youtube_id,
            title=video.title,
            project_id=project_id,
            published_at=str(video.published_at) if video.published_at else None,
        )

        for chunk_data in extraction_results:
            chunk_id = str(_uuid.uuid4())
            graph.upsert_chunk_node(
                chunk_id=chunk_id,
                text=chunk_data["text"][:1000],
                start_time=chunk_data["start_time"],
                end_time=chunk_data["end_time"],
                youtube_id=video.youtube_id,
                video_id=str(video.id),
            )

            # Write entities
            for ent in chunk_data.get("entities", []):
                if ent.get("name"):
                    concept_id = graph.upsert_concept_node(
                        name=ent["name"],
                        domain=video.assigned_domains[0] if video.assigned_domains else "general",
                        project_id=project_id,
                        description=ent.get("desc", ""),
                    )

            # Write claims
            for claim_data in chunk_data.get("claims", []):
                if not claim_data.get("text"):
                    continue
                claim_id = str(_uuid.uuid4())
                domain = video.assigned_domains[0] if video.assigned_domains else "general"

                graph.upsert_claim_node(
                    claim_id=claim_id,
                    text=claim_data["text"],
                    project_id=project_id,
                    domain=domain,
                    raw_confidence=claim_data.get("confidence", 0.5),
                )
                graph.link_claim_to_chunk(
                    claim_id=claim_id,
                    chunk_id=chunk_id,
                    youtube_id=video.youtube_id,
                    video_id=str(video.id),
                    start_time=chunk_data["start_time"],
                    end_time=chunk_data["end_time"],
                    transcript_excerpt=chunk_data["text"][:500],
                    raw_confidence=claim_data.get("confidence", 0.5),
                )
                graph.link_claim_to_video(claim_id, video.youtube_id)

                # Embed claim for verification
                try:
                    embed_claim(claim_id, claim_data["text"], project_id, domain)
                except Exception:
                    pass

    return video_id
