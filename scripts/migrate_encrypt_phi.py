#!/usr/bin/env python3
"""
migrate_encrypt_phi.py — AG-8 PHI Field-Level Encryption Migration

Encrypts existing plaintext PHI data in-place and populates hash columns.
Idempotent: safely skips already-encrypted rows.

Workflow
--------
1. Adds hash columns (if they don't exist) via ALTER TABLE
2. Reads each table's plaintext PHI rows
3. Encrypts values with Fernet and computes HMAC-SHA256 hashes
4. Updates rows in batches

Usage
-----
    # Dry-run (shows counts, no writes)
    python scripts/migrate_encrypt_phi.py --dry-run

    # Real migration
    python scripts/migrate_encrypt_phi.py

    # With explicit database URL
    python scripts/migrate_encrypt_phi.py --db-url postgresql://user:pass@host/db

Requires
--------
    ENCRYPTION_KEY environment variable (Fernet key or passphrase)
"""

import argparse
import os
import sys
import logging
from datetime import datetime

# Allow running from project root or scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dental_agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text, inspect
from encryption import encrypt_field, phi_hash, is_encryption_configured

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema: table → (phi_columns, hash_column_definitions)
# hash_column_definitions: list of (hash_col_name, source_col_name, nullable)
# ---------------------------------------------------------------------------
MIGRATION_SPEC = {
    "leads": {
        "phi_cols": ["name", "phone", "email"],
        "hash_cols": [
            ("phone_hash", "phone", False),
            ("email_hash", "email", True),
        ],
    },
    "patients": {
        "phi_cols": ["first_name", "last_name", "phone", "email", "insurance_id"],
        "hash_cols": [
            ("phone_hash", "phone", False),
            ("email_hash", "email", True),
        ],
    },
    "inbound_calls": {
        "phi_cols": ["from_number", "caller_name"],
        "hash_cols": [
            ("from_number_hash", "from_number", False),
        ],
    },
    "appointments": {
        "phi_cols": ["patient_name", "patient_phone", "patient_email"],
        "hash_cols": [
            ("patient_phone_hash", "patient_phone", True),
        ],
    },
    "patient_recalls": {
        "phi_cols": ["patient_name", "patient_phone", "patient_email"],
        "hash_cols": [
            ("patient_phone_hash", "patient_phone", False),
        ],
    },
}

BATCH_SIZE = 500


def _is_encrypted(value: str) -> bool:
    """Heuristic: Fernet tokens are base64 starting with 'gAAAAA'."""
    if not value:
        return False
    return value.startswith("gAAAAA") and len(value) > 80


def _add_hash_columns(engine, table: str, hash_cols: list, dry_run: bool):
    """Add hash columns if they don't exist."""
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns(table)}

    with engine.begin() as conn:
        for col_name, _src, nullable in hash_cols:
            if col_name not in existing:
                null_clause = "" if nullable else " NOT NULL DEFAULT ''"
                sql = f'ALTER TABLE {table} ADD COLUMN {col_name} VARCHAR{null_clause}'
                if dry_run:
                    logger.info(f"  [DRY-RUN] Would run: {sql}")
                else:
                    conn.execute(text(sql))
                    logger.info(f"  Added column {table}.{col_name}")
            else:
                logger.info(f"  Column {table}.{col_name} already exists")

    # Add indexes on hash columns
    with engine.begin() as conn:
        for col_name, _src, _nullable in hash_cols:
            idx_name = f"ix_{table}_{col_name}"
            # Check if index exists (SQLite compatible)
            try:
                existing_indexes = {idx["name"] for idx in inspector.get_indexes(table)}
                if idx_name in existing_indexes:
                    logger.info(f"  Index {idx_name} already exists")
                    continue
            except Exception:
                pass

            sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({col_name})"
            if dry_run:
                logger.info(f"  [DRY-RUN] Would run: {sql}")
            else:
                conn.execute(text(sql))
                logger.info(f"  Created index {idx_name}")


def _migrate_table(engine, table: str, spec: dict, dry_run: bool) -> dict:
    """Migrate a single table. Returns stats dict."""
    phi_cols = spec["phi_cols"]
    hash_cols = spec["hash_cols"]
    stats = {"total": 0, "encrypted": 0, "skipped": 0, "errors": 0}

    # Build SELECT
    select_cols = ["id"] + phi_cols
    select_sql = f"SELECT {', '.join(select_cols)} FROM {table}"

    with engine.begin() as conn:
        rows = conn.execute(text(select_sql)).fetchall()
        stats["total"] = len(rows)

        for row in rows:
            row_id = row[0]
            row_dict = dict(zip(select_cols, row))

            # Check if already encrypted (heuristic on first PHI col)
            first_phi_val = row_dict.get(phi_cols[0])
            if first_phi_val and _is_encrypted(first_phi_val):
                stats["skipped"] += 1
                continue

            try:
                # Build UPDATE SET clauses
                updates = {}
                for col in phi_cols:
                    val = row_dict.get(col)
                    if val is not None:
                        updates[col] = encrypt_field(str(val))
                    else:
                        updates[col] = None

                # Compute hashes
                for hash_col, src_col, _nullable in hash_cols:
                    src_val = row_dict.get(src_col)
                    updates[hash_col] = phi_hash(src_val) if src_val else ""

                if dry_run:
                    stats["encrypted"] += 1
                    continue

                # Execute UPDATE
                set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
                update_sql = f"UPDATE {table} SET {set_clauses} WHERE id = :id"
                updates["id"] = row_id
                conn.execute(text(update_sql), updates)
                stats["encrypted"] += 1

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"  Error encrypting {table} id={row_id}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Encrypt existing PHI data in database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--db-url", help="Database URL (default: DATABASE_URL env var)")
    args = parser.parse_args()

    db_url = args.db_url or os.getenv("DATABASE_URL", "sqlite:///dental_agent.db")

    if not is_encryption_configured():
        logger.error("ENCRYPTION_KEY not set. Cannot migrate without encryption key.")
        sys.exit(1)

    logger.info(f"{'DRY RUN — ' if args.dry_run else ''}PHI Encryption Migration")
    logger.info(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    logger.info(f"Started: {datetime.utcnow().isoformat()}")
    logger.info("")

    engine = create_engine(db_url)

    total_stats = {"total": 0, "encrypted": 0, "skipped": 0, "errors": 0}

    for table, spec in MIGRATION_SPEC.items():
        logger.info(f"=== {table} ===")

        # Check if table exists
        inspector = inspect(engine)
        if table not in inspector.get_table_names():
            logger.info(f"  Table {table} does not exist — skipping")
            continue

        # Add hash columns
        _add_hash_columns(engine, table, spec["hash_cols"], args.dry_run)

        # Migrate data
        stats = _migrate_table(engine, table, spec, args.dry_run)

        for k in total_stats:
            total_stats[k] += stats[k]

        logger.info(
            f"  Rows: {stats['total']}  Encrypted: {stats['encrypted']}  "
            f"Skipped: {stats['skipped']}  Errors: {stats['errors']}"
        )
        logger.info("")

    logger.info("=== SUMMARY ===")
    logger.info(f"Total rows:  {total_stats['total']}")
    logger.info(f"Encrypted:   {total_stats['encrypted']}")
    logger.info(f"Skipped:     {total_stats['skipped']} (already encrypted)")
    logger.info(f"Errors:      {total_stats['errors']}")

    if total_stats["errors"] > 0:
        logger.warning("Some rows failed — re-run migration after fixing errors")
        sys.exit(1)

    logger.info("Migration complete." + (" (DRY RUN)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
