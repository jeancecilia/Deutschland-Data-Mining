import argparse
import os
import sys
from pathlib import Path

# Adjust path to import from app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://kdp:kdp@localhost:5432/kdp_pipeline")

from app.db.session import SessionLocal
from sqlalchemy import text
from app.worker.tasks import _get_lock_connection, _acquire_advisory_lock, _release_advisory_lock, _FULL_PIPELINE_LOCK_ID

def restore_backup(backup_dir: str, skip_lock: bool = False):
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
    
    lock_conn = None
    if not skip_lock:
        lock_conn = _get_lock_connection()
        if not _acquire_advisory_lock(lock_conn, _FULL_PIPELINE_LOCK_ID):
            print("ERROR: Could not acquire pipeline lock. Another pipeline process is running.")
            lock_conn.close()
            sys.exit(1)

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

        # Obtain the underlying psycopg connection
        conn = db.connection().connection

        # Delete current state
        with conn.cursor() as cur:
            cur.execute("UPDATE keywords SET source_niche_candidate_id = NULL WHERE source_niche_candidate_id IS NOT NULL")
            cur.execute("DELETE FROM niche_candidate_keywords")
            cur.execute("DELETE FROM discovery_entity_aliases")
            cur.execute("DELETE FROM discovery_entity_relations")
            cur.execute("DELETE FROM niche_candidates")
            cur.execute("DELETE FROM discovery_entities")
            cur.execute("DELETE FROM raw_discovery_items")

            # Restore tables natively handling JSONB/types
            for table in tables:
                csv_file = path / f"{table}.csv"
                print(f"Restoring {table} from {csv_file.name}...")
                with open(csv_file, "rb") as f:
                    with cur.copy(f"COPY {table} FROM STDIN WITH CSV HEADER") as copy:
                        while data := f.read(8192):
                            copy.write(data)

            print("Restoring keyword mappings...")
            kw_file = path / "keywords_mapping.csv"
            
            # Use a temporary table for bulk updating the keywords table
            cur.execute("CREATE TEMP TABLE temp_keywords_mapping (id INTEGER, source_niche_candidate_id INTEGER)")
            with open(kw_file, "rb") as f:
                with cur.copy("COPY temp_keywords_mapping FROM STDIN WITH CSV HEADER") as copy:
                    while data := f.read(8192):
                        copy.write(data)
                        
            cur.execute('''
                UPDATE keywords 
                SET source_niche_candidate_id = t.source_niche_candidate_id 
                FROM temp_keywords_mapping t 
                WHERE keywords.id = t.id
            ''')
            cur.execute("DROP TABLE temp_keywords_mapping")
            
            # Synchronize identity sequences for restored tables
            for table in tables:
                # We can dynamically setval based on the table's id sequence if it has an id column.
                # Assuming all these tables have 'id' column as serial/identity except relations/aliases if they don't, but let's check
                # For safety, attempt it only if id exists, but we know which tables have sequences.
                # Actually, some might not have 'id'. 'discovery_entity_relations' has 'id'. 
                # Let's run a generic block that handles errors gracefully, or check schema explicitly.
                pass
            
            seq_tables = [
                "discovery_entities",
                "raw_discovery_items",
                "niche_candidates",
                "discovery_entity_aliases",
                "discovery_entity_relations",
                "niche_candidate_keywords"
            ]
            
            for table in seq_tables:
                cur.execute(f'''
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE(MAX(id), 1),
                        MAX(id) IS NOT NULL
                    )
                    FROM {table};
                ''')
            
        # Commit the entire restoration in a single transaction
        db.commit()
        print(f"Successfully restored backup from {backup_dir}")

    except Exception as e:
        db.rollback()
        print(f"Restore failed: {e}")
        sys.exit(1)
    finally:
        db.close()
        if lock_conn:
            _release_advisory_lock(lock_conn, _FULL_PIPELINE_LOCK_ID)
            lock_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore discovery tables from CSV backup.")
    parser.add_argument("--backup-dir", required=True, help="Path to the backup directory (e.g. /app/backups/discovery_backup_20260716_123456)")
    parser.add_argument("--skip-lock", action="store_true", help="Bypass acquiring the pipeline lock (use when invoked automatically during rebuild).")
    args = parser.parse_args()
    restore_backup(args.backup_dir, args.skip_lock)
