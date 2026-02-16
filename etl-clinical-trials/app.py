import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Clinical AE Dashboard",
    layout="wide"
)

with open(DB_PATH, 'rb') as f:
    header = f.read(16)
    st.write(f"File Header: {header}")

# ======================================================
# PATH SETUP
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "clinical_trials.db"

if not DB_PATH.exists():
    st.error("Database file not found. Please check path.")
    st.stop()

# ======================================================
# DATABASE CONNECTION
# ======================================================
import os
if os.path.exists(DB_PATH):
    size = os.path.getsize(DB_PATH)
    st.write(f"Database found at {DB_PATH}, size: {size} bytes")
    # If size is very small (like 130 bytes), it's a Git LFS pointer file!
else:
    st.error(f"Database file NOT found at {DB_PATH}")

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def run_query(query, params=None):
    # Use a context manager to ensure the connection closes safely
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql(query, conn, params=params)
        return df
    except sqlite3.DatabaseError as e:
        st.error(f"SQLite Error: {e}")
        return pd.DataFrame()

# ======================================================
# LOAD FILTER DATA (CACHED)
# ======================================================
@st.cache_data
def load_terms():
    return run_query(
        "SELECT DISTINCT ae_term FROM ae ORDER BY ae_term"
    )

@st.cache_data
def load_organs():
    return run_query(
        "SELECT DISTINCT organ_system FROM ae ORDER BY organ_system"
    )

@st.cache_data
def load_groups():
    return run_query(
        "SELECT DISTINCT group_id FROM ae ORDER BY group_id"
    )

terms = load_terms()
organs = load_organs()
groups = load_groups()

# ======================================================
# SIDEBAR FILTERS
# ======================================================
st.sidebar.header("Filters")

serious_filter = st.sidebar.selectbox(
    "Seriousness",
    ["All", "Serious", "Non-Serious"]
)

organ_filter = st.sidebar.multiselect(
    "Organ System",
    organs["organ_system"].dropna().tolist()
)

group_filter = st.sidebar.multiselect(
    "AE Group",
    groups["group_id"].dropna().tolist()
)

term_filter = st.sidebar.multiselect(
    "AE Term",
    terms["ae_term"].dropna().tolist()
)

# ======================================================
# BUILD SQL WHERE CLAUSE
# ======================================================
conditions = []
params = []

if serious_filter == "Serious":
    conditions.append("serious = 1")
elif serious_filter == "Non-Serious":
    conditions.append("serious = 0")

if organ_filter:
    conditions.append(f"organ_system IN ({','.join(['?']*len(organ_filter))})")
    params.extend(organ_filter)

if group_filter:
    conditions.append(f"group_id IN ({','.join(['?']*len(group_filter))})")
    params.extend(group_filter)

if term_filter:
    conditions.append(f"ae_term IN ({','.join(['?']*len(term_filter))})")
    params.extend(term_filter)

where_clause = ""
if conditions:
    where_clause = "WHERE " + " AND ".join(conditions)

# ======================================================
# TITLE
# ======================================================
st.title("Clinical Trial Adverse Events Dashboard")

# ======================================================
# MAIN TABLE
# ======================================================
st.header("AEs by Study")

main_query = f"""
SELECT
    nct_id,
    group_id,
    ae_term,
    organ_system,
    serious,
    num_affected,
    num_at_risk
FROM ae
{where_clause}
ORDER BY nct_id
LIMIT 1000
"""

with st.spinner("Loading data..."):
    ae_df = run_query(main_query, params)

st.dataframe(ae_df, use_container_width=True)

# ======================================================
# METRICS SUMMARY
# ======================================================
st.subheader("Summary Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Affected", int(ae_df["num_affected"].sum()))
c
