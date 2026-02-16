import sqlite3
import pandas as pd
from pathlib import Path

# ===========================================================================
# Paths
# ===========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

VALIDATED_DATA_DIR = PROJECT_ROOT / "data" / "validated"
DB_PATH = PROJECT_ROOT / "data" / "clinical_trials.db"

# ===========================================================================
# Load validated CSVs
# ===========================================================================
studies_df = pd.read_csv(VALIDATED_DATA_DIR / "validated_studies.csv")
conditions_df = pd.read_csv(VALIDATED_DATA_DIR / "validated_conditions.csv")
phases_df = pd.read_csv(VALIDATED_DATA_DIR / "validated_phases.csv")
ae_df = pd.read_csv(VALIDATED_DATA_DIR / "validated_ae.csv")
ae_groups_df = pd.read_csv(VALIDATED_DATA_DIR / "validated_ae_groups.csv")

# ===========================================================================
# Connect to SQLite
# ===========================================================================
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ===========================================================================
# Create Tables
# ===========================================================================

# studies table
cursor.execute("""
CREATE TABLE IF NOT EXISTS studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    title TEXT NOT NULL,
    last_updated TIMESTAMP,
    UNIQUE(nct_id, title)
);
""")


# conditions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    condition TEXT NOT NULL,
    UNIQUE(nct_id, condition)
);
""")

# phases table
cursor.execute("""
CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    UNIQUE(nct_id, phase)
);
""")

# AE table
cursor.execute("""
CREATE TABLE IF NOT EXISTS aes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    ae_term TEXT NOT NULL,
    organ_system TEXT,
    vocabulary TEXT,
    assessment_type TEXT,
    serious INTEGER NOT NULL CHECK (serious IN (0,1)),
    num_affected INTEGER CHECK (num_affected >= 0),
    num_events INTEGER CHECK (num_events >= 0),
    num_at_risk INTEGER CHECK (num_at_risk >= 0),
    last_updated TIMESTAMP,
    UNIQUE (nct_id, group_id, ae_term, serious)
);
""")

# AE groups table
cursor.execute("""
CREATE TABLE IF NOT EXISTS ae_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    group_title TEXT,
    group_description TEXT,
    num_death_affected INTEGER,
    num_death_at_risk INTEGER,
    num_serious_affected INTEGER,
    num_serious_at_risk INTEGER,
    num_other_affected INTEGER,
    num_other_at_risk INTEGER,
    UNIQUE (nct_id, group_id)
);
""")

conn.commit()

# ===========================================================================
# Incremental Load: CONDITIONS FIRST (FK dependency)
# ===========================================================================
insert_groups_query = """
INSERT OR IGNORE INTO conditions (
    nct_id, condition
)
VALUES (?, ?)
"""

before_groups = conn.total_changes
cursor.executemany(insert_groups_query, conditions_df.values.tolist())
conn.commit()
after_groups = conn.total_changes

print(f"New AE groups inserted: {after_groups - before_groups}")


# ===========================================================================
# Incremental Load: PHASES FIRST (FK dependency)
# ===========================================================================
insert_groups_query = """
INSERT OR IGNORE INTO phases (
    nct_id, phase
)
VALUES (?, ?)
"""

before_groups = conn.total_changes
cursor.executemany(insert_groups_query, phases_df.values.tolist())
conn.commit()
after_groups = conn.total_changes

print(f"New AE groups inserted: {after_groups - before_groups}")


# ===========================================================================
# Incremental Load: STUDIES
# ===========================================================================
insert_groups_query = """
INSERT OR IGNORE INTO studies (
    nct_id, title, last_updated
)
VALUES (?, ?, ?)
"""

before_groups = conn.total_changes
cursor.executemany(insert_groups_query, studies_df.values.tolist())
conn.commit()
after_groups = conn.total_changes

print(f"New AE groups inserted: {after_groups - before_groups}")




# ===========================================================================
# Incremental Load: AE GROUPS FIRST (FK dependency)
# ===========================================================================
insert_groups_query = """
INSERT OR IGNORE INTO ae_groups (
    nct_id, group_id, group_title, group_description,
    num_death_affected, num_death_at_risk,
    num_serious_affected, num_serious_at_risk,
    num_other_affected, num_other_at_risk
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

before_groups = conn.total_changes
cursor.executemany(insert_groups_query, ae_groups_df.values.tolist())
conn.commit()
after_groups = conn.total_changes

print(f"New AE groups inserted: {after_groups - before_groups}")

# ===========================================================================
# Incremental Load: AE EVENTS
# ===========================================================================
insert_ae_query = """
INSERT OR IGNORE INTO aes (
    nct_id, group_id, ae_term, organ_system,
    vocabulary, assessment_type, serious,
    num_affected, num_events, num_at_risk, last_updated
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

before_ae = conn.total_changes
cursor.executemany(insert_ae_query, ae_df.values.tolist())
conn.commit()
after_ae = conn.total_changes

print(f"New AE rows inserted: {after_ae - before_ae}")

# ===========================================================================
# Close connection
# ===========================================================================
conn.close()

print("Incremental load complete.")