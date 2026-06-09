"""
Sends audio to the Whisper microservice and stores the transcript in MinIO.
"""
import json
import tempfile

import httpx

from app.config import get_settings
from app.core.storage import download_bytes, upload_bytes

settings = get_settings()


def transcribe_video(audio_storage_key: str, project_id: str, youtube_id: str) -> str:
    """
    Downloads audio from MinIO, sends to Whisper service, stores transcript.
    Returns the transcript storage key.
    """
    audio_bytes = download_bytes(settings.minio_bucket_raw, audio_storage_key)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with httpx.Client(timeout=3600) as client:
            resp = client.post(
                f"{settings.whisper_service_url}/transcribe",
                json={"audio_path": tmp_path},
            )
            resp.raise_for_status()
            transcript = resp.json()
    finally:
        import os
        os.unlink(tmp_path)

    transcript_bytes = json.dumps(transcript, ensure_ascii=False).encode("utf-8")
    storage_key = f"transcripts/{project_id}/{youtube_id}/transcript.json"
    upload_bytes(
        settings.minio_bucket_transcripts,
        storage_key,
        transcript_bytes,
        content_type="application/json",
    )

    return storage_key


def load_transcript(project_id: str, youtube_id: str) -> dict:
    """Loads transcript JSON from MinIO."""
    key = f"transcripts/{project_id}/{youtube_id}/transcript.json"
    data = download_bytes(settings.minio_bucket_transcripts, key)
    return json.loads(data)
