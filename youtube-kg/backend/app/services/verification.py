"""
Verifies claims across multiple videos.
Rules:
  - Minimum 2 distinct source videos per claim cluster
  - Semantic similarity threshold: 0.82 for grouping
  - Confidence formula: (occurrence * 0.4) + (source_consistency * 0.3) + (semantic_coherence * 0.3)
"""
import json
import uuid
from collections import defaultdict

import numpy as np
from qdrant_client import QdrantClient

from app.config import get_settings
from app.services import graph_service as graph
from app.services.llm import call_llm
from app.services.memory import COLLECTION_CLAIMS, get_qdrant

settings = get_settings()

_CONTRADICTION_PROMPT = """You are evaluating two claims from the same knowledge domain.

Claim A: "{claim_a}"
Claim B: "{claim_b}"

Do these claims express contradictory or opposing views about the same subject?
Respond with ONLY valid JSON: {{"contradicts": true|false, "reasoning": "one sentence"}}"""


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _check_contradiction(text_a: str, text_b: str) -> tuple[bool, str]:
    try:
        resp = call_llm(
            prompt=_CONTRADICTION_PROMPT.format(claim_a=text_a, claim_b=text_b),
            model=settings.llm_model,
            temperature=0.0,
            max_tokens=100,
        )
        data = json.loads(resp)
        return bool(data.get("contradicts")), data.get("reasoning", "")
    except Exception:
        return False, ""


def run_verification(project_id: str) -> dict:
    """
    Runs the full verification pipeline for a project.
    Returns summary stats.
    """
    project_id_str = str(project_id)

    # 1. Load all claims from Neo4j
    claims = graph.get_project_claims(project_id_str)
    if not claims:
        return {"verified": 0, "contradicted": 0, "insufficient": 0}

    # 2. Load their embeddings from Qdrant
    client = get_qdrant()
    claim_ids = [c["id"] for c in claims]
    qdrant_results = client.retrieve(
        collection_name=COLLECTION_CLAIMS,
        ids=claim_ids,
        with_vectors=True,
    )
    id_to_vec = {str(r.id): np.array(r.vector) for r in qdrant_results if r.vector}

    if not id_to_vec:
        return {"verified": 0, "contradicted": 0, "insufficient": 0}

    # 3. Group claims by semantic similarity (union-find approach)
    valid_claims = [c for c in claims if c["id"] in id_to_vec]
    n = len(valid_claims)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int):
        pi, pj = find(i), find(j)
        if pi != pj:
            parent[pi] = pj

    threshold = settings.verification_similarity_threshold

    for i in range(n):
        for j in range(i + 1, n):
            cid_i = valid_claims[i]["id"]
            cid_j = valid_claims[j]["id"]
            if cid_i in id_to_vec and cid_j in id_to_vec:
                sim = _cosine_sim(id_to_vec[cid_i], id_to_vec[cid_j])
                if sim >= threshold:
                    union(i, j)

    # 4. Collect clusters
    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    stats = {"verified": 0, "contradicted": 0, "insufficient": 0}

    total_videos = len(set(
        ev["video_id"]
        for c in valid_claims
        for ev in c.get("evidence", [])
        if ev.get("video_id")
    )) or 1

    for cluster_indices in clusters.values():
        cluster_claims = [valid_claims[i] for i in cluster_indices]

        # Count distinct source videos across the cluster
        source_videos = set()
        for c in cluster_claims:
            for ev in c.get("evidence", []):
                if ev.get("video_id"):
                    source_videos.add(ev["video_id"])

        if len(source_videos) < settings.verification_min_occurrences:
            for c in cluster_claims:
                graph.update_claim_score(c["id"], c.get("raw_confidence", 0.5), "insufficient_evidence", len(source_videos))
            stats["insufficient"] += len(cluster_claims)
            continue

        # Compute cluster centroid
        vecs = [id_to_vec[c["id"]] for c in cluster_claims if c["id"] in id_to_vec]
        centroid = np.mean(vecs, axis=0)

        # Confidence scores
        confidences = [c.get("raw_confidence", 0.5) for c in cluster_claims]
        occurrence_weight = min(len(source_videos) / total_videos, 1.0)
        source_consistency = 1.0 - float(np.std(confidences))
        semantic_coherence = float(np.mean([
            _cosine_sim(id_to_vec[c["id"]], centroid)
            for c in cluster_claims
            if c["id"] in id_to_vec
        ]))

        confidence = (
            occurrence_weight * settings.verification_occurrence_weight
            + max(0, source_consistency) * settings.verification_source_consistency_weight
            + semantic_coherence * settings.verification_semantic_coherence_weight
        )

        # Mark all claims in cluster as CORROBORATES
        for i, ca in enumerate(cluster_claims):
            for cb in cluster_claims[i + 1:]:
                sim = _cosine_sim(id_to_vec.get(ca["id"], centroid), id_to_vec.get(cb["id"], centroid))
                graph.set_claim_corroborates(ca["id"], cb["id"], float(sim))

        # Check for contradictions within cluster (only for borderline similarity pairs)
        for i, ca in enumerate(cluster_claims):
            for cb in cluster_claims[i + 1:]:
                sim = _cosine_sim(id_to_vec.get(ca["id"], centroid), id_to_vec.get(cb["id"], centroid))
                if threshold <= sim <= 0.92:
                    is_contradiction, reasoning = _check_contradiction(ca["text"], cb["text"])
                    if is_contradiction:
                        graph.set_claim_contradicts(ca["id"], cb["id"], float(sim), reasoning)
                        graph.update_claim_score(ca["id"], confidence, "contradicted", len(source_videos))
                        graph.update_claim_score(cb["id"], confidence, "contradicted", len(source_videos))
                        stats["contradicted"] += 1
                        continue

            graph.update_claim_score(ca["id"], confidence, "verified", len(source_videos))
            stats["verified"] += 1

    return stats
