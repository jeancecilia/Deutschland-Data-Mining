"""Diagnose entity type and domain distribution."""
import sys, os
sys.path.insert(0, "/app")
import app.db.base
from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== Entity types ===")
rows = db.execute(text(
    "SELECT entity_type, COUNT(*) FROM discovery_entities GROUP BY entity_type ORDER BY COUNT(*) DESC LIMIT 20"
)).all()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

print("\n=== Raw item entity_type_hint ===")
rows = db.execute(text(
    "SELECT metadata_json->>'entity_type_hint' as hint, COUNT(*) "
    "FROM raw_discovery_items WHERE metadata_json->>'entity_type_hint' IS NOT NULL "
    "GROUP BY hint ORDER BY COUNT(*) DESC LIMIT 10"
)).all()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

print("\n=== Raw item domains (top 15) ===")
rows = db.execute(text(
    "SELECT metadata_json->>'domain' as domain, COUNT(*) "
    "FROM raw_discovery_items WHERE metadata_json->>'domain' IS NOT NULL "
    "GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 15"
)).all()
for r in rows:
    print(f"  {r[0]}: {r[1]:,}")

print("\n=== Unique domains count ===")
cnt = db.scalar(text(
    "SELECT COUNT(DISTINCT metadata_json->>'domain') FROM raw_discovery_items WHERE metadata_json->>'domain' IS NOT NULL"
))
print(f"  {cnt}")

print("\n=== Sample raw item ===")
row = db.execute(text(
    "SELECT raw_text, metadata_json, status FROM raw_discovery_items WHERE metadata_json->>'domain' IS NOT NULL LIMIT 1"
)).first()
if row:
    print(f"  text: {row[0]}")
    print(f"  metadata: {row[1]}")
    print(f"  status: {row[2]}")

print("\n=== Sample entity with source_count > 1 ===")
row = db.execute(text(
    "SELECT name, entity_type, normalized_name, confidence, source_count, metadata_json "
    "FROM discovery_entities WHERE source_count > 1 LIMIT 5"
)).all()
for r in row:
    print(f"  {r[0]} | type={r[1]} | norm={r[2]} | conf={r[3]} | src_count={r[4]}")

db.close()
