"""
Sends audio to the Whisper microservice and stores the transcript in MinIO.
"""
import json

import httpx

from app.config import get_settings
from app.core.storage import download_bytes, upload_bytes

settings = get_settings()


def transcribe_video(audio_storage_key: str, project_id: str, youtube_id: str) -> str:
    """
    Downloads audio from MinIO, sends bytes to Whisper service via multipart upload,
    stores the resulting transcript JSON in MinIO. Returns the transcript storage key.
    """
    audio_bytes = download_bytes(settings.minio_bucket_raw, audio_storage_key)

    with httpx.Client(timeout=3600) as client:
        resp = client.post(
            f"{settings.whisper_service_url}/transcribe",
            files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
        )
        resp.raise_for_status()
        transcript = resp.json()

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
