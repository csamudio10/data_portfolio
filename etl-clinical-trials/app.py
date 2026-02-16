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

# ======================================================
# PATH SETUP
# ======================================================
# Using absolute pathing to ensure the cloud container finds the file
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "clinical_trials.db"

if not DB_PATH.exists():
    st.error(f"Database file not found at {DB_PATH}. Please check your repository structure.")
    st.stop()

# ======================================================
# DATABASE UTILITIES
# ======================================================
@st.cache_data
def run_query(query, params=None):
    """
    Connects to the SQLite DB and returns a dataframe.
    Uses params to prevent SQL injection and handle filtering.
    """
    # 'uri=True' with 'mode=ro' is the safest way to read in cloud environments
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ======================================================
# LOAD FILTER DATA (CACHED)
# ======================================================
@st.cache_data
def load_filter_options():
    # Note: Using 'aes' as the table name per your debug results
    terms_df = run_query("SELECT DISTINCT ae_term FROM aes WHERE ae_term IS NOT NULL ORDER BY ae_term")
    organs_df = run_query("SELECT DISTINCT organ_system FROM aes WHERE organ_system IS NOT NULL ORDER BY organ_system")
    groups_df = run_query("SELECT DISTINCT group_id FROM aes WHERE group_id IS NOT NULL ORDER BY group_id")
    
    return {
        "terms": terms_df["ae_term"].tolist(),
        "organs": organs_df["organ_system"].tolist(),
        "groups": groups_df["group_id"].tolist()
    }

filters = load_filter_options()

# ======================================================
# SIDEBAR FILTERS
# ======================================================
st.sidebar.header("Filters")

serious_filter = st.sidebar.selectbox(
    "Seriousness",
    ["All", "Serious", "Non-Serious"]
)

organ_selection = st.sidebar.multiselect("Organ System", filters["organs"])
group_selection = st.sidebar.multiselect("AE Group", filters["groups"])
term_selection = st.sidebar.multiselect("AE Term", filters["terms"])

# ======================================================
# BUILD SQL WHERE CLAUSE
# ======================================================
conditions = []
query_params = []

if serious_filter == "Serious":
    conditions.append("serious = 1")
elif serious_filter == "Non-Serious":
    conditions.append("serious = 0")

if organ_selection:
    conditions.append(f"organ_system IN ({','.join(['?']*len(organ_selection))})")
    query_params.extend(organ_selection)

if group_selection:
    conditions.append(f"group_id IN ({','.join(['?']*len(group_selection))})")
    query_params.extend(group_selection)

if term_selection:
    conditions.append(f"ae_term IN ({','.join(['?']*len(term_selection))})")
    query_params.extend(term_selection)

where_clause = ""
if conditions:
    where_clause = "WHERE " + " AND ".join(conditions)

# ======================================================
# MAIN DASHBOARD UI
# ======================================================
st.title("Clinical Trial Adverse Events Dashboard")

st.header("Adverse Events Data")

main_query = f"""
SELECT
    nct_id,
    group_id,
    ae_term,
    organ_system,
    serious,
    num_affected,
    num_at_risk
FROM aes
{where_clause}
ORDER BY nct_id
LIMIT 1000
"""

with st.spinner("Fetching data..."):
    ae_df = run_query(main_query, query_params)

if not ae_df.empty:
    # Display Metrics
    st.subheader("Summary Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows Displayed", len(ae_df))
    m2.metric("Total Affected", f"{int(ae_df['num_affected'].sum()):,}")
    m3.metric("Avg Risk %", f"{(ae_df['num_affected'].sum() / ae_df['num_at_risk'].sum() * 100):.2f}%" if ae_df['num_at_risk'].sum() > 0 else "0%")

    # Display Table
    st.dataframe(ae_df, use_container_width=True)
else:
    st.warning("No data found matching the selected filters.")
