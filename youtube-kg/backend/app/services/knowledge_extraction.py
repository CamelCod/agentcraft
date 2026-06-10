"""
Extracts entities, claims, and relationships from transcript chunks using
structured LLM output. Uses domain-appropriate prompt templates.
"""
import json
import re
from dataclasses import dataclass, field

from app.config import get_settings
from app.services.llm import call_llm

settings = get_settings()


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    description: str = ""


@dataclass
class ExtractedClaim:
    text: str
    entities_mentioned: list[str] = field(default_factory=list)
    raw_confidence: float = 0.5


@dataclass
class ExtractedRelationship:
    subject: str
    predicate: str
    object: str


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    claims: list[ExtractedClaim] = field(default_factory=list)
    relationships: list[ExtractedRelationship] = field(default_factory=list)


_BASE_EXTRACTION_PROMPT = """You are extracting structured knowledge from a video transcript chunk.

Domain: {domain}
Video: "{video_title}"
Timestamp: {start_time:.1f}s – {end_time:.1f}s

Transcript:
{text}

Extract the following and return ONLY valid JSON matching this schema:
{{
  "entities": [
    {{"name": "...", "entity_type": "concept|person|product|organization|technology|number_claim|process", "description": "..."}}
  ],
  "claims": [
    {{"text": "...", "entities_mentioned": ["entity_name_1"], "raw_confidence": 0.0-1.0}}
  ],
  "relationships": [
    {{"subject": "...", "predicate": "...", "object": "..."}}
  ]
}}

Guidelines:
- Claims are verifiable statements of fact (not opinions unless clearly stated as the creator's view)
- raw_confidence: 1.0 = stated definitively, 0.5 = stated with uncertainty, 0.2 = speculative
- Only extract entities and claims actually present in the text above
- Return empty arrays if the chunk contains no extractable knowledge (e.g., intro/outro, filler)
- For Arabic text, extract Arabic names and terms as-is; do not translate them
- Minimum claim length: 10 words"""

_FINANCE_ADDITION = """
Additional instructions for Finance domain:
- Extract specific numbers, percentages, dates, and financial instruments as claims
- Mark predictions about future prices/events with raw_confidence <= 0.4
"""

_TECH_ADDITION = """
Additional instructions for Consumer Electronics/Technology domain:
- Extract product specifications as claims (e.g., "Model X has 8GB RAM")
- Comparisons between products are valuable relationships
"""

_DOMAIN_ADDITIONS = {
    "finance": _FINANCE_ADDITION,
    "investing": _FINANCE_ADDITION,
    "consumer electronics": _TECH_ADDITION,
    "technology": _TECH_ADDITION,
    "smartphones": _TECH_ADDITION,
}


def extract_from_chunk(
    text: str,
    video_title: str,
    start_time: float,
    end_time: float,
    domain: str,
) -> ExtractionResult:
    domain_lower = domain.lower()
    addition = next(
        (v for k, v in _DOMAIN_ADDITIONS.items() if k in domain_lower),
        "",
    )

    prompt = _BASE_EXTRACTION_PROMPT.format(
        domain=domain,
        video_title=video_title,
        start_time=start_time,
        end_time=end_time,
        text=text,
    ) + addition

    response = call_llm(
        prompt=prompt,
        model=settings.llm_model,
        temperature=0.1,
        max_tokens=2000,
    )

    return _parse_extraction_response(response)


def _parse_extraction_response(response: str) -> ExtractionResult:
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        m = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", response)
        if m:
            data = json.loads(m.group(1))
        else:
            return ExtractionResult()

    entities = [
        ExtractedEntity(
            name=e.get("name", ""),
            entity_type=e.get("entity_type", "concept"),
            description=e.get("description", ""),
        )
        for e in data.get("entities", [])
        if e.get("name")
    ]

    claims = [
        ExtractedClaim(
            text=c.get("text", ""),
            entities_mentioned=c.get("entities_mentioned", []),
            raw_confidence=float(c.get("raw_confidence", 0.5)),
        )
        for c in data.get("claims", [])
        if len(c.get("text", "").split()) >= 5
    ]

    relationships = [
        ExtractedRelationship(
            subject=r.get("subject", ""),
            predicate=r.get("predicate", ""),
            object=r.get("object", ""),
        )
        for r in data.get("relationships", [])
        if r.get("subject") and r.get("object")
    ]

    return ExtractionResult(entities=entities, claims=claims, relationships=relationships)
