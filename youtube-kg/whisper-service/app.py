"""
Whisper transcription microservice.
Accepts an audio file path (local or MinIO-downloaded), returns timestamped transcript.
"""
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from faster_whisper import WhisperModel
from pydantic import BaseModel

app = FastAPI(title="Whisper Transcription Service")

MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")
DEVICE = os.getenv("DEVICE", "cpu")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _model


class TranscribeRequest(BaseModel):
    audio_path: str
    language: str | None = None  # None = auto-detect


@app.on_event("startup")
def warmup():
    get_model()


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_SIZE, "device": DEVICE}


@app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    if not Path(req.audio_path).exists():
        raise HTTPException(status_code=404, detail=f"Audio file not found: {req.audio_path}")

    model = get_model()
    t0 = time.time()

    segments_iter, info = model.transcribe(
        req.audio_path,
        language=req.language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segments = []
    for seg in segments_iter:
        words = []
        if seg.words:
            words = [{"word": w.word, "start": w.start, "end": w.end} for w in seg.words]
        segments.append({
            "id": seg.id,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": words,
        })

    processing_time = time.time() - t0

    return {
        "segments": segments,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration_seconds": info.duration,
        "processing_time_seconds": processing_time,
    }
