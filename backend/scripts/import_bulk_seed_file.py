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
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--batch-size", type=int, default=5000)
    p.add_argument("--limit", type=int, default=10000)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source-name", default="LLM Balanced Seed Universe 1M 100 Domains")
    p.add_argument("--source-type", default="llm_bulk_seed_universe_balanced")
    p.add_argument("--skip-domain-check", action="store_true",
                   help="Skip domain balance validation (not recommended)")
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
    header = fh.readline().strip()
    required = {"name", "entity_type", "priority"}
    cols = [c.strip() for c in header.split(",")]
    missing = required - set(cols)
    if missing:
        print(f"ERROR: missing columns: {missing}")
        sys.exit(1)
    print(f"Header valid: {header}")
    extra_cols = [c for c in cols if c not in required]
    has_domain = "domain" in extra_cols
    print(f"Extra columns: {extra_cols}")
    print(f"Has domain column: {has_domain}")

    # ---- Row counting and domain validation (sample first 100K) ----
    print("Sampling rows for domain balance check...")
    domain_sample: dict[str, int] = {}
    total_sampled = 0
    for line in fh:
        total_sampled += 1
        if total_sampled > 100000:
            break
        if has_domain:
            parts = line.strip().split(",")
            col_map = {c.strip(): i for i, c in enumerate(cols)}
            domain_idx = col_map.get("domain")
            if domain_idx is not None and domain_idx < len(parts):
                domain = parts[domain_idx].strip()
                domain_sample[domain] = domain_sample.get(domain, 0) + 1
    fh.close()

    print(f"Sampled rows: {total_sampled:,}")
    if domain_sample:
        total_domains = len(domain_sample)
        max_domain = max(domain_sample.values()) if domain_sample else 0
        # Estimate total rows from file size (rough: ~60 bytes/row uncompressed, ~4-5x compression)
        est_total_rows = int(path.stat().st_size * 180)  # rough bytes → rows for gz
        est_total_rows = max(est_total_rows, total_sampled)  # at least what we sampled
        max_share = max_domain / est_total_rows if est_total_rows > 0 else 0
        print(f"Domains detected (in sample): {total_domains}")
        print(f"Max domain count (in sample): {max_domain}")
        print(f"Estimated total rows: {est_total_rows:,}")
        print(f"Estimated max domain share: {max_share:.2%}")

        if max_share > MAX_DOMAIN_SHARE and not args.skip_domain_check:
            # Double-check with a larger sample if we're unsure
            if est_total_rows < 500000:
                print(f"WARNING: Low estimated total — domain share may be inaccurate.")
            else:
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

    # ---- Import ----
    print(f"\nImporting: limit={args.limit:,}, offset={args.offset:,}, batch-size={args.batch_size:,}")
    db = SessionLocal()
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
        fh.readline()  # skip header
        col_map = {c.strip(): i for i, c in enumerate(cols)}
        name_idx = col_map.get("name", 0)
        etype_idx = col_map.get("entity_type", 1)
        priority_idx = col_map.get("priority", 2)
        domain_idx = col_map.get("domain", 3) if has_domain else None
        subdomain_idx = col_map.get("subdomain", 4) if len(cols) > 4 else None

        for line in fh:
            total_read += 1
            if total_read <= args.offset:
                continue
            if total_read > args.offset + args.limit:
                break

            parts = line.strip().split(",")
            name = parts[name_idx].strip() if name_idx < len(parts) else ""
            etype = parts[etype_idx].strip() if etype_idx < len(parts) else "topic"
            priority = parts[priority_idx].strip() if priority_idx < len(parts) else "50"
            domain = parts[domain_idx].strip() if domain_idx is not None and domain_idx < len(parts) else ""
            subdomain = parts[subdomain_idx].strip() if subdomain_idx is not None and subdomain_idx < len(parts) else ""

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
        rate = total_inserted / elapsed if elapsed > 0 else 0
        print(f"\nDone. Inserted: {total_inserted:,}, Skipped: {total_skipped:,}, Read: {total_read:,}")
        print(f"Duration: {elapsed:.1f}s ({rate:.0f} rows/s)")
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
