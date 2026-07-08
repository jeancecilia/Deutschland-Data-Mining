"""Tests for the large-scale discovery seed network."""
import pytest
from pathlib import Path
import glob as _glob

from app.services.discovery.domain_compatibility_rules import (
    DOMAIN_AUDIENCE_COMPATIBILITY,
    INCOMPATIBLE_COMBINATIONS,
    BLOCKED_WORDS,
    HEALTH_RISK_WORDS,
    load_compatibility_from_csvs,
)


def _csv_base():
    """Find the CSV base directory from the test location."""
    for parent in [2, 1, 3]:
        base = Path(__file__).resolve().parents[parent] / "data" / "discovery_seed_universes"
        if base.exists():
            return base
    return Path.cwd() / "data" / "discovery_seed_universes"


class TestCSVLoader:
    """Verify CSV compatibility files are loaded and merge with hardcoded rules."""

    def test_loader_returns_counts(self):
        result = load_compatibility_from_csvs()
        assert result["compat_loaded"] > 0
        assert result["incompat_loaded"] > 0
        assert result["risk_loaded"] > 0

    def test_csv_compat_rule_works(self):
        load_compatibility_from_csvs()
        assert "medikamentenplan" in DOMAIN_AUDIENCE_COMPATIBILITY

    def test_csv_incompat_rule_works(self):
        load_compatibility_from_csvs()
        assert len(INCOMPATIBLE_COMBINATIONS) >= 100

    def test_csv_risk_rule_works(self):
        load_compatibility_from_csvs()
        assert len(BLOCKED_WORDS) >= 2

    def test_idempotent_loading(self):
        r1 = load_compatibility_from_csvs()
        r2 = load_compatibility_from_csvs()
        assert r2["compat_loaded"] <= r1["compat_loaded"]


class TestSeedCount:
    """Verify seed data meets minimum targets."""

    def test_compat_pairs_count(self):
        load_compatibility_from_csvs()
        total = sum(len(v) for v in DOMAIN_AUDIENCE_COMPATIBILITY.values())
        assert total >= 100

    def test_incompat_pairs_count(self):
        load_compatibility_from_csvs()
        assert len(INCOMPATIBLE_COMBINATIONS) >= 100

    def test_seed_files_exist(self):
        base = _csv_base()
        csv_files = list(_glob.glob(str(base / "**/*.csv"), recursive=True))
        assert len(csv_files) >= 50, f"Got {len(csv_files)} files"

    def test_seed_rows_minimum(self):
        base = _csv_base()
        total = 0
        for f in _glob.glob(str(base / "**/*.csv"), recursive=True):
            with open(f, encoding='utf-8-sig') as fh:
                total += sum(1 for _ in fh) - 1
        assert total >= 1500, f"Got {total} rows"

    def test_compat_csv_minimum(self):
        base = _csv_base()
        fpath = base / "compatibility" / "topic_audience_compatibility.csv"
        if fpath.exists():
            with open(fpath, encoding='utf-8-sig') as f:
                count = sum(1 for _ in f) - 1
            assert count >= 150, f"Got {count} compat pairs"

    def test_incompat_csv_minimum(self):
        base = _csv_base()
        fpath = base / "compatibility" / "incompatible_combinations.csv"
        if fpath.exists():
            with open(fpath, encoding='utf-8-sig') as f:
                count = sum(1 for _ in f) - 1
            assert count >= 100, f"Got {count} incompat pairs"

    def test_risk_csv_minimum(self):
        base = _csv_base()
        fpath = base / "compatibility" / "risk_rules.csv"
        if fpath.exists():
            with open(fpath, encoding='utf-8-sig') as f:
                count = sum(1 for _ in f) - 1
            assert count >= 100, f"Got {count} risk rules"
