"""Export all niche candidates as CSV."""
import app.db.base, csv, sys
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
rows = db.execute(text(
    "SELECT nc.candidate_name, nc.normalized_name, nc.status, "
    "nc.fast_validation_score, nc.recommendation_label, nc.risk_category, "
    "nc.book_class_guess, nc.confidence, "
    "COALESCE(de_t.name,'') as topic, COALESCE(de_a.name,'') as audience, "
    "COALESCE(de_p.name,'') as problem, "
    "nc.source_entities->>'domain' as domain, nc.generation_template "
    "FROM niche_candidates nc "
    "LEFT JOIN discovery_entities de_t ON nc.main_topic_entity_id = de_t.id "
    "LEFT JOIN discovery_entities de_a ON nc.audience_entity_id = de_a.id "
    "LEFT JOIN discovery_entities de_p ON nc.problem_entity_id = de_p.id "
    "ORDER BY nc.fast_validation_score DESC NULLS LAST"
)).fetchall()

with open("/app/exported_candidates.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["candidate_name","normalized_name","status","score","label",
                     "risk_category","book_class","confidence","topic","audience",
                     "problem","domain","template"])
    for r in rows:
        writer.writerow(r)

print(f"Exported {len(rows)} candidates to /app/exported_candidates.csv")
db.close()
