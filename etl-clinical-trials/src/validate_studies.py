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
    df = df.copy()

    # -------------------------------------------------------------------
    # 1. Key integrity checks
    # -------------------------------------------------------------------
    key_cols = ["nct_id"]
    
    # Nulls in keys
    null_key_mask = df[key_cols].isna().any(axis=1)
    n_null_keys = null_key_mask.sum()

    if n_null_keys > 0:
        print(f"[Studies] {n_null_keys} rows have NULL key values")

        if eliminate_nulls:
            df = df.loc[~null_key_mask]

    # Duplicate keys
    dup_mask = df.duplicated(subset=key_cols)
    n_dups = dup_mask.sum()

    if n_dups > 0:
        print(f"[AE] {n_dups} duplicate AE rows found")

        if eliminate_dups:
            df = df.loc[~dup_mask]
            
    
    # -------------------------------------------------------------------
    # 2. Final checks
    # -------------------------------------------------------------------
    df.reset_index(drop=True, inplace=True)

    print(f"[Studies] Validation complete → {len(df)} rows remaining")

    return df
        
def validate_conditions(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    df = df.copy()

    # -------------------------------------------------------------------
    # 1. Key integrity checks
    # -------------------------------------------------------------------
    key_cols = ["nct_id"]
    
    # Nulls in keys
    null_key_mask = df[key_cols].isna().any(axis=1)
    n_null_keys = null_key_mask.sum()

    if n_null_keys > 0:
        print(f"[Conditions] {n_null_keys} rows have NULL key values")

        if eliminate_nulls:
            df = df.loc[~null_key_mask]

    # Duplicate keys
    dup_mask = df.duplicated()
    n_dups = dup_mask.sum()

    if n_dups > 0:
        print(f"[Conditions] {n_dups} duplicate AE rows found")

        if eliminate_dups:
            df = df.loc[~dup_mask]
            
    # -------------------------------------------------------------------
    # 2. Final checks
    # -------------------------------------------------------------------
    df.reset_index(drop=True, inplace=True)

    print(f"[Studies] Validation complete → {len(df)} rows remaining")

    return df



def validate_phases(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:
    df = df.copy()

    # -------------------------------------------------------------------
    # 1. Key integrity checks
    # -------------------------------------------------------------------
    key_cols = ["nct_id"]
    
    # Nulls in keys
    null_key_mask = df[key_cols].isna().any(axis=1)
    n_null_keys = null_key_mask.sum()

    if n_null_keys > 0:
        print(f"[Phases] {n_null_keys} rows have NULL key values")

        if eliminate_nulls:
            df = df.loc[~null_key_mask]

    # Duplicate keys
    dup_mask = df.duplicated()
    n_dups = dup_mask.sum()

    if n_dups > 0:
        print(f"[Phases] {n_dups} duplicate phases rows found")

        if eliminate_dups:
            df = df.loc[~dup_mask]
            
    # -------------------------------------------------------------------
    # 2. Final checks
    # -------------------------------------------------------------------
    df.reset_index(drop=True, inplace=True)

    print(f"[Phases] Validation complete → {len(df)} rows remaining")

    return df
    


def validate_files():
    validated_studies_df = validate_studies(studies_df)
    validated_conditions_df = validate_conditions(conditions_df)
    validated_phases_df = validate_phases(phases_df)
    
    validated_studies_df.to_csv(VALIDATED_DATA_DIR / "validated_studies.csv", index= False)
    validated_conditions_df.to_csv(VALIDATED_DATA_DIR / "validated_conditions.csv", index= False)
    validated_phases_df.to_csv(VALIDATED_DATA_DIR / "validated_phases.csv", index= False)
    
validate_files()