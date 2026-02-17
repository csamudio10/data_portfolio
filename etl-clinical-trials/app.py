import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Clinical AE Dashboard",
    page_icon="🏥",
    layout="wide"
)

# ======================================================
# PATH SETUP & DATABASE UTILITIES
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "clinical_trials.db"

if not DB_PATH.exists():
    st.error(f"Database file not found at {DB_PATH}. Please check your repository.")
    st.stop()

@st.cache_data
def run_query(query, params=None):
    """Safely connects to SQLite and returns a DataFrame."""
    # Using read-only mode for cloud stability
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data
def load_filter_options():
    """Loads unique values for the sidebar filters."""
    terms = run_query("SELECT DISTINCT ae_term FROM aes WHERE ae_term IS NOT NULL ORDER BY ae_term")
    organs = run_query("SELECT DISTINCT organ_system FROM aes WHERE organ_system IS NOT NULL ORDER BY organ_system")
    groups = run_query("SELECT DISTINCT group_id FROM aes WHERE group_id IS NOT NULL ORDER BY group_id")
    return {
        "terms": terms["ae_term"].tolist(),
        "organs": organs["organ_system"].tolist(),
        "groups": groups["group_id"].tolist()
    }

# ======================================================
# SIDEBAR FILTERS
# ======================================================
st.sidebar.header("Global Filters")
options = load_filter_options()

serious_filter = st.sidebar.selectbox("Seriousness", ["All", "Serious", "Non-Serious"])
organ_selection = st.sidebar.multiselect("Organ System", options["organs"])
group_selection = st.sidebar.multiselect("AE Group", options["groups"])
term_selection = st.sidebar.multiselect("AE Term", options["terms"])

# Build WHERE clause
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

where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

# ======================================================
# DATA LOADING
# ======================================================
main_query = f"SELECT * FROM aes {where_clause} ORDER BY nct_id LIMIT 2000"
df = run_query(main_query, query_params)

# ======================================================
# MAIN DASHBOARD UI
# ======================================================
st.title("🏥 Clinical Trial Adverse Events Dashboard")

tab1, tab2 = st.tabs(["📋 Data Explorer", "📊 Visual Analytics"])

# --- TAB 1: DATA EXPLORER ---
with tab1:
    if not df.empty:
        st.subheader("High-Level Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Studies Found", df["nct_id"].nunique())
        m2.metric("Total Affected", f"{int(df['num_affected'].sum()):,}")
        m3.metric("Serious Events", f"{int(df[df['serious'] == 1]['num_affected'].sum()):,}")
        
        risk_pct = (df['num_affected'].sum() / df['num_at_risk'].sum() * 100) if df['num_at_risk'].sum() > 0 else 0
        m4.metric("Avg Risk %", f"{risk_pct:.2f}%")

        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found for the selected filters.")

# --- TAB 2: VISUAL ANALYTICS ---
with tab2:
    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # 1. Top 10 Most Frequent AEs
            st.subheader("Top 10 Most Frequent AEs")
            top_freq = df.groupby("ae_term")["num_affected"].sum().nlargest(10).reset_index()
            fig1 = alt.Chart(top_freq).mark_bar().encode(
                x=alt.X("num_affected:Q", title="Patients Affected"),
                y=alt.Y("ae_term:N", sort="-x", title="Adverse Event"),
                color=alt.value("#4C78A8")
            )
            st.altair_chart(fig1, use_container_width=True)

            # 2. Top 10 Studies with Most AEs
            st.subheader("Top 10 Studies by Volume")
            top_studies = df.groupby(["nct_id", "serious"])["num_affected"].sum().reset_index()
            # Get top 10 IDs by total sum
            top_10_ids = top_studies.groupby("nct_id")["num_affected"].sum().nlargest(10).index
            top_studies = top_studies[top_studies["nct_id"].isin(top_10_ids)]
            
            fig2 = alt.Chart(top_studies).mark_bar().encode(
                x=alt.X("num_affected:Q", title="Total Affected"),
                y=alt.Y("nct_id:N", sort="-x"),
                color=alt.Color("serious:N", scale=alt.Scale(range=["#76b7b2", "#e15759"]), title="Serious")
            )
            st.altair_chart(fig2, use_container_width=True)

        with col2:
            # 3. Top 10 Deadliest (Serious) AEs
            st.subheader("Top 10 Serious AEs")
            top_serious = df[df["serious"] == 1].groupby("ae_term")["num_affected"].sum().nlargest(10).reset_index()
            fig3 = alt.Chart(top_serious).mark_bar().encode(
                x=alt.X("num_affected:Q"),
                y=alt.Y("ae_term:N", sort="-x"),
                color=alt.value("#E15759")
            )
            st.altair_chart(fig3, use_container_width=True)

            # 4. Group Distribution (Pie Chart)
            st.subheader("AE Distribution by Group")
            group_data = df.groupby("group_id")["num_affected"].sum().reset_index()
            fig4 = alt.Chart(group_data).mark_arc(innerRadius=50).encode(
                theta="num_affected:Q",
                color="group_id:N",
                tooltip=["group_id", "num_affected"]
            )
            st.altair_chart(fig4, use_container_width=True)

        st.divider()

        # --- INTERACTIVE DRILL-DOWN ---
        st.header("🔍 Interactive Study Drill-Down")
        study_list = run_query("SELECT DISTINCT nct_id FROM aes")["nct_id"].tolist()
        selected_study = st.selectbox("Search/Select Study ID (NCT Number)", study_list)

        if selected_study:
            s_data = run_query("SELECT * FROM aes WHERE nct_id = ?", (selected_study,))
            
            sc1, sc2 = st.columns([1, 2])
            with sc1:
                st.write(f"**Analysis for {selected_study}**")
                tot = int(s_data["num_affected"].sum())
                ser = int(s_data[s_data["serious"] == 1]["num_affected"].sum())
                st.metric("Total AEs", tot)
                st.metric("Serious AEs", ser, delta=f"{(ser/tot*100):.1f}% of total" if tot > 0 else 0)
                
                selected_grp = st.radio("Filter by Group", ["All Groups"] + list(s_data["group_id"].unique()))

            with sc2:
                filtered_s_data = s_data if selected_grp == "All Groups" else s_data[s_data["group_id"] == selected_grp]
                st.dataframe(filtered_s_data[["ae_term", "organ_system", "num_affected", "num_at_risk", "serious"]], height=300)
    else:
        st.info("Please adjust filters to see visualizations.")
