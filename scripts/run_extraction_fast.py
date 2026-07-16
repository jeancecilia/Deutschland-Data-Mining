"""Fast entity extraction — loads entity cache once, processes in bulk."""
import sys, os, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline")

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.models.discovery_pipeline import DiscoveryEntity, DiscoveryEntityAlias, RawDiscoveryItem
from app.services.discovery.entity_extractor import extract_entities_from_raw_items

db = SessionLocal()
start = time.time()

# Process ALL remaining items in a single loop, reusing entity cache
total_c, total_u, total_s = 0, 0, 0
batch = 0
BATCH_SIZE = 10000

while True:
    result = extract_entities_from_raw_items(db, limit=BATCH_SIZE)
    total_c += result.created
    total_u += result.updated
    total_s += result.skipped
    batch += 1
    if result.created == 0 and result.updated == 0 and result.skipped == 0:
        break
    elapsed = time.time() - start
    processed = batch * BATCH_SIZE
    print(f"Batch {batch}: +{result.created} created, +{result.updated} updated | total entities ~{total_c} | {processed/elapsed:.0f}/s")

elapsed = time.time() - start
print(f"\nDONE: {batch} batches in {elapsed:.1f}s")
print(f"  created={total_c}, updated={total_u}, skipped={total_s}")
db.close()
