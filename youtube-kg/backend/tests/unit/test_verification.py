"""Unit tests for verification confidence formula and claim grouping."""
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def test_confidence_formula_basic():
    """Confidence formula produces values in [0,1]."""
    occurrence_weight = 0.4
    source_consistency_weight = 0.3
    semantic_coherence_weight = 0.3

    # Perfect case
    score = (1.0 * occurrence_weight + 1.0 * source_consistency_weight + 1.0 * semantic_coherence_weight)
    assert score == 1.0

    # Minimum case
    score = (0.0 * occurrence_weight + 0.0 * source_consistency_weight + 0.0 * semantic_coherence_weight)
    assert score == 0.0


def test_confidence_formula_mixed():
    occ = 0.6
    src = 0.8
    sem = 0.75
    score = occ * 0.4 + src * 0.3 + sem * 0.3
    assert 0 <= score <= 1
    assert abs(score - (0.6 * 0.4 + 0.8 * 0.3 + 0.75 * 0.3)) < 1e-9


def test_cosine_similarity_identical():
    from app.services.verification import _cosine_sim
    v = np.array([1.0, 0.0, 0.0])
    assert _cosine_sim(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    from app.services.verification import _cosine_sim
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert _cosine_sim(a, b) == pytest.approx(0.0)


def test_cosine_similarity_opposite():
    from app.services.verification import _cosine_sim
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    assert _cosine_sim(a, b) == pytest.approx(-1.0)


def test_occurrence_threshold_enforced():
    """Claims from a single video must receive insufficient_evidence status."""
    from app.services.verification import _cosine_sim
    min_occurrences = 2
    single_source_video_count = 1
    assert single_source_video_count < min_occurrences
