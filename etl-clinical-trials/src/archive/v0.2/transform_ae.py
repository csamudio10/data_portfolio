import pandas as pd
import json
from pathlib import Path


# ===========================================================================
    # Root definition and raw data extraction
# ===========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_STUDIES_DIR = RAW_DATA_DIR / "studies"
RAW_AE_DIR = RAW_DATA_DIR / "adverse_events"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# locating the files and prepping the ae list
ae_files = sorted(RAW_AE_DIR.glob("*.json"))
all_aes = []

# extracting the AEs for ech study based on their NCT ID
for file in ae_files:
    nct_id_for_ae = str(file.stem)
    with open(file, "r", encoding="utf-8") as f:
        ae_raw_data = json.load(f)
        all_aes.append((nct_id_for_ae,ae_raw_data))
        
# getting the last updated data
last_updated_path = RAW_AE_DIR / "last_updated.txt"
try:
    with open(last_updated_path, 'r') as file:
        last_updated = file.read()
        print(last_updated)
except FileNotFoundError:
    print(f"Error: The file '{last_updated_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# ===========================================================================
    # Data processing
# ===========================================================================

processed_events_data = []
processed_ae_groups_data = []

# assuming all_aes is a list of tuples like (nct_id_str, study_dict)
for nct_id, ae_data in all_aes:
    # get the list of serious events dictionaries
    sae_list = ae_data.get("seriousEvents", [])
    # get the list of non-serious events dictionaries
    nsae_list = ae_data.get("otherEvents", [])
    # get the list of ae groups
    ae_groups = ae_data.get("eventGroups", [])
    
    last_updated_date = pd.to_datetime(last_updated)

    # Loop THROUGH the list of SAEs within this single study
    for event_dict in sae_list:
        # Extract the specific 'term' from the individual event dictionary
        term = event_dict.get("term")
        organ_system = event_dict.get("organSystem")
        source_vocabulary = event_dict.get("sourceVocabulary")
        assessment_type = event_dict.get("assessmentType")

        # If a term is found, add a flat row to the master list
        if term:
            processed_events_data.append({
                "nct_id": nct_id,
                "ae_term": term,
                "organ_system": organ_system,
                "vocabulary": source_vocabulary,
                "assessment_type": assessment_type,
                "serious": 1,
                "last_updated": last_updated_date
                
            })

    # Loop THROUGH the list of nSAEs within this single study
    for event_dict in nsae_list:
        # Extract the specific 'term' from the individual event dictionary
        term = event_dict.get("term")
        organ_system = event_dict.get("organSystem")
        source_vocabulary = event_dict.get("sourceVocabulary")
        assessment_type = event_dict.get("assessmentType")

        # If a term is found, add a flat row to our master list
        if term:
            processed_events_data.append({
                "nct_id": nct_id,
                "ae_term": term,
                "organ_system": organ_system,
                "vocabulary": source_vocabulary,
                "assessment_type": assessment_type,
                "serious": 0,
                "last_updated": last_updated_date
                
            })
    
    # looping for all the groups within the study and getting the info for each group
    for group in ae_groups:
        group_id = group.get("id")
        group_title = group.get("title")
        group_description = group.get("description")
        num_death_affected = group.get("deathsNumAffected")
        num_death_risk = group.get("deathsNumAtRisk")
        num_sae_affected = group.get("seriousNumAffected")
        num_sae_risk = group.get("seriousNumAtRisk")
        num_nSAE_affected = group.get("otherNumAffected")
        num_nSAE_risk = group.get("otherNumAffected")
        
        if group_id:
            processed_ae_groups_data.append({
                "nct_id": nct_id,
                "group_id": group_id,
                "group_title": group_title,
                "group_description": group_description,
                "num_death_affected": num_death_affected,
                "num_death_risk": num_death_risk,
                "num_sae_affected": num_sae_affected,
                "num_sae_risk": num_sae_risk,
                "num_nSAE_affected": num_nSAE_affected,
                "num_nSAE_risk": num_nSAE_risk
            })          
        

ae_data_df = pd.DataFrame(processed_events_data)
ae_group_df = pd.DataFrame(processed_ae_groups_data)

ae_data_df.to_csv(PROCESSED_DATA_DIR / "ae.csv", index=False)
ae_group_df.to_csv(PROCESSED_DATA_DIR / "ae_groups.csv", index=False)


# verification
if __name__ == "__main__":
    # Display the result ---
    print('===========================================\n')
    print(ae_data_df.head())
    print('===========================================\n')
    print(ae_group_df.head())