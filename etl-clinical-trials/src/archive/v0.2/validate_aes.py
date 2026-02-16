import pandas as pd
from pathlib import Path

# ===========================================================================
    # Root definition and raw data extraction
# ===========================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
VALIDATED_DATA_DIR = PROJECT_ROOT / "data" / "validated"



ae_df = pd.read_csv(PROCESSED_DATA_DIR / "ae.csv")
ae_grous_df = pd.read_csv(PROCESSED_DATA_DIR / "ae_groups.csv")

def validate_ae(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = False):
    key_variables = ['nct_id','ae_term','organ_system','serious']
    df_keys = df[key_variables]
    # check for null key values in AE table
    n_nulls = df_keys.isna().sum().sum()
    
    if n_nulls > 0:
        print("Null values found in key variables in AE table")
        
    
    
    # check for duplicated keys in the AE table 
    n_dups = df_keys.duplicated().sum()
    
    if n_dups > 0:
        print("Duplicated values found in key variables in AE table")





def validate_ae_groups(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    n_dup_keys = df.duplicated().sum()
    n_null = df.isna().sum().sum()
    
    if n_dup_keys > 0:
        print(f"Duplicates found in AE groups. Number of duplicates = {n_dup_keys}")
        if eliminate_dups:
            df = df.drop_duplicates()    

    else:
        print("No duplicates found in AE groups")
        
    if n_null > 0:
        print(f"Null values found in AE groups. Number of null values = {n_null}")
        
        if eliminate_nulls:
            df = df.dropna()
            
    else:
        print("No null values found in AE groups")
        
    return df


def validate_files():
    validated_ae = validate_ae(ae_df)
    validated_ae_groups = validate_ae_groups(ae_grous_df)
    
    validated_ae.to_csv(VALIDATED_DATA_DIR / "validated_ae.csv")
    validated_ae_groups.to_csv(VALIDATED_DATA_DIR / "validated_ae_groups.csv")
    
validate_files()