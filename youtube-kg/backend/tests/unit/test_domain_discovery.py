"""Unit tests for domain discovery JSON parsing and confidence scores."""
import json
import pytest
from unittest.mock import patch


MOCK_LLM_RESPONSE = json.dumps([
    {
        "domain_name": "Personal Finance",
        "description": "Content about budgeting, investing, and debt management.",
        "confidence_score": 0.89,
        "representative_topics": ["budgeting", "index funds", "debt payoff"],
        "video_percentage": 60.0,
    },
    {
        "domain_name": "Productivity",
        "description": "Tips and tools for time management.",
        "confidence_score": 0.72,
        "representative_topics": ["task management", "focus"],
        "video_percentage": 40.0,
    },
])


def test_detect_domains_parses_llm_output():
    from app.services.domain_discovery import detect_domains

    videos = [
        {"title": "How I Paid Off $50,000 in Debt", "description": "", "tags": ["finance", "debt"]},
        {"title": "My Morning Productivity Routine", "description": "", "tags": ["productivity"]},
        {"title": "Index Funds vs ETFs Explained", "description": "", "tags": ["investing"]},
    ] * 5  # 15 videos

    with patch("app.services.domain_discovery.call_llm", return_value=MOCK_LLM_RESPONSE):
        results = detect_domains(videos)

    assert len(results) == 2
    assert results[0].domain_name == "Personal Finance"
    assert results[0].confidence_score == pytest.approx(0.89)
    assert results[1].confidence_score < results[0].confidence_score  # sorted desc


def test_detect_domains_handles_markdown_code_block():
    from app.services.domain_discovery import detect_domains

    md_wrapped = f"```json\n{MOCK_LLM_RESPONSE}\n```"
    videos = [{"title": "Test", "description": "", "tags": []}] * 3

    with patch("app.services.domain_discovery.call_llm", return_value=md_wrapped):
        results = detect_domains(videos)

    assert len(results) == 2


def test_detect_domains_empty_videos():
    from app.services.domain_discovery import detect_domains

    with patch("app.services.domain_discovery.call_llm", return_value=MOCK_LLM_RESPONSE):
        results = detect_domains([])

    assert isinstance(results, list)
