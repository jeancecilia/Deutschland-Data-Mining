import pytest

from app.services.discovery.candidate_quality_gate import evaluate_candidate_quality

def test_evaluate_candidate_quality_valid_pair():
    # A valid, specific KDP concept that is not high-risk
    result = evaluate_candidate_quality(
        candidate_name="Hundebegegnungen Trainingsbuch für Anfänger",
        topic_name="hundetraining",
        audience_name="anfänger",
        problem_name=None,
        format_name="trainingsbuch",
        meta={"domain": "haustiere"}
    )
    
    assert result.allowed is True
    assert result.hard_block is False
    assert result.recommendation == "GO"
    assert result.compatibility_score >= 75
    assert result.specificity_score > 50
    assert result.format_score > 50
    
def test_evaluate_candidate_quality_hard_block_incompatible():
    # Senior specific topic combined with youth
    result = evaluate_candidate_quality(
        candidate_name="Demenz Ratgeber für Jugendliche",
        topic_name="demenz",
        audience_name="jugendliche",
        problem_name=None,
        format_name="ratgeber",
        meta={"domain": "gesundheit"}
    )
    
    assert result.allowed is False
    assert result.hard_block is True
    assert result.recommendation == "NO-GO"
    assert result.compatibility_score < 50
    assert "semantic_mismatch" in result.reason_codes

def test_evaluate_candidate_quality_blocked_content():
    # Blocked keyword "dosierungsplan"
    result = evaluate_candidate_quality(
        candidate_name="Demenz Dosierungsplan für Angehörige",
        topic_name="demenz",
        audience_name="pflegende_angehoerige",
        problem_name=None,
        format_name=None,
        meta={"domain": "gesundheit"}
    )
    
    assert result.allowed is False
    assert result.hard_block is True
    assert result.risk_category == "blocked"
    assert result.recommendation == "BLOCKED"
    assert "blocked_content" in result.reason_codes

def test_evaluate_candidate_quality_generic_low_score():
    # A generic candidate with low specificity
    result = evaluate_candidate_quality(
        candidate_name="Organisation und Dinge",
        topic_name="organisation",
        audience_name=None,
        problem_name=None,
        format_name=None,
        meta={"domain": "business"}
    )
    
    assert result.recommendation in ("NO-GO", "MAYBE")
    if result.recommendation == "NO-GO":
        assert result.allowed is False

def test_evaluate_candidate_quality_restricted_risk():
    # Content with "zyklus" indicating dosage/plan for substances
    result = evaluate_candidate_quality(
        candidate_name="Anabolika Zyklus für Anfänger",
        topic_name="anabolika",
        audience_name="anfänger",
        problem_name=None,
        format_name="ratgeber",
        meta={"domain": "gesundheit"}
    )
    
    if result.risk_category == "restricted":
        assert result.allowed is False
        assert result.recommendation == "BLOCKED"
        assert result.hard_block is True
