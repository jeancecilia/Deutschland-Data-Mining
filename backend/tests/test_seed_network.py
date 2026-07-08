"""Tests for the large-scale discovery seed network."""
import pytest
from app.services.discovery.domain_compatibility_rules import (
    DOMAIN_AUDIENCE_COMPATIBILITY,
    INCOMPATIBLE_COMBINATIONS,
    BLOCKED_WORDS,
    HEALTH_RISK_WORDS,
    load_compatibility_from_csvs,
)


class TestCSVLoader:
    """Verify CSV compatibility files are loaded and merge with hardcoded rules."""

    def test_loader_returns_counts(self):
        result = load_compatibility_from_csvs()
        assert result["compat_loaded"] > 0, "No compatibility pairs loaded from CSV"
        assert result["incompat_loaded"] > 0, "No incompatible pairs loaded from CSV"
        assert result["risk_loaded"] > 0, "No risk rules loaded from CSV"

    def test_csv_compat_rule_works(self):
        """A compatibility pair from CSV should work even if not hardcoded."""
        load_compatibility_from_csvs()
        # 'Medikamentenplan für Pflegebedürftige' comes from CSV
        assert "medikamentenplan" in DOMAIN_AUDIENCE_COMPATIBILITY
        assert "pflegebedürftige" in DOMAIN_AUDIENCE_COMPATIBILITY["medikamentenplan"]

    def test_csv_incompat_rule_works(self):
        """An incompatible pair from CSV should block."""
        load_compatibility_from_csvs()
        assert ("geburt vorbereitung", "rentner") in INCOMPATIBLE_COMBINATIONS or \
               ("geburtsvorbereitung", "rentner") in INCOMPATIBLE_COMBINATIONS

    def test_csv_risk_rule_works(self):
        """Risk rules from CSV should be loaded into word sets."""
        load_compatibility_from_csvs()
        # CSV risk rules should have added more blocked words
        assert len(BLOCKED_WORDS) >= 2, "CSV should have added blocked words"
        assert len(HEALTH_RISK_WORDS) >= 5, "CSV should have added health risk words"

    def test_idempotent_loading(self):
        """Loading twice should not cause errors or duplicates."""
        r1 = load_compatibility_from_csvs()
        r2 = load_compatibility_from_csvs()
        # Second load should find fewer new items (already loaded)
        assert r2["compat_loaded"] <= r1["compat_loaded"]
        assert r2["incompat_loaded"] <= r1["incompat_loaded"]


class TestSeedCount:
    """Verify seed data meets minimum targets."""

    def test_compat_pairs_count(self):
        load_compatibility_from_csvs()
        total = sum(len(v) for v in DOMAIN_AUDIENCE_COMPATIBILITY.values())
        assert total >= 100, f"Expected 100+ compatibility pairs, got {total}"

    def test_incompat_pairs_count(self):
        load_compatibility_from_csvs()
        assert len(INCOMPATIBLE_COMBINATIONS) >= 100, \
            f"Expected 100+ incompatible pairs, got {len(INCOMPATIBLE_COMBINATIONS)}"

    def test_seed_files_exist(self):
        from pathlib import Path
        import glob
        base = Path(__file__).resolve().parents[2] / "data" / "discovery_seed_universes"
        csv_files = list(glob.glob(str(base / "**/*.csv"), recursive=True))
        assert len(csv_files) >= 40, f"Expected 40+ CSV files, got {len(csv_files)}"
