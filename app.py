import platform
# Fix for Windows Store Python execution alias with snowflake-connector
platform.libc_ver = lambda *args, **kwargs: ('', '')

import os
import urllib.parse
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import streamlit as st

# ==========================================
# 1. PAGE SETUP & MODERN STYLING
# ==========================================
st.set_page_config(
    page_title="Hangout Tracker & Expense Hub",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern rounded cards and clean aesthetic
st.markdown("""
<style>
    .main {
        background-color: #F8FAFC;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .metric-val {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 13px;
        font-weight: 500;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE CONNECTION
# ==========================================
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()
load_env()

# Connect to Snowflake (Supports Streamlit secrets / env vars)
USER = os.environ.get("SNOWFLAKE_USER", "VOREKZ")
RAW_PASSWORD = os.environ.get("SNOWFLAKE_PASSWORD", "")
PASSWORD = urllib.parse.quote_plus(RAW_PASSWORD)
ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "kdicljj-hs69473")
DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "HangoutTracker")
SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "Core")
WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
ROLE = os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

@st.cache_resource
def get_engine():
    engine_url = f"snowflake://{USER}:{PASSWORD}@{ACCOUNT}/{DATABASE}/{SCHEMA}?warehouse={WAREHOUSE}&role={ROLE}"
    return create_engine(engine_url)

@st.cache_data(ttl=60)
def fetch_data():
    engine = get_engine()
    events_df = pd.read_sql("SELECT * FROM Events ORDER BY EventDate ASC", engine)
    ledger_df = pd.read_sql("SELECT * FROM Ledger", engine)
    people_df = pd.read_sql("SELECT * FROM People", engine)
    return events_df, ledger_df, people_df

try:
    events_df, ledger_df, people_df = fetch_data()
except Exception as e:
    st.error(f"Failed to connect to Snowflake: {e}")
    st.stop()

# ==========================================
# 3. HEADER & QUICK ACTION
# ==========================================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Monthly Hangout & Social Tracker")
    st.caption("Live social outing expenses, fair splits, and hangout suggestions")

with col_h2:
    st.write("")
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeCGstKbFpj3Is7mMxd2WDQ0s7x2RvSvav-w12x45U6hQVi6g/viewform"
    st.link_button("📱 Log New Outing", form_url, use_container_width=True, type="primary")

# ==========================================
# 4. CALCULATE METRICS
# ==========================================
total_spend = events_df['totalcost'].sum() if not events_df.empty else 0.0

# Hangouts this year
current_year = date.today().year
if not events_df.empty and 'eventdate' in events_df.columns:
    events_df['eventdate'] = pd.to_datetime(events_df['eventdate'])
    events_this_year = events_df[events_df['eventdate'].dt.year == current_year]
    hangouts_count = len(events_this_year)
    
    # Days since last hangout
    latest_date = events_df['eventdate'].max().date()
    days_since = (date.today() - latest_date).days
    since_last_str = f"{days_since} days" if days_since >= 0 else "0 days"
else:
    hangouts_count = 0
    since_last_str = "No Data"

# Least Suggested By calculation
if not events_df.empty and not people_df.empty and 'suggestedby' in events_df.columns:
    sugg_counts = {}
    for _, person in people_df.iterrows():
        pname = person['name']
        # Check if name is contained in suggestedby
        count = events_df['suggestedby'].fillna('').apply(lambda s: pname.lower() in s.lower()).sum()
        sugg_counts[pname] = count
    
    min_count = min(sugg_counts.values()) if sugg_counts else 0
    least_people = [p for p, c in sugg_counts.items() if c == min_count]
    least_sugg_str = f"{', '.join(least_people)} ({min_count})"
else:
    least_sugg_str = "No Data"

# ==========================================
# 5. TOP 4 SCORECARD CARDS
# ==========================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">${total_spend:,.2f}</div>
        <div class="metric-lbl">💰 Total Expenses</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{hangouts_count}</div>
        <div class="metric-lbl">🎯 Hangouts (YTD)</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{since_last_str}</div>
        <div class="metric-lbl">📅 Since Last Hangout</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="font-size: 18px; line-height: 28px;">{least_sugg_str}</div>
        <div class="metric-lbl">💤 Least Suggested By</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================
# 6. MAIN VISUALS (2 COLUMNS MATCHING MOCKUP)
# ==========================================
col_left, col_right = st.columns([4, 6])

# --- LEFT COLUMN: Category Donut & Balance Sheet ---
with col_left:
    st.subheader("Expenses by Category")
    if not events_df.empty:
        cat_df = events_df.groupby('category', as_index=False)['totalcost'].sum()
        fig_donut = px.pie(
            cat_df, 
            values='totalcost', 
            names='category', 
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        fig_donut.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True, height=260)
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No expense data recorded yet.")

    st.subheader("Friend Balances & Settlements")
    balance_records = []
    for _, person in people_df.iterrows():
        pid = person['personid']
        pname = person['name']
        paid = float(ledger_df[ledger_df['personid'] == pid]['amountpaid'].sum())
        owed = float(ledger_df[ledger_df['personid'] == pid]['amountowed'].sum())
        net = round(paid - owed, 2)
        
        if net > 0.01:
            status = f"🟢 Owed ${net:,.2f}"
        elif net < -0.01:
            status = f"🔴 Owes ${abs(net):,.2f}"
        else:
            status = "⚪ Settled"
            
        balance_records.append({
            "Friend": pname,
            "Total Paid": f"${paid:,.2f}",
            "Fair Share": f"${owed:,.2f}",
            "Net Balance": f"${net:,.2f}",
            "Status": status
        })
    
    bdf = pd.DataFrame(balance_records)
    st.dataframe(bdf, hide_index=True, use_container_width=True)

# --- RIGHT COLUMN: Spend Over Time & Bar Chart ---
with col_right:
    st.subheader("Hangout Spend by Month")
    if not events_df.empty:
        trend_df = events_df.copy()
        trend_df['MonthYear'] = trend_df['eventdate'].dt.strftime('%Y-%m')
        monthly_df = trend_df.groupby('MonthYear', as_index=False)['totalcost'].sum()
        
        fig_line = px.line(
            monthly_df, 
            x='MonthYear', 
            y='totalcost',
            markers=True,
            labels={'MonthYear': 'Month', 'totalcost': 'Spend ($)'},
            color_discrete_sequence=['#4F46E5']
        )
        fig_line.update_layout(margin=dict(t=10, b=20, l=20, r=10), height=260)
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Spend by Outing Spot")
    if not events_df.empty:
        spot_df = events_df.groupby(['location', 'category'], as_index=False)['totalcost'].sum()
        fig_bar = px.bar(
            spot_df, 
            x='location', 
            y='totalcost',
            color='category',
            labels={'location': 'Hangout Spot', 'totalcost': 'Total Bill ($)'},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_bar.update_layout(margin=dict(t=10, b=20, l=20, r=10), height=260)
        st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 7. RECENT HANGOUT ACTIVITY LOG
# ==========================================
with st.expander("📋 Full Hangout History Log", expanded=False):
    if not events_df.empty:
        display_events = events_df.copy()
        display_events['eventdate'] = display_events['eventdate'].dt.strftime('%Y-%m-%d')
        display_events['totalcost'] = display_events['totalcost'].apply(lambda x: f"${x:,.2f}")
        display_events.rename(columns={
            'eventdate': 'Date',
            'location': 'Spot Name',
            'category': 'Category',
            'totalcost': 'Total Bill',
            'suggestedby': 'Suggested By',
            'address': 'Location / City'
        }, inplace=True)
        cols_to_show = [c for c in ['Date', 'Spot Name', 'Category', 'Total Bill', 'Suggested By', 'Location / City'] if c in display_events.columns]
        st.dataframe(display_events[cols_to_show].sort_values('Date', ascending=False), hide_index=True, use_container_width=True)
