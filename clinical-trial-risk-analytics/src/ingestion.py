import requests
import json

def fetch_all_ae_data(condition):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": condition,
        "fields": "protocolSection.identificationModule.nctId,resultsSection.adverseEventsModule",
        "pageSize": 50
    }

    # 1. INITIALIZE AN EMPTY LIST OUTSIDE THE LOOP
    all_studies_captured = []

    response = requests.get(url, params=params)
    data = response.json()
    studies = data.get("studies", [])

    for study in studies:
        nct_id = study["protocolSection"]["identificationModule"]["nctId"]
        ae_module = study.get("resultsSection", {}).get("adverseEventsModule")

        if ae_module:
            # 2. APPEND TO THE LIST SO DATA GROWS RATHER THAN OVERWRITES
            study_record = {
                "nct_id": nct_id,
                "adverse_events": ae_module
            }
            all_studies_captured.append(study_record)
            print(f"Stored data for {nct_id}")

    # 3. RETURN AFTER THE LOOP IS FULLY FINISHED
    return all_studies_captured

def has_ae_data(study: dict) -> bool:
    try:
        ae_module = study["adverse_events"]
        serious = ae_module.get("seriousEvents", [])
        other = ae_module.get("otherEvents", [])
        return len(serious) > 0 or len(other) > 0
    except KeyError:
        return False



if __name__ == "__main__":
    
# Save to a JSON file to verify all 13 are there
    results = fetch_all_ae_data("Oncology")
    with open("clinical_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print(f"Success! Total studies saved: {len(results)}")

    for study in results:
        print(has_ae_data(study=study))
