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
from app.services.discovery.domain_composer import compose_micro_domain_candidates
from app.services.discovery.niche_candidate_composer import compose_niche_candidates
from app.services.discovery.candidate_ranker import rank_candidates_for_validation
from app.services.discovery.fast_validator import validate_candidates_fast
from app.worker.tasks import _get_lock_connection, _acquire_advisory_lock, _release_advisory_lock, _FULL_PIPELINE_LOCK_ID
from sqlalchemy import select, func, text
import json


def reset_discovery_tables(db):
    print("Resetting discovery tables...")
    # Order matters for foreign keys
    db.execute(text("TRUNCATE TABLE discovery_entity_relations CASCADE"))
    db.execute(text("TRUNCATE TABLE discovery_entities CASCADE"))
    db.execute(text("TRUNCATE TABLE niche_candidates CASCADE"))
    db.execute(text("TRUNCATE TABLE raw_discovery_items CASCADE"))
    db.commit()


def get_unprocessed_raw_count(db):
    return db.scalar(select(func.count()).select_from(RawDiscoveryItem).where(RawDiscoveryItem.status == 'new'))


def assert_metadata_coverage(db, catalog_source):
    print("Asserting metadata coverage...")
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
    
    print(f"Total entities from {catalog_source}: {total}")
    print(f"Entities with macro_domain: {macro_domain}")
    print(f"Entities with audience_hint: {audience_hint}")
    print(f"Entities with format_hint: {format_hint}")
    
    if total > 0 and macro_domain == 0:
        raise RuntimeError("Metadata assertion failed: macro_domain coverage is 0. Wrong catalog loaded?")


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Truncate/archive existing discovery tables")
    parser.add_argument("--import-seeds", action="store_true", help="Trigger seed imports and catalog imports")
    parser.add_argument("--catalog-source", default="micro_domain_catalog_10k_de_v2", help="Default: micro_domain_catalog_10k_de_v2")
    parser.add_argument("--canonical-only", action="store_true", help="Skip variants")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit transactions")
    args = parser.parse_args()

    print("Starting True Discovery V2 Full Rebuild at Scale...")
    
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
        
        if args.reset:
            reset_discovery_tables(db)
            if args.dry_run:
                db.rollback()
                print("Dry run: Rolled back table reset.")
                
        if args.import_seeds:
            print("\nImporting manifest seeds...")
            import_all_seed_universes(db)
            print("Importing structured micro-domain catalog...")
            # Run the importer script
            cmd = [
                "python", 
                "import_micro_domain_catalog.py", 
                "--file", 
                "/data/discovery_seed_universes/micro_domains/micro_domain_catalog_10000_de_v2.csv", 
                "--source-name", 
                args.catalog_source
            ]
            if args.dry_run:
                cmd.append("--dry-run")
            subprocess.run(cmd, check=True, cwd="/app")
            
        print("\n--- Phase: Entity Extraction ---")
        iteration = 1
        while True:
            unprocessed = get_unprocessed_raw_count(db)
            if unprocessed == 0:
                print("Raw queue exhausted (0 unprocessed items).")
                break
                
            print(f"Iteration {iteration}: {unprocessed} raw items remain...")
            ext = extract_entities_from_raw_items(db, limit=2000)
            if args.dry_run:
                db.rollback()
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
        if args.dry_run:
            db.rollback()
        print(f"  Canonical Candidates: created={comp_canonical.created}, skipped={comp_canonical.skipped_blocked}")
        
        if not args.canonical_only:
            print("\n--- Phase: Supplementary Graph Relations ---")
            rel = build_entity_relations(db, limit_per_rule=1000)
            if args.dry_run:
                db.rollback()
            print(f"  Relations: created={rel.created}, skipped={rel.skipped}")
            
            print("\n--- Phase: Graph/Domain-aware Candidate Composition ---")
            comp_graph = compose_niche_candidates(db, limit=2000)
            if args.dry_run:
                db.rollback()
            print(f"  Graph Candidates: created={comp_graph.created}, skipped={comp_graph.skipped_blocked}")
            
        print("\n--- Phase: Ranking ---")
        rank = rank_candidates_for_validation(db, limit=10000, min_score=70)
        if args.dry_run:
            db.rollback()
        print(f"  Ranked: ranked={rank.ranked}, queued={rank.queued}, manual={rank.manual_review}, rejected={rank.rejected_pre_validation}")
        
        print("\n--- Phase: Fast Validation ---")
        val = validate_candidates_fast(db, limit=10000)
        if args.dry_run:
            db.rollback()
        print(f"  Validation: processed={len(val)}")

        print("\n--- After Funnel ---")
        overview_after = get_discovery_overview(db)
        print(json.dumps(json.loads(overview_after.model_dump_json()), indent=2))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: Rebuild failed: {e}")
        sys.exit(1)
    finally:
        db.close()
        _release_advisory_lock(lock_conn, _FULL_PIPELINE_LOCK_ID)
        lock_conn.close()

if __name__ == "__main__":
    run()
