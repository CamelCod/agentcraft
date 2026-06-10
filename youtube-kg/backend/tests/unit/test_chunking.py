"""Unit tests for transcript chunking logic."""
from app.services.memory import _split_transcript_into_chunks


def _make_transcript(segment_count: int, words_per_segment: int = 100) -> dict:
    word = "word"
    segments = [
        {
            "start": i * 10.0,
            "end": (i + 1) * 10.0,
            "text": " ".join([word] * words_per_segment),
        }
        for i in range(segment_count)
    ]
    return {"segments": segments}


def test_chunks_produced_for_long_transcript():
    transcript = _make_transcript(segment_count=10, words_per_segment=100)
    chunks = _split_transcript_into_chunks(transcript)
    assert len(chunks) > 0


def test_empty_transcript_returns_empty():
    chunks = _split_transcript_into_chunks({"segments": []})
    assert chunks == []


def test_chunk_timestamps_are_monotone():
    transcript = _make_transcript(segment_count=20, words_per_segment=50)
    chunks = _split_transcript_into_chunks(transcript)
    for c in chunks:
        assert c["end_time"] >= c["start_time"]


def test_chunk_word_count_near_target():
    """Each non-final chunk should be near CHUNK_SIZE (512) words."""
    transcript = _make_transcript(segment_count=30, words_per_segment=100)
    chunks = _split_transcript_into_chunks(transcript)
    # All but the last chunk should be around 512 words (may vary due to overlap)
    for c in chunks[:-1]:
        assert c["word_count"] >= 400  # allow some tolerance


def test_arabic_text_not_corrupted():
    arabic_text = "هذا نص باللغة العربية لاختبار التقطيع"
    transcript = {"segments": [{"start": 0, "end": 5, "text": arabic_text}]}
    chunks = _split_transcript_into_chunks(transcript)
    assert len(chunks) == 1
    assert arabic_text in chunks[0]["text"]
