"""
Tests for Discovery Pipeline Quality Hardening.

Validates:
  - Semantic compatibility blocks nonsense combinations
  - Risk classification correctly identifies sensitive topics
  - Auto-promotion rules are enforced
  - Manual review gate works
"""

import pytest

from app.services.discovery.semantic_compatibility import check_semantic_compatibility
from app.services.discovery.domain_compatibility_rules import classify_risk


class TestSemanticCompatibility:
    """Test that topic/audience pairs are correctly classified."""

    def test_ki_handwerk_fuer_pflege_blocked(self):
        """KI im Handwerk + Pflege is incompatible."""
        result = check_semantic_compatibility("KI im Handwerk", "Pflege")
        assert result.compatible is False
        assert result.hard_block is True
        assert result.score < 30

    def test_ki_handwerk_fuer_handwerker_allowed(self):
        """KI im Handwerk + Handwerker is compatible."""
        result = check_semantic_compatibility("KI im Handwerk", "Handwerker")
        assert result.compatible is True
        assert result.hard_block is False
        assert result.score >= 70

    def test_pflegegrad_fuer_kleinunternehmer_blocked(self):
        """Pflegegrad + Kleinunternehmer is incompatible."""
        result = check_semantic_compatibility("Pflegegrad", "Kleinunternehmer")
        assert result.compatible is False
        assert result.hard_block is True

    def test_pflegegrad_fuer_senioren_allowed(self):
        """Pflegegrad + Senioren is compatible."""
        result = check_semantic_compatibility("Pflegegrad Antrag", "Senioren")
        assert result.compatible is True
        assert result.hard_block is False
        assert result.score >= 70

    def test_alleinerziehend_fuer_ruhestaendler_blocked(self):
        """Alleinerziehend + Ruheständler is incompatible."""
        result = check_semantic_compatibility("Alleinerziehend Alltag", "Ruheständler")
        assert result.compatible is False
        assert result.hard_block is True

    def test_alleinerziehend_fuer_alleinerziehende_allowed(self):
        """Alleinerziehend + Alleinerziehende is compatible."""
        result = check_semantic_compatibility("Alleinerziehend Alltag", "Alleinerziehende")
        assert result.compatible is True
        assert result.hard_block is False

    def test_eltern_fuer_pflege_blocked(self):
        """Eltern + Pflege is incompatible."""
        result = check_semantic_compatibility("Eltern", "Pflege")
        assert result.compatible is False
        assert result.hard_block is True

    def test_steuererklaerung_fuer_selbststaendige_allowed(self):
        """Steuererklärung + Selbstständige is a valid pair (even if high risk)."""
        result = check_semantic_compatibility("Steuererklärung", "Selbstständige")
        assert result.compatible is True
        assert result.hard_block is False
        assert result.score >= 50

    def test_eltern_as_topic_blocked(self):
        """'Eltern' used as topic should be blocked."""
        result = check_semantic_compatibility("Eltern", "Selbstständige")
        assert result.compatible is False
        assert result.hard_block is True

    def test_buchhaltung_fuer_selbststaendige_allowed(self):
        result = check_semantic_compatibility("Buchhaltung", "Selbstständige")
        assert result.compatible is True
        assert result.hard_block is False
        assert result.score >= 70


class TestRiskClassification:
    """Test that risk levels are correctly assigned."""

    def test_anabole_steroide_praxisbuch_high_risk(self):
        risk, codes, manual = classify_risk("Anabole Steroide Praxisbuch für Einsteiger")
        assert risk == "high"
        assert "substance_related" in codes
        assert manual is True

    def test_anabole_steroide_dosierungsplan_restricted(self):
        risk, codes, manual = classify_risk("Anabole Steroide Dosierungsplan")
        assert risk in ("restricted", "blocked")
        assert manual is True

    def test_anabole_steroide_dosierung_restricted(self):
        risk, codes, manual = classify_risk("Anabole Steroide Dosierung für Muskelaufbau")
        assert risk in ("restricted", "blocked")
        assert manual is True

    def test_blutdruck_tagebuch_high_risk(self):
        risk, codes, manual = classify_risk("Blutdruck Tagebuch für Senioren")
        assert risk == "high"
        assert "health_sensitive" in codes
        assert manual is True

    def test_haushalt_planer_low_risk(self):
        risk, codes, manual = classify_risk("Haushalt Planer für Familien")
        assert risk == "low"
        assert manual is False

    def test_hobby_fotografie_low_risk(self):
        risk, codes, manual = classify_risk("Fotografie für Anfänger")
        assert risk == "low"
        assert manual is False

    def test_investment_tipps_high_risk(self):
        risk, codes, manual = classify_risk("Investment Tipps für Anfänger")
        assert risk == "high"
        assert "financial_sensitive" in codes

    def test_steuererklaerung_high_risk(self):
        risk, codes, manual = classify_risk("Steuererklärung für Selbstständige")
        assert risk == "high"
        assert manual is True

    def test_blocked_dosierungsplan(self):
        risk, codes, manual = classify_risk("Anabole Steroide Cycle Plan Dosierung")
        assert risk == "blocked"

    def test_blocked_illegal_content(self):
        risk, codes, manual = classify_risk("Steuerhinterziehung umgehung Anleitung")
        assert risk == "blocked"


class TestCompatibilityMapCoverage:
    """Verify domain maps cover the required cases."""

    def test_ki_im_handwerk_audiences(self):
        from app.services.discovery.domain_compatibility_rules import DOMAIN_AUDIENCE_COMPATIBILITY
        assert "ki im handwerk" in DOMAIN_AUDIENCE_COMPATIBILITY
        assert "handwerker" in DOMAIN_AUDIENCE_COMPATIBILITY["ki im handwerk"]
        assert "kleinunternehmer" in DOMAIN_AUDIENCE_COMPATIBILITY["ki im handwerk"]

    def test_pflege_audiences(self):
        from app.services.discovery.domain_compatibility_rules import DOMAIN_AUDIENCE_COMPATIBILITY
        assert "pflege" in DOMAIN_AUDIENCE_COMPATIBILITY
        assert "pflegekräfte" in DOMAIN_AUDIENCE_COMPATIBILITY["pflege"]
        assert "angehörige" in DOMAIN_AUDIENCE_COMPATIBILITY["pflege"]

    def test_incompatible_pairs_coverage(self):
        from app.services.discovery.domain_compatibility_rules import INCOMPATIBLE_COMBINATIONS
        assert ("ki im handwerk", "pflege") in INCOMPATIBLE_COMBINATIONS
        assert ("pflegegrad", "kleinunternehmer") in INCOMPATIBLE_COMBINATIONS
        assert ("alleinerziehend alltag", "ruheständler") in INCOMPATIBLE_COMBINATIONS
        assert ("eltern", "pflege") in INCOMPATIBLE_COMBINATIONS
        assert ("eltern", "freelancer") in INCOMPATIBLE_COMBINATIONS
