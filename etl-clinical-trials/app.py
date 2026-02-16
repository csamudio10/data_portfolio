import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Clinical AE Dashboard", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "data" / "clinical_trials.db"

# ======================================================
# DATABASE CONNECTION
# ======================================================
@st.cache_data
def run_query(query, params=None):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


# ======================================================
# LOAD FILTER OPTIONS
# ======================================================
terms = run_query("SELECT DISTINCT ae_term FROM ae ORDER BY ae_term")
organs = run_query("SELECT DISTINCT organ_system FROM ae ORDER BY organ_system")
groups = run_query("SELECT DISTINCT group_id FROM ae ORDER BY group_id")

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
    groups["group_id"].tolist()
)

term_filter = st.sidebar.multiselect(
    "AE Term",
    terms["ae_term"].tolist()
)

# ======================================================
# BUILD WHERE CLAUSE
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
# MAIN TITLE
# ======================================================
st.title("Clinical Trial Adverse Events Dashboard")

# ======================================================
# AE TABLE BY STUDY
# ======================================================
st.header("AEs by Study")

query = f"""
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

ae_df = run_query(query, params)

st.dataframe(ae_df, use_container_width=True)

# ======================================================
# TOP AEs BY FREQUENCY
# ======================================================
st.header("Top AEs by Frequency")

freq_query = f"""
SELECT
    ae_term,
    SUM(num_affected) AS total_affected
FROM ae
{where_clause}
GROUP BY ae_term
ORDER BY total_affected DESC
LIMIT 15
"""

freq_df = run_query(freq_query, params)

st.bar_chart(freq_df.set_index("ae_term"))

# ======================================================
# DEADLIEST AEs
# ======================================================
st.header("Top AEs by Deadliness")

dead_query = f"""
SELECT
    ae_term,
    SUM(num_affected)*1.0 / SUM(num_at_risk) AS death_rate
FROM ae
{where_clause}
GROUP BY ae_term
HAVING SUM(num_at_risk) > 0
ORDER BY death_rate DESC
LIMIT 15
"""

dead_df = run_query(dead_query, params)

st.bar_chart(dead_df.set_index("ae_term"))

# ======================================================
# TOP ORGAN SYSTEMS
# ======================================================
st.header("Top Organ Systems")

organ_query = f"""
SELECT
    organ_system,
    SUM(num_affected) AS affected
FROM ae
{where_clause}
GROUP BY organ_system
ORDER BY affected DESC
LIMIT 15
"""

organ_df = run_query(organ_query, params)

st.bar_chart(organ_df.set_index("organ_system"))

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")
st.caption("Interactive AE dashboard built from ETL pipeline")
