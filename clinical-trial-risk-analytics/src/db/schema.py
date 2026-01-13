"""
schema.py

Defines the database schema for the Clinical Trials Adverse Events platform.

Responsibilities:
- Declare all tables, constraints, indexes, and views
- Declare schema version
- Provide SQL statements ONLY (no execution)

Data source: ClinicalTrials.gov API (public data)
Database: SQLite (local, reproducible)
"""

from typing import List

# -------------------------
# Schema metadata
# -------------------------

SCHEMA_VERSION = "1.0.0"


def get_schema_version() -> str:
    return SCHEMA_VERSION


def enable_foreign_keys() -> str:
    return "PRAGMA foreign_keys = ON;"


def create_schema_metadata_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS schema_metadata (
        schema_version TEXT NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
def create_trials_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS trials (
        nct_id TEXT PRIMARY KEY,
        title TEXT,
        phase TEXT,
        condition TEXT,
        sponsor TEXT,
        study_status TEXT,
        start_date TEXT,
        completion_date TEXT
    );
    """

def create_trial_arms_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS trial_arms (
        arm_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nct_id TEXT NOT NULL,
        arm_name TEXT NOT NULL,
        arm_type TEXT,
        intervention TEXT,

        FOREIGN KEY (nct_id)
            REFERENCES trials(nct_id)
            ON DELETE RESTRICT
    );
    """

def create_adverse_events_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS adverse_events (
        ae_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nct_id TEXT NOT NULL,
        arm_id INTEGER NOT NULL,
        ae_term TEXT NOT NULL,
        ae_category TEXT,
        seriousness TEXT,
        affected_subjects INTEGER NOT NULL CHECK (affected_subjects >= 0),
        population_at_risk INTEGER NOT NULL CHECK (population_at_risk > 0),

        FOREIGN KEY (nct_id)
            REFERENCES trials(nct_id)
            ON DELETE RESTRICT,

        FOREIGN KEY (arm_id)
            REFERENCES trial_arms(arm_id)
            ON DELETE RESTRICT
    );
    """

def create_ae_ontology_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS ae_ontology (
        ae_term TEXT PRIMARY KEY,
        system_organ_class TEXT,
        severity_tier INTEGER CHECK (severity_tier BETWEEN 1 AND 5)
    );
    """
    
def create_data_sources_table() -> str:
    return """
    CREATE TABLE IF NOT EXISTS data_sources (
        source_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nct_id TEXT NOT NULL,
        api_version TEXT,
        retrieval_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        has_adverse_events INTEGER CHECK (has_adverse_events IN (0, 1)),

        FOREIGN KEY (nct_id)
            REFERENCES trials(nct_id)
            ON DELETE RESTRICT
    );
    """

def create_indexes() -> List[str]:
    return [
        """
        CREATE INDEX IF NOT EXISTS idx_trials_phase
        ON trials(phase);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_adverse_events_term
        ON adverse_events(ae_term);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_adverse_events_arm
        ON adverse_events(arm_id);
        """
    ]

def create_views() -> List[str]:
    return [
        """
        CREATE VIEW IF NOT EXISTS ae_rate_per_arm AS
        SELECT
            t.nct_id,
            a.arm_name,
            ae.ae_term,
            CAST(ae.affected_subjects AS FLOAT) / ae.population_at_risk AS ae_rate
        FROM adverse_events ae
        JOIN trial_arms a ON ae.arm_id = a.arm_id
        JOIN trials t ON ae.nct_id = t.nct_id;
        """,
        """
        CREATE VIEW IF NOT EXISTS serious_ae_summary AS
        SELECT
            nct_id,
            COUNT(*) AS serious_ae_count
        FROM adverse_events
        WHERE seriousness = 'Serious'
        GROUP BY nct_id;
        """
    ]

def register_schema_version() -> str:
    return f"""
    INSERT INTO schema_metadata (schema_version)
    SELECT '{SCHEMA_VERSION}'
    WHERE NOT EXISTS (
        SELECT 1 FROM schema_metadata
        WHERE schema_version = '{SCHEMA_VERSION}'
    );
    """

def get_all_schema_statements() -> List[str]:
    statements = [
        enable_foreign_keys(),
        create_schema_metadata_table(),
        create_trials_table(),
        create_trial_arms_table(),
        create_adverse_events_table(),
        create_ae_ontology_table(),
        create_data_sources_table(),
        register_schema_version(),
    ]

    statements.extend(create_indexes())
    statements.extend(create_views())

    return statements
