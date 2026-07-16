import sys
import os
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline")

import app.db.base
from app.db.session import SessionLocal
from app.models.discovery_pipeline import RawDiscoveryItem, DiscoveryEntity, DiscoveryEntityRelation, NicheCandidate
from app.services.discovery.source_registry import import_all_seed_universes
from app.services.discovery.entity_extractor import extract_entities_from_raw_items
from app.services.discovery.relation_builder import build_entity_relations
from app.services.discovery.domain_composer import compose_micro_domain_candidates, compose_domain_aware_candidates
from app.services.discovery.niche_candidate_composer import compose_niche_candidates
from app.services.discovery.candidate_ranker import rank_candidates_for_validation
from app.services.discovery.fast_validator import validate_candidates_fast
from app.worker.tasks import _get_lock_connection, _acquire_advisory_lock, _release_advisory_lock, _FULL_PIPELINE_LOCK_ID
from sqlalchemy import select, func, text
import json


def reset_discovery_tables(db):
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Backing up discovery tables to /app/backups/discovery_backup_{timestamp}/...")
    try:
        import os
        os.makedirs(f"/app/backups/discovery_backup_{timestamp}", exist_ok=True)
        conn = db.connection().connection
        with conn.cursor() as cur:
            for table in ["discovery_entity_relations", "niche_candidates", "discovery_entities", "raw_discovery_items", "discovery_entity_aliases", "niche_candidate_keywords"]:
                with open(f"/app/backups/discovery_backup_{timestamp}/{table}.csv", "wb") as f:
                    with cur.copy(f"COPY {table} TO STDOUT WITH CSV HEADER") as copy:
                        for data in copy:
                            f.write(data)
            
            # Backup keyword mappings
            with open(f"/app/backups/discovery_backup_{timestamp}/keywords_mapping.csv", "wb") as f:
                with cur.copy("COPY (SELECT id, source_niche_candidate_id FROM keywords WHERE source_niche_candidate_id IS NOT NULL) TO STDOUT WITH CSV HEADER") as copy:
                    for data in copy:
                        f.write(data)
            
        print("Backup complete.")
    except Exception as e:
        print(f"Backup failed: {e}. Aborting reset.")
        raise RuntimeError(f"Backup failed: {e}")
    
    print("Resetting discovery tables...")
    # Prevent destructive cascade into collected amazon data (keywords/search_runs)
    db.execute(text("UPDATE keywords SET source_niche_candidate_id = NULL WHERE source_niche_candidate_id IS NOT NULL"))
    
    db.execute(text("DELETE FROM niche_candidate_keywords"))
    db.execute(text("DELETE FROM discovery_entity_aliases"))
    db.execute(text("DELETE FROM discovery_entity_relations"))
    db.execute(text("DELETE FROM niche_candidates"))
    db.execute(text("DELETE FROM discovery_entities"))
    db.execute(text("DELETE FROM raw_discovery_items"))
    db.commit()
    
    return f"/app/backups/discovery_backup_{timestamp}"

def get_unprocessed_raw_count(db):
    return db.scalar(select(func.count()).select_from(RawDiscoveryItem).where(RawDiscoveryItem.status == 'new'))


