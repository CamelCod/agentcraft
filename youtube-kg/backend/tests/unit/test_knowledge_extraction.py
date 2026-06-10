"""Unit tests for knowledge extraction JSON parsing."""
import json
import pytest
from unittest.mock import patch

MOCK_EXTRACTION = json.dumps({
    "entities": [
        {"name": "iPhone 15 Pro", "entity_type": "product", "description": "Apple smartphone"},
    ],
    "claims": [
        {"text": "The iPhone 15 Pro features a titanium frame that is lighter than stainless steel", "entities_mentioned": ["iPhone 15 Pro"], "raw_confidence": 0.92},
        {"text": "Short", "entities_mentioned": [], "raw_confidence": 0.5},  # too short, should be filtered
    ],
    "relationships": [
        {"subject": "iPhone 15 Pro", "predicate": "uses", "object": "titanium frame"},
    ],
})


def test_extraction_parses_valid_json():
    from app.services.knowledge_extraction import extract_from_chunk

    with patch("app.services.knowledge_extraction.call_llm", return_value=MOCK_EXTRACTION):
        result = extract_from_chunk(
            text="The iPhone 15 Pro features a titanium frame.",
            video_title="iPhone 15 Pro Review",
            start_time=120.0,
            end_time=180.0,
            domain="Consumer Electronics",
        )

    assert len(result.entities) == 1
    assert result.entities[0].name == "iPhone 15 Pro"
    # Short claim filtered out
    assert all(len(c.text.split()) >= 5 for c in result.claims)
    assert len(result.relationships) == 1


def test_extraction_handles_invalid_json():
    from app.services.knowledge_extraction import extract_from_chunk, ExtractionResult

    with patch("app.services.knowledge_extraction.call_llm", return_value="not valid json at all"):
        result = extract_from_chunk("text", "title", 0, 10, "general")

    assert isinstance(result, ExtractionResult)
    assert result.entities == []
    assert result.claims == []


def test_extraction_confidence_range():
    from app.services.knowledge_extraction import extract_from_chunk

    with patch("app.services.knowledge_extraction.call_llm", return_value=MOCK_EXTRACTION):
        result = extract_from_chunk("text", "title", 0, 10, "Consumer Electronics")

    for claim in result.claims:
        assert 0.0 <= claim.raw_confidence <= 1.0
