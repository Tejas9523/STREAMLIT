import streamlit as st
import pandas as pd
import psycopg2
import json
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Operations Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# CUSTOM CSS (🔥 UI MAGIC)
# -------------------------------
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }

        .main-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 0px;
        }

        .sub-title {
            color: gray;
            margin-bottom: 20px;
        }

        .card {
            padding: 20px;
            border-radius: 12px;
            background-color: #f8f9fa;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        }

        .metric-card {
            background: gray;
            padding: 15px;
            border-radius: 10px;
            border-left: 6px solid #4CAF50;
        }

        .sidebar .sidebar-content {
            background-color: #1e1e2f;
        }

    </style>
""", unsafe_allow_html=True)

# -------------------------------
# DB CONFIG
# -------------------------------
DB_CONFIG = {
    "host": "internal-elevate-edb-pgbouncer-ro-prod-933826853.us-east-1.elb.amazonaws.com",
    "port": "6433",
    "dbname": "ymdb",
    "user": "tppaw120",
    "password": "Py#8ivKg&99e",
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# -------------------------------
# LOAD QUERIES
# -------------------------------
@st.cache_data
def load_queries():
    with open("sql_query.json") as f:
        return json.load(f)

queries = load_queries()

# -------------------------------
# QUERY RUNNER
# -------------------------------
def run_query(query, start=None, end=None):
    try:
        if start:
            query = query.replace("start_date", str(start))
            query = query.replace("end_date", str(end))
            query = query.replace("concern_date", str(start))
            query = query.replace("sel_asof_date", str(start))

        conn = get_conn()
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return str(e)

# -------------------------------
# SIDEBAR (🔥 CLEAN NAVIGATION)
# -------------------------------
st.sidebar.markdown("## 📊 Dashboard")
st.sidebar.markdown("---")

query_name = st.sidebar.selectbox(
    "📁 Select Report",
    list(queries.keys())
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙ Filters")

# -------------------------------
# HEADER
# -------------------------------
st.markdown('<div class="main-title">Operations Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Job Monitoring · SPB Analytics · System Insights</div>', unsafe_allow_html=True)

# -------------------------------
# FILTERS UI
# -------------------------------
if query_name == "spb_adherence":
    selected_date = st.sidebar.date_input("📅 Select Date")

    run_clicked = st.sidebar.button("▶ Run Report")

else:
    start_date = st.sidebar.date_input("📅 Start Date")
    end_date = st.sidebar.date_input("📅 End Date")

    run_clicked = st.sidebar.button("▶ Run Report")

# -------------------------------
# RUN QUERY
# -------------------------------
if run_clicked:

    with st.spinner("Loading data..."):

        if query_name == "spb_adherence":
            result = run_query(queries[query_name], start=selected_date)
        else:
            result = run_query(queries[query_name], start=start_date, end=end_date)

    # -------------------------------
    # SPB DASHBOARD (🔥 PREMIUM LOOK)
    # -------------------------------
    if query_name == "spb_adherence" and isinstance(result, pd.DataFrame) and not result.empty:

        st.markdown("### 📈 SPB Adherence Overview")

        total_met = result["cut_off_met"].sum()
        total_missed = result["cut_off_missed"].sum()
        total_pending = result["pending"].sum()

        col1, col2, col3 = st.columns(3)

        col1.markdown(f"""
            <div class='metric-card'>
                <h4>✅ Met</h4>
                <h2>{total_met}</h2>
            </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
            <div class='metric-card' style='border-left:6px solid red'>
                <h4>❌ Missed</h4>
                <h2>{total_missed}</h2>
            </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
            <div class='metric-card' style='border-left:6px solid orange'>
                <h4>⏳ Pending</h4>
                <h2>{total_pending}</h2>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        # Chart
        fig = px.bar(
            result,
            x="region",
            y=["cut_off_met", "cut_off_missed"],
            barmode="group",
            title="Adherence by Region",
        )

        st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # TABLE SECTION
    # -------------------------------
    st.markdown("### 📋 Detailed Data")

    if isinstance(result, pd.DataFrame):
        if result.empty:
            st.warning("No data available")
        else:
            st.dataframe(result, use_container_width=True)

            csv = result.to_csv(index=False)
            st.download_button("⬇ Download CSV", csv, f"{query_name}.csv")
    else:
        st.error(result)