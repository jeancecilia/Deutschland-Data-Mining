"""Import bulk .csv.gz seed files in batches."""
import argparse, gzip, sys, os, time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@localhost:5432/kdp_pipeline")

from app.db.session import SessionLocal
from app.models.discovery_pipeline import DiscoverySource, RawDiscoveryItem, DiscoveryEntity
from sqlalchemy import select


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--batch-size", type=int, default=1000)
    p.add_argument("--limit", type=int, default=10000)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source-name", default="LLM Bulk Seed Universe 1M")
    p.add_argument("--max-per-domain", type=int, default=0)
    p.add_argument("--max-per-entity-type", type=int, default=0)
    p.add_argument("--entity-type", default="")
    p.add_argument("--domain", default="")
    args = p.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    # Peek at file
    print(f"File: {path} ({path.stat().st_size:,} bytes)")
    fh = gzip.open(path, "rt", encoding="utf-8-sig")
    header = fh.readline().strip()
    required = {"name", "entity_type", "priority"}
    cols = [c.strip() for c in header.split(",")]
    missing = required - set(cols)
    if missing:
        print(f"ERROR: missing columns: {missing}")
        sys.exit(1)
    print(f"Header valid: {header}")

    # Count rows
    est_rows = 0
    for _ in fh:
        est_rows += 1
        if est_rows >= 100000:
            break
    fh.close()
    print(f"Estimated rows (sampled): {est_rows}+")

    if args.dry_run:
        print("DRY RUN — showing samples:")
        fh = gzip.open(path, "rt", encoding="utf-8-sig")
        fh.readline()
        for i, line in enumerate(fh):
            if i >= 10:
                break
            print(f"  {line.strip()}")
        fh.close()
        print("Dry run complete. No data written.")
        return

    # Import
    db = SessionLocal()
    try:
        source = db.scalars(
            select(DiscoverySource).where(DiscoverySource.name == args.source_name)
        ).first()
        if not source:
            source = DiscoverySource(
                name=args.source_name,
                source_type="llm_bulk_seed_universe",
                language="de",
                country="DE",
                is_active=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)

        existing = set(db.scalars(select(RawDiscoveryItem.raw_text)))
        total_read = 0
        total_inserted = 0
        total_skipped = 0
        batch = []
        domain_counts = {}
        etype_counts = {}
        started = time.time()

        fh = gzip.open(path, "rt", encoding="utf-8-sig")
        fh.readline()  # skip header
        col_map = {c.strip(): i for i, c in enumerate(cols)}

        for line in fh:
            total_read += 1
            if total_read <= args.offset:
                continue
            if total_read > args.offset + args.limit:
                break

            parts = line.strip().split(",")
            name = parts[col_map.get("name", 0)].strip()
            etype = parts[col_map.get("entity_type", 1)].strip()
            priority = parts[col_map.get("priority", 2)].strip() or "50"
            domain = parts[col_map.get("domain", 3)].strip() if len(parts) > 3 else ""
            subdomain = parts[col_map.get("subdomain", 4)].strip() if len(parts) > 4 else ""

            if not name:
                continue

            # Filters
            if args.entity_type and etype != args.entity_type:
                continue
            if args.domain and domain != args.domain:
                continue
            if args.max_per_domain and domain_counts.get(domain, 0) >= args.max_per_domain:
                continue
            if args.max_per_entity_type and etype_counts.get(etype, 0) >= args.max_per_entity_type:
                continue

            if name in existing:
                total_skipped += 1
                continue

            existing.add(name)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            etype_counts[etype] = etype_counts.get(etype, 0) + 1

            batch.append(RawDiscoveryItem(
                discovery_source_id=source.id,
                raw_text=name,
                language="de",
                country="DE",
                confidence=int(priority) if priority.isdigit() else 50,
                status="new",
                collected_at=datetime.now(UTC),
                metadata_json={
                    "bulk_file": path.name,
                    "bulk_dataset": "llm_1m_de",
                    "is_raw_combinatorial": True,
                    "entity_type_hint": etype,
                    "priority": int(priority) if priority.isdigit() else 50,
                },
            ))

            if len(batch) >= args.batch_size:
                db.add_all(batch)
                db.commit()
                total_inserted += len(batch)
                print(f"  Inserted {total_inserted:,} / skipped {total_skipped:,} (read {total_read:,})")
                batch = []

        if batch:
            db.add_all(batch)
            db.commit()
            total_inserted += len(batch)

        elapsed = time.time() - started
        print(f"\nDone. Inserted: {total_inserted:,}, Skipped: {total_skipped:,}, Read: {total_read:,}")
        print(f"Duration: {elapsed:.1f}s ({total_inserted/elapsed:.0f} rows/s)")
        print(f"Domain distribution: {dict(sorted(domain_counts.items()))}")
        print(f"Entity type distribution: {dict(sorted(etype_counts.items()))}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
