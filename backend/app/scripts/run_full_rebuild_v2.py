import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline")

import app.db.base
from app.db.session import SessionLocal
from app.services.discovery.entity_extractor import extract_entities_from_raw_items
from app.services.discovery.relation_builder import build_entity_relations
from app.services.discovery.niche_candidate_composer import compose_niche_candidates
from app.services.discovery.candidate_ranker import rank_candidates_for_validation
from app.services.discovery.fast_validator import validate_candidates_fast
import json

def run():
    db = SessionLocal()
    try:
        print("Starting Discovery V2 Full Rebuild at Scale...")
        iteration = 1
        while True:
            print(f"\n--- Iteration {iteration} ---")
            progress_made = False
            
            # Extract entities
            print("Extracting entities...")
            ext = extract_entities_from_raw_items(db, limit=1000)
            if ext.created > 0 or ext.updated > 0:
                progress_made = True
            print(f"  Entities: created={ext.created}, updated={ext.updated}, skipped={ext.skipped}")
            
            # Build relations
            print("Building relations...")
            rel = build_entity_relations(db, limit_per_rule=200)
            if rel.created > 0:
                progress_made = True
            print(f"  Relations: created={rel.created}, skipped={rel.skipped}")
            
            # Compose candidates
            print("Composing candidates...")
            comp = compose_niche_candidates(db, limit=2000)
            if comp.created > 0:
                progress_made = True
            print(f"  Candidates: created={comp.created}, skipped={comp.skipped_blocked}")
            
            # Rank candidates
            print("Ranking candidates...")
            rank = rank_candidates_for_validation(db, limit=5000, min_score=60)
            if rank.ranked > 0:
                progress_made = True
            print(f"  Ranked: ranked={rank.ranked}, queued={rank.queued}, manual={rank.manual_review}, rejected={rank.rejected_pre_validation}")
            
            # Fast Validate
            print("Validating candidates...")
            val = validate_candidates_fast(db, limit=1000)
            if len(val) > 0:
                progress_made = True
            print(f"  Validation: processed={len(val)}")
            
            if not progress_made:
                print("\nNo more progress can be made. Pipeline has exhausted the queue.")
                break
                
            iteration += 1

        print("\nRebuild complete! Fetching final pipeline overview:")
        from app.api.routes.discovery_pipeline import get_discovery_overview
        overview = get_discovery_overview(db)
        print(json.dumps(json.loads(overview.model_dump_json()), indent=2))
        
    finally:
        db.close()

if __name__ == "__main__":
    run()
