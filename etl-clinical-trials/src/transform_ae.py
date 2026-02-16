import pandas as pd
import json
from pathlib import Path

# ===========================================================================
# Project paths
# ===========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_AE_DIR = RAW_DATA_DIR / "adverse_events"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_AE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===========================================================================
# Load AE JSON files
# ===========================================================================
ae_files = sorted(RAW_AE_DIR.glob("*.json"))
all_aes = []

for file in ae_files:
    nct_id = file.stem
    with open(file, "r", encoding="utf-8") as f:
        ae_raw_data = json.load(f)
        all_aes.append((nct_id, ae_raw_data))

# Load last updated timestamp
last_updated_path = RAW_AE_DIR / "last_updated.txt"
last_updated_date = None

if last_updated_path.exists():
    last_updated_date = pd.to_datetime(last_updated_path.read_text().strip())

# ===========================================================================
# Helper function: process AE events (SAE + non-SAE)
# ===========================================================================
def process_events(event_list, nct_id, serious_flag, last_updated):
    rows = []

    for event in event_list:
        term = event.get("term")
        organ_system = event.get("organSystem")
        vocabulary = event.get("sourceVocabulary")
        assessment_type = event.get("assessmentType")

        stats_list = event.get("stats", [])

        for stat in stats_list:
            rows.append({
                "nct_id": nct_id,
                "group_id": stat.get("groupId"),
                "ae_term": term,
                "organ_system": organ_system,
                "vocabulary": vocabulary,
                "assessment_type": assessment_type,
                "serious": serious_flag,
                "num_affected": stat.get("numAffected"),
                "num_events": stat.get("numEvents"),
                "num_at_risk": stat.get("numAtRisk"),
                "last_updated": last_updated
            })

    return rows

# ===========================================================================
# Transform AE data
# ===========================================================================
processed_events_data = []
processed_ae_groups_data = []

for nct_id, ae_data in all_aes:

    serious_events = ae_data.get("seriousEvents", [])
    other_events = ae_data.get("otherEvents", [])
    ae_groups = ae_data.get("eventGroups", [])

    # ---- AE EVENTS (term-level, group-aware) ----
    processed_events_data.extend(
        process_events(serious_events, nct_id, 1, last_updated_date)
    )

    processed_events_data.extend(
        process_events(other_events, nct_id, 0, last_updated_date)
    )

    # ---- AE GROUPS (arm-level metadata) ----
    for group in ae_groups:
        processed_ae_groups_data.append({
            "nct_id": nct_id,
            "group_id": group.get("id"),
            "group_title": group.get("title"),
            "group_description": group.get("description"),
            "num_death_affected": group.get("deathsNumAffected"),
            "num_death_at_risk": group.get("deathsNumAtRisk"),
            "num_serious_affected": group.get("seriousNumAffected"),
            "num_serious_at_risk": group.get("seriousNumAtRisk"),
            "num_other_affected": group.get("otherNumAffected"),
            "num_other_at_risk": group.get("otherNumAtRisk"),
        })

# ===========================================================================
# Create DataFrames
# ===========================================================================
ae_df = pd.DataFrame(processed_events_data)
ae_groups_df = pd.DataFrame(processed_ae_groups_data)

# ===========================================================================
# Write outputs
# ===========================================================================
ae_df.to_csv(PROCESSED_DATA_DIR / "ae.csv", index=False)
ae_groups_df.to_csv(PROCESSED_DATA_DIR / "ae_groups.csv", index=False)

# ===========================================================================
# Verification
# ===========================================================================
if __name__ == "__main__":
    print("AE data sample:")
    print(ae_df.head())

    print("\nAE groups sample:")
    print(ae_groups_df.head())
