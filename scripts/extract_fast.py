"""One-pass entity extraction — uses key-only lookups for speed."""
import sys, os, time
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / "backend"))
os.environ["DATABASE_URL"] = "postgresql+psycopg://kdp:kdp@postgres:5432/kdp_pipeline"

import app.db.base  # noqa
from app.db.session import SessionLocal
from sqlalchemy import select, text

db = SessionLocal()
start = time.time()

# Load existing entity keys as a set (lightweight — no full objects)
print("Loading existing entity keys...")
t0 = time.time()
existing_keys = set()
rows = db.execute(
    select(
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntity']).DiscoveryEntity.id,
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntity']).DiscoveryEntity.normalized_name,
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntity']).DiscoveryEntity.entity_type,
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntity']).DiscoveryEntity.language,
    )
).all()
for row in rows:
    key = f"{row[1]}|{row[2]}|{row[3]}"
    existing_keys.add((key, row[0]))  # (key, entity_id)
existing_keys_dict = {k: eid for k, eid in existing_keys}
print(f"Loaded {len(existing_keys_dict):,} entity keys in {time.time()-t0:.1f}s")

# Load existing aliases
print("Loading existing aliases...")
t0 = time.time()
known_aliases = set()
alias_rows = db.execute(
    select(
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntityAlias']).DiscoveryEntityAlias.entity_id,
        __import__('app.models.discovery_pipeline', fromlist=['DiscoveryEntityAlias']).DiscoveryEntityAlias.alias,
    )
).all()
for row in alias_rows:
    known_aliases.add((row[0], row[1]))
print(f"Loaded {len(known_aliases):,} aliases in {time.time()-t0:.1f}s")

# Count unprocessed
from app.models.discovery_pipeline import RawDiscoveryItem, DiscoveryEntity, DiscoveryEntityAlias
from app.services.discovery.entity_extractor import _infer_entity_type
from app.services.discovery.entity_normalizer import normalize_entity_name
from datetime import UTC, datetime

total_remaining = db.scalar(
    select(__import__('sqlalchemy', fromlist=['func']).func.count()).select_from(RawDiscoveryItem).where(RawDiscoveryItem.status == "new")
)
print(f"Unprocessed raw items: {total_remaining:,}")

# Process in large batches
BATCH = 10000
total_created = 0
total_updated = 0
total_skipped = 0
batch_num = 0

while True:
    batch_num += 1
    items = list(db.scalars(
        select(RawDiscoveryItem)
        .where(RawDiscoveryItem.status == "new")
        .order_by(RawDiscoveryItem.id.asc())
        .limit(BATCH)
    ))
    if not items:
        break

    new_entities = []
    for item in items:
        raw_text = item.raw_text.strip()
        if not raw_text or len(raw_text) < 2:
            item.status = "ignored"
            item.processed_at = item.collected_at
            total_skipped += 1
            continue

        entity_type = _infer_entity_type(raw_text, item.metadata_json)
        if entity_type is None:
            entity_type = "topic"

        normalized = normalize_entity_name(raw_text)
        if not normalized or len(normalized) < 2:
            item.status = "ignored"
            item.processed_at = item.collected_at
            total_skipped += 1
            continue

        key = f"{normalized}|{entity_type}|{item.language}"
        if key in existing_keys_dict:
            # Update existing
            eid = existing_keys_dict[key]
            db.execute(
                text("UPDATE discovery_entities SET source_count = COALESCE(source_count, 1) + 1, confidence = LEAST(1.0, confidence + 0.05) WHERE id = :eid"),
                {"eid": eid}
            )
            total_updated += 1
        else:
            # Create new
            new_entity = DiscoveryEntity(
                name=raw_text[:255],
                normalized_name=normalized,
                entity_type=entity_type,
                language=item.language,
                country=item.country,
                confidence=0.6,
                source_count=1,
                metadata_json=item.metadata_json,
            )
            db.add(new_entity)
            db.flush()
            existing_keys_dict[key] = new_entity.id
            new_entities.append((new_entity.id, raw_text[:255], item.language))
            total_created += 1

        item.status = "processed"
        item.processed_at = datetime.now(UTC)

    # Add aliases for new entities (bulk)
    for eid, alias_text, lang in new_entities:
        normalized_key = None
        # Check alias
        if alias_text.casefold() not in ("",):  # simplified check
            alias_key = (eid, alias_text)
            if alias_key not in known_aliases:
                db.add(DiscoveryEntityAlias(
                    entity_id=eid,
                    alias=alias_text,
                    language=lang,
                ))
                known_aliases.add(alias_key)

    db.commit()
    elapsed = time.time() - start
    processed = total_created + total_updated + total_skipped
    rate = processed / elapsed if elapsed > 0 else 0
    print(f"Batch {batch_num}: +{total_created} new, +{total_updated} upd, +{total_skipped} skip | {processed:,} total | {rate:.0f}/s")

elapsed = time.time() - start
print(f"\nDONE in {elapsed:.1f}s: created={total_created}, updated={total_updated}, skipped={total_skipped}")
db.close()
