import pandas as pd
from pathlib import Path

# ===========================================================================
    # Root definition and raw data extraction
# ===========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
VALIDATED_DATA_DIR = PROJECT_ROOT / "data" / "validated"


studies_df = pd.read_csv(PROCESSED_DATA_DIR / "studies.csv")
conditions_df = pd.read_csv(PROCESSED_DATA_DIR / "conditions.csv")
phases_df = pd.read_csv(PROCESSED_DATA_DIR / "phases.csv")



def validate_studies(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    n_dup_keys = df.duplicated(subset=['nct_id']).sum()
    n_null = df.isna().sum().sum()
    
    if n_dup_keys > 0:
        print(f"Duplicates found in studies. Number of duplicates = {n_dup_keys}")
        df = df.drop_duplicates()
    else:
        print("No duplicates found in studies")
        
    if n_null > 0:
        print(f"Null values found in studies. Number of null values = {n_null}")
        df = df.dropna()
    else:
        print("No null values found in studies")
        
    return df
        
def validate_conditions(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    n_dup_keys = df.duplicated().sum()
    n_null = df.isna().sum().sum()
    
    if n_dup_keys > 0:
        print(f"Duplicates found in conditions. Number of duplicates = {n_dup_keys}")
        if eliminate_dups:
            df = df.drop_duplicates()    

    else:
        print("No duplicates found in conditions")
        
    if n_null > 0:
        print(f"Null values found in conditions. Number of null values = {n_null}")
        
        if eliminate_nulls:
            df = df.dropna()
            
    else:
        print("No null values found in conditions")
        
    return df

def validate_phases(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    n_dup_keys = df.duplicated().sum()
    n_null = df.isna().sum().sum()
    
    if n_dup_keys > 0:
        print(f"Duplicates found in phases. Number of duplicates = {n_dup_keys}")

        if eliminate_dups:
            df = df.drop_duplicates()
    else:
        print("No duplicates found in phases")

    if n_null > 0:
        print(f"Null values found in phases. Number of null values = {n_null}")
    
        if eliminate_nulls:
            df = df.dropna()
    else:
        print("No null values found in phases")
        
    return df
    


def validate_files():
    validated_studies_df = validate_studies(studies_df)
    validated_conditions_df = validate_conditions(conditions_df)
    validated_phases_df = validate_phases(phases_df)
    
    validated_studies_df.to_csv(VALIDATED_DATA_DIR / "validated_studies.csv")
    validated_conditions_df.to_csv(VALIDATED_DATA_DIR / "validated_conditions.csv")
    validated_phases_df.to_csv(VALIDATED_DATA_DIR / "validated_phases.csv")
    
validate_files()