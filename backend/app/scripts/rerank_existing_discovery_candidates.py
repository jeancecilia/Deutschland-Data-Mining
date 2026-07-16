#!/usr/bin/env python
import argparse
import time
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from app.core.config import settings
from app.models.discovery_pipeline import NicheCandidate, DiscoveryEntity
from app.services.discovery.candidate_quality_gate import evaluate_candidate_quality

def get_engine():
    return create_engine(
        str(settings.SQLALCHEMY_DATABASE_URI),
        pool_pre_ping=True,
        pool_size=5,
    )

def main():
    parser = argparse.ArgumentParser(description="Retroactively apply the new Candidate Quality Gate to the 1M-row universe.")
    parser.add_argument("--batch-size", type=int, default=10000, help="Number of rows per batch")
    parser.add_argument("--limit", type=int, default=None, help="Max total rows to process")
    args = parser.parse_args()

    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print("Loading entity map...")
    with SessionLocal() as db:
        entity_map: dict[int, str] = {}
        for e in db.scalars(select(DiscoveryEntity)):
            entity_map[e.id] = e.name
    print(f"Loaded {len(entity_map)} entities.")

    with SessionLocal() as db:
        # We process all candidates that are not already explicitly approved or fast_validated
        # (Since we want to re-eval the universe, we can re-eval 'new', 'prevalidation_queued', etc.)
        status_filter = ("new", "prevalidation_queued", "prevalidation_manual_review", "needs_manual_review")
        
        query = select(NicheCandidate.id).where(NicheCandidate.status.in_(status_filter))
        if args.limit:
            query = query.limit(args.limit)
            
        candidate_ids = db.scalars(query).all()
        
    total = len(candidate_ids)
    print(f"Found {total} candidates to re-evaluate.")
    
    processed = 0
    rejected = 0
    blocked = 0
    updated = 0
    
    start_time = time.time()
    
    with SessionLocal() as db:
        for i in range(0, total, args.batch_size):
            batch_ids = candidate_ids[i:i + args.batch_size]
            candidates = db.scalars(
                select(NicheCandidate).where(NicheCandidate.id.in_(batch_ids))
            ).all()
            
            for candidate in candidates:
                topic_name = entity_map.get(candidate.main_topic_entity_id) if candidate.main_topic_entity_id else None
                audience_name = entity_map.get(candidate.audience_entity_id) if candidate.audience_entity_id else None
                problem_name = entity_map.get(candidate.problem_entity_id) if candidate.problem_entity_id else None
                format_name = entity_map.get(candidate.format_entity_id) if candidate.format_entity_id else None
                
                meta = candidate.source_entities or {}
                
                gate_result = evaluate_candidate_quality(
                    candidate_name=candidate.candidate_name,
                    topic_name=topic_name,
                    audience_name=audience_name,
                    problem_name=problem_name,
                    format_name=format_name,
                    meta=meta,
                )
                
                candidate.fast_validation_score = gate_result.total_score
                candidate.compatibility_score = gate_result.compatibility_score
                candidate.risk_category = gate_result.risk_category
                candidate.risk_reason_codes = gate_result.reason_codes
                candidate.recommendation_label = gate_result.recommendation
                
                # Update status if it was hard-blocked or rejected by the new gate
                if not gate_result.allowed:
                    if gate_result.recommendation == "BLOCKED":
                        candidate.status = "blocked"
                        candidate.rejection_reason = gate_result.reason
                        blocked += 1
                    else:
                        candidate.status = "rejected"
                        candidate.rejection_reason = gate_result.reason
                        rejected += 1
                else:
                    # If it was allowed, we keep its status but update scores.
                    # Or if it was already in a queue, maybe we should push it back to "new" to be ranked?
                    # Let's just update the scores so the ranker will pick them up correctly on next run if they are "new".
                    updated += 1
                    
                processed += 1
                
            db.commit()
            
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            print(f"Processed {processed}/{total} ({rate:.1f} rows/s). Rejected: {rejected}, Blocked: {blocked}, Updated: {updated}")
            
    print("\n--- Reranking Complete ---")
    print(f"Total Processed: {processed}")
    print(f"Total Rejected:  {rejected}")
    print(f"Total Blocked:   {blocked}")
    print(f"Total Updated:   {updated}")

if __name__ == "__main__":
    main()
