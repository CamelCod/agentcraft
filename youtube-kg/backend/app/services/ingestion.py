"""
Downloads audio from YouTube videos via yt-dlp and stores to MinIO.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

from app.config import get_settings
from app.core.storage import upload_file

settings = get_settings()


def download_audio(youtube_id: str, project_id: str) -> tuple[str, dict]:
    """
    Downloads audio as 128kbps mono MP3 and uploads to MinIO.
    Returns (storage_key, info_dict).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "%(id)s.%(ext)s")
        info_path = os.path.join(tmpdir, f"{youtube_id}.info.json")

        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "5",  # 128kbps
            "--postprocessor-args", "-ac 1",  # mono
            "--write-info-json",
            "--output", output_template,
            "--no-warnings",
            "--quiet",
            f"https://www.youtube.com/watch?v={youtube_id}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed for {youtube_id}: {result.stderr[:500]}")

        audio_file = Path(tmpdir) / f"{youtube_id}.mp3"
        if not audio_file.exists():
            # Try finding any mp3
            mp3_files = list(Path(tmpdir).glob("*.mp3"))
            if not mp3_files:
                raise FileNotFoundError(f"No MP3 output found for {youtube_id}")
            audio_file = mp3_files[0]

        storage_key = f"raw-audio/{project_id}/{youtube_id}/audio.mp3"
        upload_file(settings.minio_bucket_raw, storage_key, str(audio_file))

        info_dict = {}
        if Path(info_path).exists():
            with open(info_path) as f:
                info_dict = json.load(f)
            info_key = f"raw-audio/{project_id}/{youtube_id}/audio.info.json"
            upload_file(settings.minio_bucket_raw, info_key, info_path)

        return storage_key, info_dict
