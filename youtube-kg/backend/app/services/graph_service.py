"""
Neo4j graph operations. All writes use MERGE for idempotency.
Every relationship carries source traceability fields.
"""
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from neo4j import GraphDatabase, Driver

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_driver() -> Driver:
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def ensure_constraints():
    with get_driver().session() as session:
        session.run("CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE")
        session.run("CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE")
        session.run("CREATE CONSTRAINT video_yt_id IF NOT EXISTS FOR (v:Video) REQUIRE v.youtube_id IS UNIQUE")
        session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (t:Transcript_Chunk) REQUIRE t.id IS UNIQUE")
        session.run("CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)")
        session.run("CREATE INDEX claim_project IF NOT EXISTS FOR (c:Claim) ON (c.project_id)")


def upsert_video_node(youtube_id: str, title: str, project_id: str, published_at: str | None = None):
    with get_driver().session() as session:
        session.run(
            """
            MERGE (v:Video {youtube_id: $youtube_id})
            SET v.title = $title,
                v.project_id = $project_id,
                v.published_at = $published_at
            """,
            youtube_id=youtube_id,
            title=title,
            project_id=str(project_id),
            published_at=published_at,
        )


def upsert_chunk_node(chunk_id: str, text: str, start_time: float, end_time: float, youtube_id: str, video_id: str):
    with get_driver().session() as session:
        session.run(
            """
            MERGE (t:Transcript_Chunk {id: $id})
            SET t.text = $text,
                t.start_time = $start_time,
                t.end_time = $end_time,
                t.youtube_id = $youtube_id,
                t.video_id = $video_id
            """,
            id=chunk_id,
            text=text[:1000],  # cap stored text length
            start_time=start_time,
            end_time=end_time,
            youtube_id=youtube_id,
            video_id=str(video_id),
        )


def upsert_concept_node(name: str, domain: str, project_id: str, description: str = "") -> str:
    concept_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{project_id}:{name.lower()}"))
    with get_driver().session() as session:
        session.run(
            """
            MERGE (c:Concept {id: $id})
            SET c.name = $name,
                c.domain = $domain,
                c.project_id = $project_id,
                c.description = $description
            """,
            id=concept_id,
            name=name,
            domain=domain,
            project_id=str(project_id),
            description=description,
        )
    return concept_id


def upsert_claim_node(
    claim_id: str,
    text: str,
    project_id: str,
    domain: str,
    raw_confidence: float,
) -> None:
    with get_driver().session() as session:
        session.run(
            """
            MERGE (c:Claim {id: $id})
            SET c.text = $text,
                c.project_id = $project_id,
                c.domain = $domain,
                c.raw_confidence = $raw_confidence,
                c.confidence_score = $raw_confidence,
                c.verification_status = 'pending',
                c.occurrence_count = coalesce(c.occurrence_count, 0) + 1
            """,
            id=claim_id,
            text=text,
            project_id=str(project_id),
            domain=domain,
            raw_confidence=raw_confidence,
        )


def link_claim_to_chunk(
    claim_id: str,
    chunk_id: str,
    youtube_id: str,
    video_id: str,
    start_time: float,
    end_time: float,
    transcript_excerpt: str,
    raw_confidence: float,
):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (cl:Claim {id: $claim_id})
            MATCH (ch:Transcript_Chunk {id: $chunk_id})
            MERGE (cl)-[r:SUPPORTED_BY {chunk_id: $chunk_id}]->(ch)
            SET r.source_video_id = $video_id,
                r.youtube_id = $youtube_id,
                r.start_time = $start_time,
                r.end_time = $end_time,
                r.transcript_excerpt = $excerpt,
                r.raw_confidence = $raw_confidence,
                r.extracted_at = datetime()
            """,
            claim_id=claim_id,
            chunk_id=chunk_id,
            video_id=str(video_id),
            youtube_id=youtube_id,
            start_time=start_time,
            end_time=end_time,
            excerpt=transcript_excerpt[:500],
            raw_confidence=raw_confidence,
        )


def link_concept_to_claim(concept_id: str, claim_id: str, weight: float = 1.0):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (c:Concept {id: $concept_id})
            MATCH (cl:Claim {id: $claim_id})
            MERGE (c)-[:MENTIONS {weight: $weight}]->(cl)
            """,
            concept_id=concept_id,
            claim_id=claim_id,
            weight=weight,
        )


