"""
Whisper transcription microservice.
Accepts an audio file upload, returns timestamped transcript.
"""
import os
import tempfile
import time

from fastapi import FastAPI, File, HTTPException, UploadFile

from faster_whisper import WhisperModel

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


@app.on_event("startup")
def warmup():
    get_model()


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_SIZE, "device": DEVICE}


@app.post("/transcribe")
def transcribe(
    file: UploadFile = File(...),
    language: str | None = None,
):
    model = get_model()
    t0 = time.time()

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        segments_iter, info = model.transcribe(
            tmp_path,
            language=language,
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
    finally:
        os.unlink(tmp_path)

    processing_time = time.time() - t0

    return {
        "segments": segments,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration_seconds": info.duration,
        "processing_time_seconds": processing_time,
    }
