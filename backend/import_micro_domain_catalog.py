"""Import the micro-domain catalog CSV into the discovery pipeline."""
import argparse, csv, sys, os, time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@localhost:5432/kdp_pipeline")

import app.db.base  # noqa
from app.db.session import SessionLocal
from app.models.discovery_pipeline import DiscoverySource, RawDiscoveryItem
from sqlalchemy import select


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--source-name", default="micro_domain_catalog_2k_de_v2")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--batch-size", type=int, default=1000)
    args = p.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"File: {path} ({len(rows)} rows)")

    if args.dry_run:
        print("DRY RUN — showing first 5 rows:")
        for row in rows[:5]:
            print(f"  {row['macro_domain']} / {row['subdomain']} / {row['micro_domain']}")
        print("Dry run complete. No data written.")
        return

    db = SessionLocal()
    try:
        # Get or create source
        source = db.scalars(
            select(DiscoverySource).where(DiscoverySource.name == args.source_name)
        ).first()
        if not source:
            source = DiscoverySource(
                name=args.source_name,
                source_type="micro_domain_catalog",
                language="de",
                country="DE",
                is_active=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            print(f"Created source: id={source.id}")

        existing = set(db.scalars(
            select(RawDiscoveryItem.raw_text)
            .where(RawDiscoveryItem.discovery_source_id == source.id)
        ))
        total_inserted = 0
        total_skipped = 0
        batch = []
        started = time.time()

        for row in rows:
            micro = row["micro_domain"].strip()
            if micro in existing:
                total_skipped += 1
                continue

            existing.add(micro)
            metadata = {
                "macro_domain": row["macro_domain"].strip(),
                "subdomain": row["subdomain"].strip(),
                "micro_domain": micro,
                "audience_hint": row["audience_hint"].strip(),
                "problem_hint": row["problem_hint"].strip(),
                "format_hint": row["format_hint"].strip(),
                "risk_level": row["risk_level"].strip(),
                "priority": int(row["priority"].strip()) if row["priority"].strip().isdigit() else 50,
                "source": args.source_name,
                "entity_type_hint": "topic",
            }

            item = RawDiscoveryItem(
                discovery_source_id=source.id,
                raw_text=micro,
                language="de",
                country="DE",
                confidence=metadata["priority"],
                status="new",
                collected_at=datetime.now(UTC),
                metadata_json=metadata,
            )
            batch.append(item)

            if len(batch) >= args.batch_size:
                db.add_all(batch)
                db.commit()
                total_inserted += len(batch)
                elapsed = time.time() - started
                print(f"  Inserted {total_inserted:,} / skipped {total_skipped:,} ({total_inserted/elapsed:.0f}/s)")
                batch = []

        if batch:
            db.add_all(batch)
            db.commit()
            total_inserted += len(batch)

        elapsed = time.time() - started
        print(f"\nDone. Inserted: {total_inserted:,}, Skipped: {total_skipped:,} in {elapsed:.1f}s")

    finally:
        db.close()


if __name__ == "__main__":
    main()
