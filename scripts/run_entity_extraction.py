"""Run entity extraction in batches until all raw items are processed."""
import sys, os, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline")

import app.db.base  # noqa: F401 — ensure all models are loaded for relationship resolution
from app.db.session import SessionLocal
from app.services.discovery.entity_extractor import extract_entities_from_raw_items

db = SessionLocal()
total_c, total_u, total_s = 0, 0, 0
batch = 0
start = time.time()
BATCH_SIZE = 5000

while True:
    result = extract_entities_from_raw_items(db, limit=BATCH_SIZE)
    total_c += result.created
    total_u += result.updated
    total_s += result.skipped
    batch += 1

    if result.created == 0 and result.updated == 0 and result.skipped == 0:
        break

    if batch % 10 == 0:
        elapsed = time.time() - start
        total_processed = total_c + total_u
        rate = batch * BATCH_SIZE / elapsed if elapsed > 0 else 0
        print(f"Batch {batch}: created={total_c} updated={total_u} skipped={total_s} ({rate:.0f}/s)")

elapsed = time.time() - start
total_processed = total_c + total_u
rate = total_processed / elapsed if elapsed > 0 else 0
print(f"DONE: {batch} batches, created={total_c}, updated={total_u}, skipped={total_s}, {elapsed:.1f}s ({rate:.0f}/s)")
db.close()
