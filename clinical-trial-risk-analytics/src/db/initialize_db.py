"""
initialize_db.py

Initializes the SQLite database and applies the schema.

This script:
- Creates the database file if it does not exist
- Applies all schema definitions from schema.py
- Is safe to run multiple times (idempotent)

Run once before any ingestion pipelines.
"""

import sqlite3
from pathlib import Path

from schema import get_all_schema_statements


# -------------------------
# Configuration
# -------------------------

DB_PATH = Path("data/clinical_trials.db")


# -------------------------
# Initialization logic
# -------------------------

def initialize_database(db_path: Path) -> None:
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to SQLite database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Apply schema statements
        for statement in get_all_schema_statements():
            cursor.execute(statement)

        # Commit all changes atomically
        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database(DB_PATH)
    print("Database initialized successfully.")