def link_claim_to_video(claim_id: str, youtube_id: str):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (cl:Claim {id: $claim_id})
            MATCH (v:Video {youtube_id: $youtube_id})
            MERGE (cl)-[:APPEARS_IN]->(v)
            """,
            claim_id=claim_id,
            youtube_id=youtube_id,
        )


def set_claim_corroborates(claim_a_id: str, claim_b_id: str, similarity: float):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (a:Claim {id: $a}), (b:Claim {id: $b})
            MERGE (a)-[r:CORROBORATES]->(b)
            SET r.similarity_score = $sim, r.detected_at = datetime()
            """,
            a=claim_a_id,
            b=claim_b_id,
            sim=similarity,
        )


def set_claim_contradicts(claim_a_id: str, claim_b_id: str, similarity: float, reasoning: str):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (a:Claim {id: $a}), (b:Claim {id: $b})
            MERGE (a)-[r:CONTRADICTS]->(b)
            SET r.similarity_score = $sim,
                r.llm_reasoning = $reasoning,
                r.detected_at = datetime()
            """,
            a=claim_a_id,
            b=claim_b_id,
            sim=similarity,
            reasoning=reasoning,
        )


def update_claim_score(claim_id: str, confidence_score: float, verification_status: str, distinct_video_count: int):
    with get_driver().session() as session:
        session.run(
            """
            MATCH (c:Claim {id: $id})
            SET c.confidence_score = $score,
                c.verification_status = $status,
                c.distinct_video_count = $vid_count
            """,
            id=claim_id,
            score=confidence_score,
            status=verification_status,
            vid_count=distinct_video_count,
        )


def get_project_claims(project_id: str) -> list[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (c:Claim {project_id: $project_id})
            OPTIONAL MATCH (c)-[r:SUPPORTED_BY]->(ch:Transcript_Chunk)
            WITH c, collect({
                chunk_id: ch.id,
                youtube_id: r.youtube_id,
                start_time: r.start_time,
                end_time: r.end_time,
                excerpt: r.transcript_excerpt,
                video_id: r.source_video_id
            }) AS evidence
            RETURN c.id AS id, c.text AS text, c.domain AS domain,
                   c.confidence_score AS confidence_score,
                   c.raw_confidence AS raw_confidence,
                   c.verification_status AS verification_status,
                   c.occurrence_count AS occurrence_count,
                   evidence
            """,
            project_id=str(project_id),
        )
        return [dict(r) for r in result]


def get_graph_overview(project_id: str) -> dict:
    with get_driver().session() as session:
        r = session.run(
            """
            MATCH (n {project_id: $pid})
            WITH labels(n)[0] AS label, count(n) AS cnt
            RETURN collect({label: label, count: cnt}) AS counts
            """,
            pid=str(project_id),
        ).single()
        counts = r["counts"] if r else []
        return {c["label"]: c["count"] for c in counts}


def get_claim_with_evidence(claim_id: str) -> dict | None:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (c:Claim {id: $id})
            OPTIONAL MATCH (c)-[r:SUPPORTED_BY]->(ch:Transcript_Chunk)
            OPTIONAL MATCH (c)-[:CORROBORATES]->(corr:Claim)
            OPTIONAL MATCH (c)-[:CONTRADICTS]->(cont:Claim)
            WITH c,
                 collect(DISTINCT {chunk_id: ch.id, text: ch.text, start_time: r.start_time,
                                   end_time: r.end_time, youtube_id: r.youtube_id,
                                   excerpt: r.transcript_excerpt}) AS chunks,
                 collect(DISTINCT {id: corr.id, text: corr.text}) AS corroborates,
                 collect(DISTINCT {id: cont.id, text: cont.text}) AS contradicts
            RETURN c, chunks, corroborates, contradicts
            """,
            id=claim_id,
        ).single()
        if not result:
            return None
        c = dict(result["c"])
        c["supporting_chunks"] = result["chunks"]
        c["corroborates"] = result["corroborates"]
        c["contradicts"] = result["contradicts"]
        return c
