"""
Analyzes video metadata (titles, descriptions, tags) to detect topic clusters
and produce ranked domain suggestions — without downloading any content.

Uses LLM-based clustering on a summarized metadata corpus.
"""
import json
from dataclasses import dataclass

from app.config import get_settings
from app.services.llm import call_llm

settings = get_settings()

_DOMAIN_DISCOVERY_PROMPT = """You are a knowledge domain analyst. Given a list of YouTube video titles, descriptions, and tags from a single creator, identify the main knowledge domains they teach or discuss.

For each domain:
- Give it a clear, human-readable name (e.g. "Personal Finance", "Machine Learning", "Arabic Grammar")
- Write a 1-2 sentence description of what the creator covers in that domain
- Estimate a confidence score (0.0–1.0) based on how consistently the creator covers it
- List 3-5 representative topics/subtopics
- Estimate what percentage of the video catalog belongs to this domain

Return a JSON array with this exact schema:
[
  {
    "domain_name": "string",
    "description": "string",
    "confidence_score": float,
    "representative_topics": ["string"],
    "video_percentage": float
  }
]

Sort by confidence_score descending. Return between 2 and 8 domains.

Video metadata corpus (titles + tags sample):
{corpus}
"""


@dataclass
class DomainSuggestion:
    domain_name: str
    description: str
    confidence_score: float
    representative_topics: list[str]
    video_percentage: float
    video_count: int


def detect_domains(videos: list[dict], max_sample: int = 200) -> list[DomainSuggestion]:
    """
    videos: list of dicts with keys: title, description, tags
    Returns ranked domain suggestions.
    """
    sampled = videos[:max_sample]
    corpus_lines = []
    for v in sampled:
        tags = ", ".join(v.get("tags", [])[:10])
        line = f"- {v['title']}"
        if tags:
            line += f" [tags: {tags}]"
        corpus_lines.append(line)

    corpus = "\n".join(corpus_lines)
    prompt = _DOMAIN_DISCOVERY_PROMPT.format(corpus=corpus)

    response_text = call_llm(
        prompt=prompt,
        model=settings.llm_model,
        temperature=0.2,
        max_tokens=2000,
    )

    try:
        raw = json.loads(response_text)
    except json.JSONDecodeError:
        # Extract JSON from markdown code block if present
        import re
        m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", response_text)
        if m:
            raw = json.loads(m.group(1))
        else:
            raise ValueError(f"LLM returned non-JSON response: {response_text[:200]}")

    total_videos = len(videos)
    suggestions = []
    for d in raw:
        video_count = round(d.get("video_percentage", 0) * total_videos / 100)
        suggestions.append(DomainSuggestion(
            domain_name=d["domain_name"],
            description=d.get("description", ""),
            confidence_score=float(d["confidence_score"]),
            representative_topics=d.get("representative_topics", []),
            video_percentage=float(d.get("video_percentage", 0)),
            video_count=max(1, video_count),
        ))

    return sorted(suggestions, key=lambda x: x.confidence_score, reverse=True)
