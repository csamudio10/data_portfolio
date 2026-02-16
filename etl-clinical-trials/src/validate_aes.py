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

def validate_ae(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:

    df = df.copy()

    # -------------------------------------------------------------------
    # 1. Key integrity checks
    # -------------------------------------------------------------------
    key_cols = ["nct_id", "group_id", "ae_term", "serious"]

    # Nulls in keys
    null_key_mask = df[key_cols].isna().any(axis=1)
    n_null_keys = null_key_mask.sum()

    if n_null_keys > 0:
        print(f"[AE] {n_null_keys} rows have NULL key values")

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
    # 2. Domain logic checks
    # -------------------------------------------------------------------
    logic_errors = []

    # num_affected <= num_at_risk
    mask = df["num_affected"] > df["num_at_risk"]
    if mask.any():
        logic_errors.append("num_affected > num_at_risk")
        df = df.loc[~mask]

    # num_events >= num_affected
    mask = df["num_events"] < df["num_affected"]
    if mask.any():
        logic_errors.append("num_events < num_affected")
        df = df.loc[~mask]

    # serious must be 0 or 1
    mask = ~df["serious"].isin([0, 1])
    if mask.any():
        logic_errors.append("invalid serious flag")
        df = df.loc[~mask]

    if logic_errors:
        print(f"[AE] Logic violations removed: {set(logic_errors)}")

    # -------------------------------------------------------------------
    # 3. Final checks
    # -------------------------------------------------------------------
    df.reset_index(drop=True, inplace=True)

    print(f"[AE] Validation complete → {len(df)} rows remaining")

    return df



def validate_ae_groups(df: pd.DataFrame, eliminate_nulls: bool = True, eliminate_dups: bool = True) -> pd.DataFrame:

    df = df.copy()

    # -------------------------------------------------------------------
    # 1. Key integrity checks
    # -------------------------------------------------------------------
    key_cols = ["nct_id", "group_id", "group_title"]

    # Nulls in keys
    null_key_mask = df[key_cols].isna().any(axis=1)
    n_null_keys = null_key_mask.sum()

    if n_null_keys > 0:
        print(f"[AE groups] {n_null_keys} rows have NULL key values")

        if eliminate_nulls:
            df = df.loc[~null_key_mask]

    # Duplicate keys
    dup_mask = df.duplicated(subset=key_cols)
    n_dups = dup_mask.sum()

    if n_dups > 0:
        print(f"[AE groups] {n_dups} duplicate AE group rows found")

        if eliminate_dups:
            df = df.loc[~dup_mask]

    # -------------------------------------------------------------------
    # 2. Domain logic checks
    # -------------------------------------------------------------------
    logic_errors = []
    
    numeric_cols = ['num_death_affected', 'num_death_at_risk', 'num_serious_affected', 'num_serious_at_risk', 'num_other_affected', 'num_other_at_risk']
    df[numeric_cols] = df[numeric_cols].fillna(value=0,inplace=True)

    # negative numbers in number of X
    mask = df[['num_death_affected', 'num_death_at_risk', 'num_serious_affected', 'num_serious_at_risk', 'num_other_affected', 'num_other_at_risk']] < 0
    if mask.any().any():
        logic_errors.append("negative numbers detected")
        df = df.abs()
        
    
    # -------------------------------------------------------------------
    # 3. Final checks
    # -------------------------------------------------------------------
    df.reset_index(drop=True, inplace=True)

    print(f"[AE groups] Validation complete → {len(df)} rows remaining")

    return df



def validate_files():
    validated_ae = validate_ae(ae_df)
    validated_ae_groups = validate_ae_groups(ae_grous_df)
    
    validated_ae.to_csv(VALIDATED_DATA_DIR / "validated_ae.csv", index=False)
    validated_ae_groups.to_csv(VALIDATED_DATA_DIR / "validated_ae_groups.csv", index=False)
    
validate_files()
