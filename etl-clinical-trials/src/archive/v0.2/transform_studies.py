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




# saving the processed files to .csv format
study_df.to_csv(PROCESSED_DATA_DIR / "studies.csv", index=False)
conditions_df.to_csv(PROCESSED_DATA_DIR / "conditions.csv", index=False)
phase_df.to_csv(PROCESSED_DATA_DIR / "phases.csv", index=False)



# verification
if __name__ == "__main__":
    # Display the result ---
    print('\n===========================================')
    print(study_df.head())
    print('\n')
    print(conditions_df.head())