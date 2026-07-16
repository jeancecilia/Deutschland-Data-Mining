from datetime import UTC, datetime

from app.db import base  # noqa: F401
from app.db.session import SessionLocal
from app.services.bsr_tracking import refresh_recent_cluster_bsr_snapshots
from app.services.discovery_engine import run_discovery_cycle
from app.services.search_collection import refresh_recent_keyword_search_runs
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.heartbeat")
def heartbeat() -> dict[str, str]:
    return {"status": "alive", "timestamp": datetime.now(UTC).isoformat()}


@celery_app.task(name="app.worker.tasks.refresh_recent_bsr_snapshots")
def refresh_recent_bsr_snapshots() -> dict[str, int | str]:
    db = SessionLocal()
    try:
        summary = refresh_recent_cluster_bsr_snapshots(db)
        summary["timestamp"] = datetime.now(UTC).isoformat()
        return summary
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.refresh_recent_search_runs")
def refresh_recent_search_runs() -> dict[str, int | str]:
    db = SessionLocal()
    try:
        summary = refresh_recent_keyword_search_runs(db)
        summary["timestamp"] = datetime.now(UTC).isoformat()
        return summary
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.run_discovery_cycle")
def run_discovery_cycle_task() -> dict[str, int | str]:
    db = SessionLocal()
    try:
        cycle = run_discovery_cycle(
            db,
            generate_limit=90,
            validate_limit=4,
            auto_generate_reports=False,
            force=False,
        )
        return {
            "run_id": cycle.run_id,
            "generated_count": cycle.generated_count,
            "updated_count": cycle.updated_count,
            "deduplicated_count": cycle.deduplicated_count,
            "validated_count": cycle.validated_count,
            "kept_count": cycle.kept_count,
            "failed_count": cycle.failed_count,
            "report_count": cycle.report_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


# ── Discovery Pipeline Tasks ────────────────────────────────────────────────


@celery_app.task(name="app.worker.tasks.discovery_import_seeds")
def discovery_import_seeds() -> dict:
    """Import all CSV seed universe files into raw_discovery_items."""
    db = SessionLocal()
    try:
        from app.services.discovery import import_all_seed_universes
        results = import_all_seed_universes(db)
        return {"status": "ok", "imported": results, "timestamp": datetime.now(UTC).isoformat()}
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.discovery_extract_entities")
def discovery_extract_entities() -> dict:
    """Extract entities from raw_discovery_items."""
    db = SessionLocal()
    try:
        from app.services.discovery import extract_entities_from_raw_items
        result = extract_entities_from_raw_items(db, limit=500)
        return {
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.discovery_build_relations")
def discovery_build_relations() -> dict:
    """Build entity relations (Topic Graph)."""
    db = SessionLocal()
    try:
        from app.services.discovery.relation_builder import build_entity_relations
        result = build_entity_relations(db, limit_per_rule=20)
        return {
            "created": result.created,
            "skipped": result.skipped,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.discovery_compose_candidates")
def discovery_compose_candidates() -> dict:
    """Compose niche candidates from entities and templates."""
    db = SessionLocal()
    try:
        from app.services.discovery import compose_niche_candidates
        batch = compose_niche_candidates(db, limit=500)
        return {
            "created": batch.created,
            "skipped_blocked": batch.skipped_blocked,
            "skipped_duplicate": batch.skipped_duplicate,
            "skipped_generic": batch.skipped_generic,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.discovery_fast_validate")
def discovery_fast_validate() -> dict:
    """Fast-validate new niche candidates."""
    db = SessionLocal()
    try:
        from app.services.discovery import validate_candidates_fast
        results = validate_candidates_fast(db, limit=100)
        promoted = sum(1 for r in results if r.recommendation_label == "GO")
        rejected = sum(1 for r in results if r.recommendation_label in ("NO-GO", "BLOCKED"))
        return {
            "total": len(results),
            "promoted": promoted,
            "rejected": rejected,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.discovery_promote_candidates")
def discovery_promote_candidates() -> dict:
    """Promote validated candidates to seed keywords."""
    db = SessionLocal()
    try:
        from app.services.discovery import promote_candidates_to_seeds
        batch = promote_candidates_to_seeds(db, limit=50, min_score=50)
        return {
            "promoted": batch.promoted,
            "skipped": batch.skipped,
            "keyword_ids": [kw.id for kw in batch.keywords],
            "timestamp": datetime.now(UTC).isoformat(),
        }
    finally:
        db.close()


# PostgreSQL advisory lock ID for the full discovery pipeline
_FULL_PIPELINE_LOCK_ID = 1001


def _acquire_advisory_lock(db, lock_id: int) -> bool:
    """Try to acquire a PostgreSQL advisory lock. Returns True if acquired."""
    from sqlalchemy import text
    result = db.execute(text("SELECT pg_try_advisory_lock(:id)"), {"id": lock_id}).scalar()
    return bool(result)


def _release_advisory_lock(db, lock_id: int) -> None:
    """Release a PostgreSQL advisory lock."""
    from sqlalchemy import text
    db.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": lock_id})


@celery_app.task(
    name="app.worker.tasks.discovery_full_pipeline",
    time_limit=3600,
    soft_time_limit=3300,
    acks_late=True,
)
def discovery_full_pipeline() -> dict:
    """Run the full initial discovery pipeline sequentially.

    Uses a PostgreSQL advisory lock to prevent overlapping runs.
    """
    db = SessionLocal()
    if not _acquire_advisory_lock(db, _FULL_PIPELINE_LOCK_ID):
        db.close()
        return {"status": "skipped", "reason": "Another pipeline run is in progress."}

    result: dict[str, object] = {
        "import_seeds": None,
        "extract_entities": None,
        "build_relations": None,
        "compose_candidates": None,
        "fast_validate": None,
        "promote_candidates": None,
    }

    try:
        from app.services.discovery import (
            import_all_seed_universes,
            extract_entities_from_raw_items,
            compose_niche_candidates,
            validate_candidates_fast,
            promote_candidates_to_seeds,
        )
        from app.services.discovery.relation_builder import build_entity_relations

        # Step 1: Import seeds
        import_results = import_all_seed_universes(db)
        result["import_seeds"] = {"status": "ok", "files": import_results}

        # Step 2: Extract entities
        ext_result = extract_entities_from_raw_items(db, limit=500)
        result["extract_entities"] = {
            "created": ext_result.created,
            "updated": ext_result.updated,
            "skipped": ext_result.skipped,
        }

        # Step 3: Build relations
        rel_result = build_entity_relations(db, limit_per_rule=20)
        result["build_relations"] = {
            "created": rel_result.created,
            "skipped": rel_result.skipped,
        }

        # Step 4: Compose candidates
        comp_batch = compose_niche_candidates(db, limit=500)
        result["compose_candidates"] = {
            "created": comp_batch.created,
            "skipped_blocked": comp_batch.skipped_blocked,
            "skipped_duplicate": comp_batch.skipped_duplicate,
            "skipped_generic": comp_batch.skipped_generic,
        }

        # Step 5: Fast validate
        val_results = validate_candidates_fast(db, limit=100)
        result["fast_validate"] = {
            "total": len(val_results),
            "promoted": sum(1 for r in val_results if r.recommendation_label == "GO"),
            "rejected": sum(1 for r in val_results if r.recommendation_label in ("NO-GO", "BLOCKED")),
        }

        # Step 6: Promote
        promo_batch = promote_candidates_to_seeds(db, limit=50, min_score=50)
        result["promote_candidates"] = {
            "promoted": promo_batch.promoted,
            "skipped": promo_batch.skipped,
        }

        result["timestamp"] = datetime.now(UTC).isoformat()
        return result
    finally:
        _release_advisory_lock(db, _FULL_PIPELINE_LOCK_ID)
        db.close()
