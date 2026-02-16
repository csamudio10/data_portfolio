from pathlib import Path
from datetime import datetime, timezone
import requests
import json



PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_STUDIES_DIR = PROJECT_ROOT / "data" / "raw" / "studies"
RAW_STUDIES_DIR.mkdir(parents=True, exist_ok=True)

RAW_AE_DIR = PROJECT_ROOT / "data" / "raw" / "adverse_events"
RAW_AE_DIR.mkdir(parents=True, exist_ok=True)



def fetch_studies(condition: str):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": condition,
        "aggFilters" : "results:with,status:com",
        "fields": "NCTId,BriefTitle,Phase,Condition,Intervention",
        "pageSize": 50
    }

    try:
        response = requests.get(url, params=params, timeout=10)
    
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            print(f"Server Message: {response.text}") 
            return None
        
        data = response.json()
        studies = data.get("studies", [])

        return studies           
    
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def fetch_ae_data(nct_id: str):
    url = "https://clinicaltrials.gov/api/v2/studies"
    
    params = {
        "filter.ids": nct_id,
        "fields": "protocolSection.identificationModule.nctId|resultsSection.adverseEventsModule",
        "pageSize": 50
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
    
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            print(f"Server Message: {response.text}") 
            return None
            
        data = response.json()
        ae = data.get("studies", [])[0].get("resultsSection", {}).get("adverseEventsModule")
        
        if ae:
            return ae
        else:
            return None
    
    except Exception as e:
        print(f"Request failed: {e}")
        return None
    
    

def store_study_data(condition: str = "Oncology"):
    timestamp = datetime.now(timezone.utc).isoformat()[:10]
    file_path = RAW_STUDIES_DIR / f"studies_{timestamp}.json"

    studies_data = fetch_studies(condition)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(studies_data, f, indent=2)
        
    return studies_data

 
def store_ae_data(nct_id: str):
    
    ae_data = fetch_ae_data(nct_id)
    file_path = RAW_AE_DIR / f"{nct_id}.json"
    if ae_data:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ae_data, f, indent=2)


def main(condition: str = "Oncology"):
    timestamp = datetime.now(timezone.utc).isoformat()[:10]
    studies = store_study_data(condition=condition)
    if studies:
        for study in studies:
            nct_id = study["protocolSection"]["identificationModule"]["nctId"]
            store_ae_data(nct_id=nct_id)
            
    file_path = RAW_AE_DIR / "last_updated.txt"
    content_to_write = f"{timestamp}"

    try:
        with open(file_path, 'w') as file:
            file.write(content_to_write)
        print(f"File '{file_path}' created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
main()