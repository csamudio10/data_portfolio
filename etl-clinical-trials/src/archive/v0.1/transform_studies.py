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

study_files = sorted(RAW_STUDIES_DIR.glob("*.json"))
ae_files = sorted(RAW_AE_DIR.glob("*.json"))

all_studies = []
all_aes = []

with open(study_files[0], "r", encoding="utf-8") as f:
    study_raw_data = json.load(f)
    all_studies.append(study_raw_data)

for file in ae_files:
    nct_id_for_ae = str(file.stem)
    with open(file, "r", encoding="utf-8") as f:
        ae_raw_data = json.load(f)
        all_aes.append((nct_id_for_ae,ae_raw_data))

# ===========================================================================
    # Data processing
# ===========================================================================

# ---- Study data ----
# Extracting the study data from the raw json file through list comprehension
study_data = [
    {
        "nct_id": study["protocolSection"]["identificationModule"]["nctId"],
        "title": study["protocolSection"]['identificationModule']['briefTitle'],
        "last_updated": pd.to_datetime(str(study_files[0]).split("_")[2].split(".")[0])
        
    }
    for study in all_studies[0]
]

# Extracting the condition data from the raw json file through list comprehension
condition_data = [
    {
        "nct_id": study["protocolSection"]["identificationModule"]["nctId"],
        # The 'conditions' value here is a Python list, e.g., ['Leukemia', 'Cancer']
        "condition_list": study["protocolSection"]["conditionsModule"]["conditions"]
    }
    for study in all_studies[0]
]

# Extracting the phase data from the raw json file through list comprehension
phase_data = [
    {
        "nct_id": study["protocolSection"]["identificationModule"]["nctId"],
        "phase_list":study["protocolSection"]['designModule'].get('phases',[])
    }
    for study in all_studies[0]
    if study["protocolSection"]['designModule'].get('phases', []) 
]



# creation of the dataframes
study_df = pd.DataFrame(study_data)

# since there can be multiple conditions for one study, further processing is required
conditions_df = pd.DataFrame(condition_data)
conditions_df = conditions_df.explode('condition_list')
conditions_df = conditions_df.rename(columns={'condition_list': 'condition'})
conditions_df = conditions_df.reset_index(drop=True)

# since there can be multiple conditions for one study, further processing is required
phase_df = pd.DataFrame(phase_data)
phase_df = phase_df.explode('phase_list')
phase_df = phase_df.rename(columns={'phase_list': 'phase'})
phase_df = phase_df.reset_index(drop=True)



# ---- AE data ----
processed_events_data = []
processed_ae_groups_data = []

# Assuming all_aes is a list of tuples like (nct_id_str, study_dict)
for nct_id, ae_data in all_aes:
    # Safely get the list of serious events dictionaries
    sae_list = ae_data.get("seriousEvents", [])
    nsae_list = ae_data.get("otherEvents", [])
    ae_groups = ae_data.get("eventGroups", [])
    
    last_updated_date = pd.to_datetime(study_files[0].stem.split("_")[1])

    # Loop THROUGH the list of events within this single study
    for event_dict in sae_list:
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
                "serious": 1,
                "last_updated": last_updated_date
                
            })

    # Loop THROUGH the list of events within this single study
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
        

ae_df = pd.DataFrame(processed_events_data)
ae_group_df = pd.DataFrame(processed_ae_groups_data)


# saving the processed files to .csv format
study_df.to_csv(PROCESSED_DATA_DIR / "studies.csv")
conditions_df.to_csv(PROCESSED_DATA_DIR / "conditions.csv")
phase_df.to_csv(PROCESSED_DATA_DIR / "phases.csv")


ae_df.to_csv(PROCESSED_DATA_DIR / "ae_processed.csv")
ae_group_df.to_csv(PROCESSED_DATA_DIR / "ae_groups_processed.csv")



# verification
if __name__ == "__main__":
    # Display the result ---
    print('\n===========================================')
    print(study_df.head())
    print('\n')
    print(conditions_df.head())
    print('\n')
    print(ae_df)
    print('\n')
    print(ae_group_df)
