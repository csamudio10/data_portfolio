import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Clinical Trial Safety Dashboard",
    page_icon="🧪",
    layout="wide"
)

# ======================================================
# DATABASE UTILITIES
# ======================================================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "clinical_trials.db"

@st.cache_data
def run_query(query, params=None):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ======================================================
# REUSABLE CHARTING COMPONENT
# ======================================================
def render_ae_visualization_suite(data, context_name):
    """Renders the three standard charts for any data subset."""
    st.subheader(f"📊 {context_name} Visualizations")
    col1, col2, col3 = st.columns(3)
    
    if data.empty:
        st.warning(f"No data available for {context_name}")
        return

    with col1:
        st.write("**Top 10 Most Frequent AEs**")
        freq_df = data.groupby("ae_term")["num_affected"].sum().nlargest(10).reset_index()
        chart = alt.Chart(freq_df).mark_bar().encode(
            x=alt.X("num_affected:Q", title="Total Affected"),
            y=alt.Y("ae_term:N", sort="-x", title=None),
            color=alt.value("#4C78A8")
        ).properties(height=250)
        st.altair_chart(chart, use_container_width=True)

    with col2:
        st.write("**Top 10 Deadliest (Serious) AEs**")
        deadly_df = data[data["serious"] == 1].groupby("ae_term")["num_affected"].sum().nlargest(10).reset_index()
        if not deadly_df.empty:
            chart = alt.Chart(deadly_df).mark_bar().encode(
                x=alt.X("num_affected:Q", title="Serious Cases"),
                y=alt.Y("ae_term:N", sort="-x", title=None),
                color=alt.value("#E15759")
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No serious AEs reported.")

    with col3:
        st.write("**SAE vs NSAE Distribution**")
        dist_df = data.groupby("serious")["num_affected"].sum().reset_index()
        dist_df["label"] = dist_df["serious"].map({1: "Serious", 0: "Non-Serious"})
        chart = alt.Chart(dist_df).mark_arc(innerRadius=50).encode(
            theta="num_affected:Q",
            color=alt.Color("label:N", scale=alt.Scale(range=["#E15759", "#76B7B2"]), title=None)
        ).properties(height=250)
        st.altair_chart(chart, use_container_width=True)

# ======================================================
# MAIN DASHBOARD STRUCTURE
# ======================================================
st.title("🧪 Clinical Trial Adverse Events Dashboard")

# 1. GENERAL VISUALIZATIONS
# ------------------------------------------------------
st.header("🌎 1. General Level Analysis")
with st.spinner("Loading global statistics..."):
    global_df = run_query("SELECT ae_term, serious, num_affected FROM aes")
if not global_df.empty:
    render_ae_visualization_suite(global_df, "Global")

st.divider()

# 2. STUDY WIDE VISUALIZATIONS
# ------------------------------------------------------
st.header("🔍 2. Study-Wide Analysis")
study_list_df = run_query("SELECT nct_id, title FROM studies ORDER BY nct_id")
study_options = {row['nct_id']: f"{row['nct_id']} - {row['title']}" for _, row in study_list_df.iterrows()}

selected_nct = st.selectbox("Search/Select a Study", options=list(study_options.keys()), format_func=lambda x: study_options[x])

if selected_nct:
    study_query = """
    SELECT a.ae_term, a.serious, a.num_affected, a.num_at_risk, g.group_title
    FROM aes a
    LEFT JOIN ae_groups g ON a.nct_id = g.nct_id AND a.group_id = g.group_id
    WHERE a.nct_id = ?
    """
    study_data = run_query(study_query, (selected_nct,))
    
    if not study_data.empty:
        render_ae_visualization_suite(study_data, f"Study {selected_nct}")
        st.divider()

        # 3. GROUP WIDE VISUALIZATIONS
        # ------------------------------------------------------
        st.header("👥 3. Group-Level Analysis")
        unique_groups = sorted([g for g in study_data["group_title"].unique() if g is not None])
        selected_group = st.selectbox("Select a Specific Group (Arm)", options=unique_groups)
        
        if selected_group:
            group_data = study_data[study_data["group_title"] == selected_group]
            render_ae_visualization_suite(group_data, f"Group: {selected_group}")
            st.divider()

            # 4. INDIVIDUAL AE METRICS (Row 3 Search)
            # ------------------------------------------------------
            st.header("🔬 4. Individual AE Comparison")
            unique_aes = sorted(study_data["ae_term"].unique().tolist())
            selected_ae = st.selectbox("Search for an Individual Adverse Event (AE)", options=unique_aes)

            if selected_ae:
                ae_study_subset = study_data[study_data["ae_term"] == selected_ae]
                ae_group_subset = ae_study_subset[ae_study_subset["group_title"] == selected_group]

                # Metric Logic
                def calc_rate(df):
                    aff = df["num_affected"].sum()
                    risk = df["num_at_risk"].sum()
                    return (aff / risk * 100) if risk > 0 else 0, aff

                s_rate, s_aff = calc_rate(ae_study_subset)
                g_rate, g_aff = calc_rate(ae_group_subset)

                st.subheader(f"Incidence Comparison: '{selected_ae}'")
                m1, m2, m3 = st.columns(3)
                m1.metric("Study-Wide Rate", f"{s_rate:.2f}%")
                m2.metric(f"{selected_group} Rate", f"{g_rate:.2f}%", 
                          delta=f"{(g_rate - s_rate):+.2f}% vs Study Average", 
                          delta_color="inverse")
                m3.metric(f"Total Affected ({selected_group})", int(g_aff))

                # Chart for AE Comparison
                comp_data = pd.DataFrame({
                    "Category": ["Entire Study", f"Group: {selected_group}"],
                    "Incidence (%)": [s_rate, g_rate]
                })
                
                comp_chart = alt.Chart(comp_data).mark_bar(size=60).encode(
                    x=alt.X("Category:N", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Incidence (%):Q", title="Incidence Rate (%)"),
                    color=alt.Color("Category:N", scale=alt.Scale(range=["#4C78A8", "#F58518"]))
                ).properties(height=300)
                st.altair_chart(comp_chart, use_container_width=True)
