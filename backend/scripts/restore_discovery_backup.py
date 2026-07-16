import argparse
import csv
import os
import sys
from pathlib import Path

# Adjust path to import from app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@localhost:5432/kdp_pipeline")

from app.db.session import SessionLocal
from sqlalchemy import text

def restore_backup(backup_dir: str):
    path = Path(backup_dir)
    if not path.is_dir():
        print(f"ERROR: Backup directory {backup_dir} does not exist.")
        sys.exit(1)

    tables = [
        "discovery_entities",
        "raw_discovery_items",
        "niche_candidates",
        "discovery_entity_aliases",
        "discovery_entity_relations",
        "niche_candidate_keywords",
    ]

    db = SessionLocal()
    try:
        # Check if all files exist
        for table in tables:
            if not (path / f"{table}.csv").exists():
                print(f"ERROR: Missing backup file for {table} in {backup_dir}")
                sys.exit(1)
        if not (path / "keywords_mapping.csv").exists():
            print(f"ERROR: Missing backup file for keywords_mapping in {backup_dir}")
            sys.exit(1)

        print("Restoring discovery tables...")

        # We need to disable constraints or restore in order.
        # However, restoring via INSERT might conflict with existing data if not clean.
        # We assume the user is restoring onto a cleaned or partially cleaned state, or we TRUNCATE first.
        print("WARNING: This will drop current discovery tables before restore.")
        db.execute(text("UPDATE keywords SET source_niche_candidate_id = NULL WHERE source_niche_candidate_id IS NOT NULL"))
        db.execute(text("DELETE FROM niche_candidate_keywords"))
        db.execute(text("DELETE FROM discovery_entity_aliases"))
        db.execute(text("DELETE FROM discovery_entity_relations"))
        db.execute(text("DELETE FROM niche_candidates"))
        db.execute(text("DELETE FROM discovery_entities"))
        db.execute(text("DELETE FROM raw_discovery_items"))
        db.commit()

        for table in tables:
            csv_file = path / f"{table}.csv"
            print(f"Restoring {table} from {csv_file.name}...")
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                if not headers:
                    continue
                cols = ", ".join([f'"{h}"' for h in headers])
                params = ", ".join([f":{h}" for h in headers])
                sql = text(f"INSERT INTO {table} ({cols}) VALUES ({params})")
                
                batch = []
                for row in reader:
                    # Convert empty strings to None where applicable?
                    # CSV writer writes None as empty string. We must handle nulls.
                    # Since we used csv writer without special null handling, empty strings might be inserted.
                    row_dict = {h: (v if v != "" else None) for h, v in zip(headers, row)}
                    batch.append(row_dict)
                    if len(batch) >= 1000:
                        db.execute(sql, batch)
                        batch = []
                if batch:
                    db.execute(sql, batch)
            db.commit()

        print("Restoring keyword mappings...")
        kw_file = path / "keywords_mapping.csv"
        with open(kw_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers:
                batch = []
                sql = text("UPDATE keywords SET source_niche_candidate_id = :source_niche_candidate_id WHERE id = :id")
                for row in reader:
                    row_dict = {h: (v if v != "" else None) for h, v in zip(headers, row)}
                    batch.append(row_dict)
                    if len(batch) >= 1000:
                        db.execute(sql, batch)
                        batch = []
                if batch:
                    db.execute(sql, batch)
        db.commit()

        print(f"Successfully restored backup from {backup_dir}")

    except Exception as e:
        db.rollback()
        print(f"Restore failed: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore discovery tables from CSV backup.")
    parser.add_argument("--backup-dir", required=True, help="Path to the backup directory (e.g. /app/backups/discovery_backup_20260716_123456)")
    args = parser.parse_args()
    restore_backup(args.backup_dir)