def assert_metadata_coverage(db, catalog_source):
    print("Asserting metadata coverage...")
    import os
    csv_path = f"/data/discovery_seed_universes/micro_domains/{catalog_source}.csv"
    csv_rows = 0
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_rows = sum(1 for line in f) - 1  # exclude header
    
    raw_count = db.scalar(select(func.count()).select_from(RawDiscoveryItem).where(
        text("metadata_json->>'source' = :source")
    ).params(source=catalog_source))
            
    total = db.scalar(select(func.count()).select_from(DiscoveryEntity).where(
        text("metadata_json->>'source' = :source")
    ).params(source=catalog_source))
    
    macro_domain = db.scalar(select(func.count()).select_from(DiscoveryEntity).where(
        text("metadata_json->>'source' = :source AND metadata_json->>'macro_domain' IS NOT NULL AND metadata_json->>'macro_domain' != ''")
    ).params(source=catalog_source))
    
    audience_hint = db.scalar(select(func.count()).select_from(DiscoveryEntity).where(
        text("metadata_json->>'source' = :source AND metadata_json->>'audience_hint' IS NOT NULL AND metadata_json->>'audience_hint' != ''")
    ).params(source=catalog_source))
    
    format_hint = db.scalar(select(func.count()).select_from(DiscoveryEntity).where(
        text("metadata_json->>'source' = :source AND metadata_json->>'format_hint' IS NOT NULL AND metadata_json->>'format_hint' != ''")
    ).params(source=catalog_source))
    
    print(f"CSV rows: {csv_rows}")
    print(f"Raw items imported: {raw_count}")
    print(f"Total entities from {catalog_source}: {total}")
    print(f"Entities with macro_domain: {macro_domain}")
    print(f"Entities with audience_hint: {audience_hint}")
    print(f"Entities with format_hint: {format_hint}")
    
    if total == 0:
        raise RuntimeError("Catalog source not found or no entities extracted")
    if csv_rows > 0 and raw_count / csv_rows < 0.99:
        raise RuntimeError(f"Missing raw items: {raw_count}/{csv_rows} ({raw_count/csv_rows:.1%})")
    if total / raw_count < 0.95:
        raise RuntimeError(f"Excessive deduplication/collapse: {total} entities from {raw_count} raw items")
        
    if macro_domain / total < 0.95:
        raise RuntimeError(f"Insufficient macro-domain coverage: {macro_domain}/{total}")
    if audience_hint / total < 0.95:
        raise RuntimeError(f"Insufficient audience coverage: {audience_hint}/{total}")
    if format_hint / total < 0.95:
        raise RuntimeError(f"Insufficient format coverage: {format_hint}/{total}")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete existing discovery tables safely")
    parser.add_argument("--import-seeds", action="store_true", help="Trigger seed imports and catalog imports")
    parser.add_argument("--catalog-source", default="micro_domain_catalog_2k_de_v2", help="Default: micro_domain_catalog_2k_de_v2")
    parser.add_argument("--canonical-only", action="store_true", help="Skip variants")
    parser.add_argument("--bulk-file", type=str, help="Path to bulk seed file (e.g. data/discovery_seed_universes/bulk/...)")
    parser.add_argument("--bulk-limit", type=int, default=1000000, help="Limit for bulk importer")
    parser.add_argument("--dry-run", action="store_true", help="Print execution plan without making changes")
    args = parser.parse_args()

    print("Starting True Discovery V2 Full Rebuild at Scale...")

    if args.dry_run:
        print("\nDRY RUN ENABLED - Execution Plan:")
        print("1. Acquire PostgreSQL advisory lock")
        if args.reset:
            print("2. UPDATE keywords SET source_niche_candidate_id = NULL")
            print("3. DELETE FROM discovery_entity_relations, discovery_entities, niche_candidates, raw_discovery_items")
        if args.import_seeds:
            print("4. Call import_all_seed_universes(db)")
            print(f"5. Import /data/discovery_seed_universes/micro_domains/{args.catalog_source}.csv")
        print("6. Iteratively extract entities until raw queue is empty")
        print("7. Assert metadata coverage for catalog source")
        print("8. Compose canonical microdomain candidates")
        if not args.canonical_only:
            print("9. Build supplementary graph relations and domain-aware candidates")
        print("10. Rank candidates iteratively until new queue is exhausted")
        print("11. Fast-validate candidates iteratively until prevalidation_queued is exhausted")
        print("12. Release lock")
        sys.exit(0)
    
    lock_conn = _get_lock_connection()
    if not _acquire_advisory_lock(lock_conn, _FULL_PIPELINE_LOCK_ID):
        print("ERROR: Could not acquire discovery pipeline advisory lock. Another process is running.")
        lock_conn.close()
        sys.exit(1)
        
    db = SessionLocal()
    try:
        from app.api.routes.discovery_pipeline import get_discovery_overview
        print("\n--- Before Funnel ---")
        overview_before = get_discovery_overview(db)
        print(json.dumps(json.loads(overview_before.model_dump_json()), indent=2))
        
        backup_dir = None
        if args.reset:
            backup_dir = reset_discovery_tables(db)
                
        if args.import_seeds:
            print("\nImporting manifest seeds...")
            from app.services.discovery.source_registry import import_all_seed_universes
            import_all_seed_universes(db)
            db.commit()
            
            print("Importing structured micro-domain catalog...")
            import sys
            from import_micro_domain_catalog import main as import_micro_main
            
            old_argv = sys.argv
            sys.argv = ["import_micro_domain_catalog.py", "--file", f"/data/discovery_seed_universes/micro_domains/{args.catalog_source}.csv", "--source-name", args.catalog_source]
            try:
                import_micro_main()
            except SystemExit as exc:
                raise RuntimeError(f"Micro catalog importer exited with {exc.code}") from exc
            finally:
                sys.argv = old_argv
            
            if args.bulk_file:
                print("Importing bulk seed file...")
                from scripts.import_bulk_seed_file import main as import_bulk_main
                sys.argv = ["import_bulk_seed_file.py", "--file", args.bulk_file, "--limit", str(args.bulk_limit), "--batch-size", "5000", "--skip-lock"]
                try:
                    summary = import_bulk_main()
                except SystemExit as exc:
                    raise RuntimeError(f"Bulk importer exited with {exc.code}") from exc
                finally:
                    sys.argv = old_argv
                
                if summary:
                    # Assertions for bulk file
                    expected_target = args.bulk_limit
                    if summary["total_read"] < args.bulk_limit:
                        expected_target = summary["total_read"]
                    
                    processed = summary["total_inserted"] + summary["total_skipped"]
                    if processed < expected_target * 0.99:
                        raise RuntimeError(f"Bulk import processed {processed} (inserted+skipped) which is less than 99% of expected {expected_target}")
                    if summary["max_share"] > 0.015:
                        raise RuntimeError(f"Bulk import file domain imbalance: {summary['max_share']:.2%} exceeds 1.5%")
                    if summary.get("imported_slice_max_domain_share", 0) > 0.015:
                        raise RuntimeError(f"Bulk import slice domain imbalance: {summary['imported_slice_max_domain_share']:.2%} exceeds 1.5%")
                    bulk_count = db.scalar(select(func.count()).select_from(RawDiscoveryItem).where(RawDiscoveryItem.discovery_source_id == summary["source_id"]))
                    if bulk_count < expected_target * 0.99:
                        raise RuntimeError(f"Missing bulk raw items in database: {bulk_count}/{expected_target}")
                    print("Bulk metadata coverage verified.")
            
        print("\n--- Phase: Entity Extraction ---")
        iteration = 1
        while True:
            unprocessed = get_unprocessed_raw_count(db)
            if unprocessed == 0:
                print("Raw queue exhausted (0 unprocessed items).")
                break
                
            print(f"Iteration {iteration}: {unprocessed} raw items remain...")
            ext = extract_entities_from_raw_items(db, limit=2000)
            print(f"  Extracted: created={ext.created}, updated={ext.updated}, skipped={ext.skipped}")
            
            if ext.created == 0 and ext.updated == 0 and ext.skipped == 0:
                print("WARNING: Extraction made no progress but queue is not empty!")
                break
            iteration += 1

        print("\n--- Phase: Assert Metadata Coverage ---")
        assert_metadata_coverage(db, args.catalog_source)

        print("\n--- Phase: Canonical Composition ---")
        comp_canonical = compose_micro_domain_candidates(
            db, 
            limit=10000, 
            max_candidates_per_micro_domain=1, 
            max_micro_domains=10000, 
            source=args.catalog_source
        )
        print(f"  Canonical Candidates: created={comp_canonical.created}, skipped={comp_canonical.skipped_blocked}")
        
        if not args.canonical_only:
            print("\n--- Phase: Supplementary Graph Relations ---")
            rel = build_entity_relations(db, limit_per_rule=1000)
            print(f"  Relations: created={rel.created}, skipped={rel.skipped}")
            
            print("\n--- Phase: Graph/Domain-aware Candidate Composition ---")
            comp_domain = compose_domain_aware_candidates(db, limit=2000, max_candidates_per_domain=100)
            print(f"  Domain-Aware Candidates: created={comp_domain.created}, skipped={comp_domain.skipped_blocked}")
            
            comp_graph = compose_niche_candidates(db, limit=2000)
            print(f"  Graph Candidates: created={comp_graph.created}, skipped={comp_graph.skipped_blocked}")
            
        print("\n--- Phase: Ranking ---")
        iteration = 1
        while True:
            rank = rank_candidates_for_validation(db, limit=10000, min_score=70)
            print(f"  Iteration {iteration}: ranked={rank.ranked}, queued={rank.queued}, manual={rank.manual_review}, rejected={rank.rejected_pre_validation}")
            unranked = db.scalar(select(func.count()).select_from(NicheCandidate).where(NicheCandidate.status == 'new'))
            if unranked == 0 or rank.ranked == 0:
                break
            iteration += 1
        
        print("\n--- Phase: Fast Validation ---")
        iteration = 1
        while True:
            val = validate_candidates_fast(db, limit=10000)
            print(f"  Iteration {iteration}: processed={len(val)}")
            unvalidated = db.scalar(select(func.count()).select_from(NicheCandidate).where(NicheCandidate.status == 'prevalidation_queued'))
            if unvalidated == 0 or len(val) == 0:
                break
            iteration += 1

        print("\n--- After Funnel ---")
        overview_after = get_discovery_overview(db)
        print(json.dumps(json.loads(overview_after.model_dump_json()), indent=2))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: Rebuild failed: {e}")
        if 'args' in locals() and args.reset and backup_dir:
            print("Initiating automatic rollback...")
            if db:
                db.rollback()
                db.close()
                db = None
            import subprocess
            subprocess.run([sys.executable, "scripts/restore_discovery_backup.py", "--backup-dir", backup_dir, "--skip-lock"], check=True)
            print("Rollback completed successfully.")
        sys.exit(1)
    finally:
        if db:
            db.close()
        _release_advisory_lock(lock_conn, _FULL_PIPELINE_LOCK_ID)
        lock_conn.close()

if __name__ == "__main__":
    run()
