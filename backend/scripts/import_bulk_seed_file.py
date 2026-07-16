"""Import bulk .csv.gz seed files in batches.

Features:
- Blocklist for old bad files
- Domain balance validation (max 1.5% per domain for 100-domain files)
- Source tracking via metadata
- Dry-run support
- Offset/limit pagination for staged imports
"""
import argparse, gzip, sys, os, time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@localhost:5432/kdp_pipeline")

from app.db.session import SessionLocal
from app.models.discovery_pipeline import DiscoverySource, RawDiscoveryItem
from sqlalchemy import select
from app.worker.tasks import _acquire_advisory_lock, _FULL_PIPELINE_LOCK_ID
import csv

# Files that must never be imported (old bad datasets)
BLOCKED_BULK_FILES: set[str] = {
    "discovery_seed_entities_1000000_de.csv.gz",
    "discovery_seed_entities_1000000_balanced_de.csv.gz",
}

# Only this file is allowed for the balanced 100-domain import
ALLOWED_100DOMAIN_FILE = "discovery_seed_entities_1000000_100domains_de.csv.gz"

# Maximum allowed share for any single domain (1.5%)
MAX_DOMAIN_SHARE = 0.015


def main():
    p = argparse.ArgumentParser(description="Bulk importer for seed universes")
    p.add_argument("--file", required=True)
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--batch-size", type=int, default=10000, help="Batch size for inserts")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source-name", default="LLM Balanced Seed Universe 1M 100 Domains")
    p.add_argument("--source-type", default="llm_bulk_seed_universe_balanced")
    p.add_argument("--skip-domain-check", action="store_true", help="Bypass the max domain share constraint")
    p.add_argument("--skip-lock", action="store_true", help="Do not try to acquire pipeline lock")
    args = p.parse_args()

    path = Path(args.file)
    filename = path.name

    # ---- Blocklist check ----
    if filename in BLOCKED_BULK_FILES:
        print(f"BLOCKED: {filename} is on the blocked file list and must not be imported.")
        print(f"  Reason: This file is known to cause domain imbalance (Pflege dominance etc).")
        print(f"  Use the 100-domain balanced file instead: {ALLOWED_100DOMAIN_FILE}")
        sys.exit(1)

    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    # ---- Header validation ----
    print(f"File: {path} ({path.stat().st_size:,} bytes)")
    fh = gzip.open(path, "rt", encoding="utf-8-sig")
    reader = csv.DictReader(fh)
    header = reader.fieldnames
    if not header:
        print("ERROR: Empty file or missing header")
        sys.exit(1)
        
    required = {"name", "entity_type", "priority"}
    missing = required - set(header)
    if missing:
        print(f"ERROR: missing columns: {missing}")
        sys.exit(1)
    print(f"Header valid: {header}")
    has_domain = "domain" in header
    print(f"Has domain column: {has_domain}")

    # ---- Row counting and domain validation (sample first 100K) ----
    print("Sampling rows for domain balance check...")
    domain_sample: dict[str, int] = {}
    total_sampled = 0
    for row in reader:
        total_sampled += 1
        if total_sampled > 100000:
            break
        if has_domain:
            domain = row.get("domain", "").strip()
            if domain:
                domain_sample[domain] = domain_sample.get(domain, 0) + 1
    fh.close()

    print(f"Sampled rows: {total_sampled:,}")
    if domain_sample:
        total_domains = len(domain_sample)
        max_domain = max(domain_sample.values()) if domain_sample else 0
        max_share = max_domain / total_sampled if total_sampled > 0 else 0
        print(f"Domains detected (in sample): {total_domains}")
        print(f"Max domain count (in sample): {max_domain}")
        print(f"Max domain share: {max_share:.2%}")

        if max_share > MAX_DOMAIN_SHARE and not args.skip_domain_check:
            print(f"ERROR: Domain imbalance detected! Max domain share {max_share:.2%} exceeds {MAX_DOMAIN_SHARE:.2%} threshold.")
            print(f"  This dataset is too domain-skewed. Import aborted.")
            print(f"  Use --skip-domain-check to bypass this validation (not recommended).")
            sys.exit(1)
    else:
        print("WARNING: No domain column found — skipping domain balance check.")

    # ---- Dry run ----
    if args.dry_run:
        print("\nDRY RUN — showing samples:")
        fh = gzip.open(path, "rt", encoding="utf-8-sig")
        fh.readline()  # skip header
        for i, line in enumerate(fh):
            if i >= 10:
                break
            print(f"  {line.strip()}")
        fh.close()
        print("\nDry run complete. No data written.")
        return

    print(f"\nImporting: limit={args.limit:,}, offset={args.offset:,}, batch-size={args.batch_size:,}")
    db = SessionLocal()
    
    if not args.skip_lock:
        if not _acquire_advisory_lock(db, _FULL_PIPELINE_LOCK_ID):
            print("ERROR: Could not acquire pipeline lock. Another import or pipeline rebuild is running.")
            sys.exit(1)
        
    try:
        # Get or create source
        source = db.scalars(
            select(DiscoverySource).where(DiscoverySource.name == args.source_name)
        ).first()
        if not source:
            source = DiscoverySource(
                name=args.source_name,
                source_type=args.source_type,
                language="de",
                country="DE",
                is_active=True,
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            print(f"Created source: id={source.id}, name={source.name}")
        else:
            print(f"Using existing source: id={source.id}, name={source.name}")

        # Preload existing raw_text for dedup (only from this source to keep it fast)
        existing = set(
            db.scalars(
                select(RawDiscoveryItem.raw_text).where(
                    RawDiscoveryItem.discovery_source_id == source.id
                )
            )
        )
        print(f"Existing raw items for this source: {len(existing):,}")

        total_read = 0
        total_inserted = 0
        total_skipped = 0
        batch: list[RawDiscoveryItem] = []
        domain_counts: dict[str, int] = {}
        etype_counts: dict[str, int] = {}
        started = time.time()

        fh = gzip.open(path, "rt", encoding="utf-8-sig")
        reader = csv.DictReader(fh)

        for row in reader:
            total_read += 1
            if total_read <= args.offset:
                continue
            if total_read > args.offset + args.limit:
                break

            name = row.get("name", "").strip()
            etype = row.get("entity_type", "topic").strip()
            priority = row.get("priority", "50").strip()
            domain = row.get("domain", "").strip() if has_domain else ""
            subdomain = row.get("subdomain", "").strip() if "subdomain" in header else ""

            if not name:
                continue

            if name in existing:
                total_skipped += 1
                continue

            existing.add(name)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            etype_counts[etype] = etype_counts.get(etype, 0) + 1

            metadata = {
                "bulk_file": path.name,
                "bulk_dataset": "llm_1m_100domains_balanced",
                "is_raw_combinatorial": True,
                "entity_type_hint": etype,
                "priority": int(priority) if priority.isdigit() else 50,
            }
            if domain:
                metadata["domain"] = domain
            if subdomain:
                metadata["subdomain"] = subdomain

            batch.append(RawDiscoveryItem(
                discovery_source_id=source.id,
                raw_text=name,
                language="de",
                country="DE",
                confidence=int(priority) if priority.isdigit() else 50,
                status="new",
                collected_at=datetime.now(UTC),
                metadata_json=metadata,
            ))

            if len(batch) >= args.batch_size:
                db.add_all(batch)
                db.commit()
                total_inserted += len(batch)
                elapsed = time.time() - started
                rate = total_inserted / elapsed if elapsed > 0 else 0
                print(f"  Inserted {total_inserted:,} / skipped {total_skipped:,} / read {total_read:,} ({rate:.0f} rows/s)")
                batch = []

        # Final batch
        if batch:
            db.add_all(batch)
            db.commit()
            total_inserted += len(batch)

        elapsed = time.time() - started
        print(f"\nDone. Imported: {total_inserted:,}, Skipped: {total_skipped:,} in {elapsed:.1f}s")
        print(f"Total rows read: {total_read:,}")
        if domain_counts:
            print(f"Domains: {len(domain_counts)}")
            top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for d, c in top_domains:
                print(f"  {d}: {c:,}")
        if etype_counts:
            print(f"Entity types: {dict(sorted(etype_counts.items()))}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
