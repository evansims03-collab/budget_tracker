#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 21:07:00 2026
Updated Wed Sep 2

@author: evansims
"""
#pip install streamlit pandas plotly
#streamlit run app.py
from datetime import date, datetime
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_NAME = "finance_tracker.db"

# --- Default Categories & Initial Targets ---
DEFAULT_EXPENSE_CATEGORIES = {
    "Rent/mortgage": 1100.0,
    "Renters Insurance": 13.0,
    "Utilities": 200.0,
    "WiFi": 20.0,
    "Groceries": 455.0,
    "Restaurant": 180.0,
    "Phone Bill": 20.0,
    "Auto Insurance": 300.0,
    "Auto gas": 150.0,
    "Personal care": 75.0,
}

DEFAULT_SAVINGS_BUCKETS = {
    "Entertainment": 100.0,
    "Trips/Vacation": 300.0,
    "Glasses/Optics": 15.0,
    "Home renovations": 20.0,
    "Doctor Copay": 100.0,
    "Gifts for others": 40.0,
    "Auto expenses": 150.0,
    "Clothes": 80.0,
    "Bike/Bus": 10.0,
    "Big investment": 950.0,
    "Tech/Electronics": 50.0,
    "Skiing": 60.0,
    "Gym/Exercise/Sport": 80.0,
}

DEFAULT_RECURRING_BILLS = [
    {"name": "Apartment Rent", "category": "Rent/mortgage", "amount": 1100.0},
    {"name": "Renters Insurance", "category": "Renters Insurance", "amount": 13.0},
    {"name": "Electric & Gas", "category": "Utilities", "amount": 200.0},
    {"name": "Home Internet", "category": "WiFi", "amount": 20.0},
    {"name": "Cell Phone Plan", "category": "Phone Bill", "amount": 20.0},
    {"name": "Car Insurance", "category": "Auto Insurance", "amount": 300.0},
]

DEFAULT_KEYWORD_RULES = {
    "Groceries": ["trader joe", "kroger", "safeway", "wholefds", "sprouts", "aldi", "wegmans", "market", "costco whse"],
    "Restaurant": ["doordash", "uber eats", "grubhub", "starbucks", "chipotle", "cafe", "coffee", "restaurant", "pizza", "diner", "taco", "sushi", "burger", "bakery"],
    "Auto gas": ["shell", "chevron", "exxon", "mobil", "bp ", "circle k", "speedway", "sunoco", "costco gas", "quiktrip", "kum & go"],
    "Utilities": ["electric", "water dept", "xcel", "coned", "national grid", "waste mgmt", "sanitation", "power"],
    "WiFi": ["comcast", "xfinity", "verizon fios", "spectrum", "centurylink", "att internet", "starlink"],
    "Phone Bill": ["verizon wireless", "t-mobile", "att mobility", "mint mobile", "google fi", "visible"],
    "Rent/mortgage": ["leasing", "rent payment", "apartments", "mortgage"],
    "Renters Insurance": ["lemonade", "state farm renters", "geico renters", "progressive renters"],
    "Auto Insurance": ["progressive auto", "geico auto", "state farm auto", "allstate", "liberty mutual"],
    "Personal care": ["great clips", "supercuts", "salon", "barber", "sephora", "ulta", "cvs", "walgreens", "pharmacy"],
    "[Bucket] Trips/Vacation": ["airline", "delta", "united air", "american air", "southwest", "airbnb", "hotel", "expedia", "booking.com"],
    "[Bucket] Skiing": ["ikon pass", "epic pass", "resort", "lift ticket", "ski rental"],
    "[Bucket] Tech/Electronics": ["apple.com", "best buy", "micro center", "newegg", "b&h photo"],
    "[Bucket] Auto expenses": ["firestone", "autozone", "mechanic", "oil change", "brakes", "tire", "dealership service"],
    "[Bucket] Glasses/Optics": ["warby parker", "lenscrafters", "optometry", "vision care"],
    "[Bucket] Doctor Copay": ["quest diagnostics", "labcorp", "urgent care", "copay", "medical center", "hospital"],
    "[Bucket] Gym/Exercise/Sport": ["climbing", "gym", "fitness", "strava", "alltrails", "rei ", "patagonia"],
    "[Bucket] Clothes": ["nordstrom", "nike", "target", "uniqlo", "zara", "gap", "clothing"],
    "[Bucket] Bike/Bus": ["transit", "metro", "bus fare", "bike shop", "trek"],
    "[Bucket] Entertainment": ["ticketmaster", "cinema", "amc", "concert", "theatre", "bowling"],
    "[Bucket] Home renovations": ["home depot", "lowes", "ace hardware", "ikea"],
}

# --- Database Setup & Migrations ---
def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                name TEXT PRIMARY KEY,
                monthly_target REAL,
                is_active INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS savings_buckets (
                name TEXT PRIMARY KEY,
                monthly_allocation REAL,
                is_active INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount REAL,
                note TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bucket_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                bucket_name TEXT,
                type TEXT,
                amount REAL,
                note TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS recurring_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                amount REAL,
                is_active INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS posted_recurring (
                month TEXT,
                rule_id INTEGER,
                PRIMARY KEY(month, rule_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS posted_bucket_deposits (
                month TEXT PRIMARY KEY
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS keyword_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE,
                destination_category TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS income_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                amount REAL,
                source TEXT
            )
        """)

        c.execute("SELECT COUNT(*) FROM categories")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO categories (name, monthly_target) VALUES (?, ?)", [(k, v) for k, v in DEFAULT_EXPENSE_CATEGORIES.items()])

        c.execute("SELECT COUNT(*) FROM savings_buckets")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO savings_buckets (name, monthly_allocation) VALUES (?, ?)", [(k, v) for k, v in DEFAULT_SAVINGS_BUCKETS.items()])

        c.execute("SELECT COUNT(*) FROM recurring_rules")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO recurring_rules (name, category, amount) VALUES (?, ?, ?)", [(r["name"], r["category"], r["amount"]) for r in DEFAULT_RECURRING_BILLS])

        c.execute("SELECT COUNT(*) FROM keyword_rules")
        if c.fetchone()[0] == 0:
            rule_pairs = [(kw.strip().lower(), dest) for dest, keywords in DEFAULT_KEYWORD_RULES.items() for kw in keywords]
            c.executemany("INSERT OR IGNORE INTO keyword_rules (keyword, destination_category) VALUES (?, ?)", rule_pairs)
        conn.commit()

init_db()

# --- Page Config & Styling ---
st.set_page_config(page_title="AmericasBudget", layout="wide", page_icon="💳")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAF9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .block-container {
        max-width: 1140px !important;
        padding-top: 3.2rem !important;
        padding-bottom: 8.5rem !important;
    }
    .header-container {
        margin-bottom: 2rem;
    }
    .brand-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #0f3923;
        letter-spacing: -0.03em;
        margin: 0;
        line-height: 1.1;
    }
    .brand-tagline {
        font-size: 0.82rem;
        color: #4A6357;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-top: 6px;
    }
    .card-shell {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 24px;
        border: 1px solid rgba(15, 57, 35, 0.08);
        box-shadow: 0 4px 16px rgba(15, 57, 35, 0.03);
        margin-bottom: 20px;
    }
    .card-shell-header {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6C7E76;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .cat-wrapper {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 16px 20px;
        border: 1px solid rgba(15, 57, 35, 0.07);
        box-shadow: 0 2px 10px rgba(15, 57, 35, 0.02);
        margin-bottom: 18px;
    }
    .cat-title {
        font-weight: 800;
        font-size: 1.1rem;
        color: #122820;
        margin: 0;
    }
    .cat-sub {
        font-size: 0.88rem;
        color: #556B61;
        margin: 4px 0 2px 0;
    }
    .cat-rem {
        font-size: 0.82rem;
        font-weight: 700;
        margin: 0;
    }
    .trans-row {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 14px 20px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(15, 57, 35, 0.06);
    }
    .trans-title {
        font-weight: 700;
        font-size: 1.02rem;
        color: #122820;
        margin: 0;
    }
    .trans-sub {
        font-size: 0.8rem;
        color: #6A7D75;
        margin: 2px 0 0 0;
    }
    .trans-amt {
        font-weight: 800;
        font-size: 1.15rem;
        color: #0f3923;
        margin: 0;
    }

    /* Pinned Bottom Dock */
    .stRadio > div[role="radiogroup"] {
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: #0f3923;
        padding: 8px 24px;
        border-radius: 44px;
        display: flex;
        align-items: center;
        gap: 16px;
        z-index: 99999;
        box-shadow: 0 10px 36px rgba(15, 57, 35, 0.42);
    }
    .stRadio > div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    .stRadio > div[role="radiogroup"] label {
        margin: 0 !important;
        background: transparent !important;
    }
    .stRadio > div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        cursor: pointer;
    }
    .stRadio > div[role="radiogroup"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] {
        background-color: rgba(255, 255, 255, 0.16) !important;
        color: #FFFFFF !important;
    }
    .stRadio > div[role="radiogroup"] label:nth-child(3) {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stRadio > div[role="radiogroup"] label:nth-child(3) div[data-testid="stMarkdownContainer"] {
        background: #185c37 !important;
        color: #FFFFFF !important;
        width: 46px !important;
        height: 46px !important;
        border-radius: 50% !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
        border: 2px solid rgba(255, 255, 255, 0.25) !important;
        margin: -8px 4px !important;
    }
    .stRadio > div[role="radiogroup"] label:nth-child(3) div[data-testid="stMarkdownContainer"] p {
        font-size: 1.7rem !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Fetch Data & Context ---
conn = get_db()
cats_df = pd.read_sql("SELECT name, monthly_target FROM categories WHERE is_active=1", conn)
buckets_df = pd.read_sql("SELECT name, monthly_allocation FROM savings_buckets WHERE is_active=1", conn)
trans_df = pd.read_sql("SELECT * FROM transactions", conn)
bucket_ledger_df = pd.read_sql("SELECT * FROM bucket_ledger", conn)
rules_df = pd.read_sql("SELECT id, keyword, destination_category FROM keyword_rules ORDER BY destination_category, keyword", conn)
recurring_df = pd.read_sql("SELECT * FROM recurring_rules WHERE is_active=1", conn)
income_df = pd.read_sql("SELECT * FROM income_logs", conn)

all_destinations = cats_df["name"].tolist() + [f"[Bucket] {b}" for b in buckets_df["name"].tolist()]

# --- Toast Trigger Check ---
if "pending_toast" in st.session_state:
    st.toast(st.session_state["pending_toast"])
    del st.session_state["pending_toast"]

# --- Header Bar with Month Horizon ---
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
h_col1, h_col2 = st.columns([2.4, 1.4])
with h_col1:
    st.markdown("<h1 class='brand-title'>AmericasBudget</h1>", unsafe_allow_html=True)
    st.markdown("<p class='brand-tagline'>UNEMPLOYED STUDIOS</p>", unsafe_allow_html=True)

with h_col2:
    current_dt = date.today()
    month_options = []
    for m_idx in range(12):
        yr = 2026 + (m_idx // 12)
        mo = (m_idx % 12) + 1
        month_options.append(date(yr, mo, 1))

    month_labels = [d.strftime("%B %Y") for d in month_options]
    default_idx = next((i for i, d in enumerate(month_options) if d.year == current_dt.year and d.month == current_dt.month), 7)
    
    selected_label = st.selectbox("Month Horizon", options=month_labels, index=default_idx)
    selected_month_date = month_options[month_labels.index(selected_label)]
    active_month_str = selected_month_date.strftime("%Y-%m")
st.markdown("</div>", unsafe_allow_html=True)

# Filter Transactions for active month
if not trans_df.empty:
    trans_df["month"] = pd.to_datetime(trans_df["date"]).dt.strftime("%Y-%m")
    month_trans = trans_df[trans_df["month"] == active_month_str].copy()
else:
    month_trans = pd.DataFrame(columns=["id", "date", "category", "amount", "note", "month"])

# Filter Income for active month
if not income_df.empty:
    income_df["month"] = pd.to_datetime(income_df["date"]).dt.strftime("%Y-%m")
    month_income = income_df[income_df["month"] == active_month_str]["amount"].sum()
else:
    month_income = 0.0

# --- Chart Helpers ---
def render_hero_donut_spent(spent, target):
    pct_used = max(0.0, min(spent / target, 1.0)) if target > 0 else 0.0
    rem_pct = 1.0 - pct_used

    bar_color = "#0f3923" if spent <= target else "#E74C3C"
    fig = go.Figure(
        data=[
            go.Pie(
                values=[pct_used, rem_pct],
                hole=0.82,
                sort=False,
                direction="clockwise",
                rotation=0,
                marker=dict(colors=[bar_color, "#E3EAE6"], line=dict(color="#FFFFFF", width=3)),
                hoverinfo="none",
                textinfo="none",
            )
        ]
    )
    whole = int(abs(spent))
    cents = int(round((abs(spent) - whole) * 100))
    tag = f"spent out of ${target:,.2f}"

    fig.update_layout(
        showlegend=False,
        margin=dict(t=5, b=5, l=5, r=5),
        height=260,
        annotations=[
            dict(
                text=f"<span style='font-size:2.8rem; font-weight:800; color:{bar_color};'>${whole:,}</span><span style='font-size:1.4rem; font-weight:700; color:{bar_color};'>.{cents:02d}</span><br><span style='font-size:0.9rem; color:#6A7D75; font-weight:600;'>{tag}</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
    )
    return fig

def render_mini_gauge(spent, target):
    pct = max(0.0, min(spent / target, 1.0)) if target > 0 else 0.0
    pct_val = int(round((spent / target) * 100)) if target > 0 else 0
    color = "#0f3923" if spent <= target else "#E74C3C"

    fig = go.Figure(
        go.Pie(
            values=[pct, 1.0 - pct],
            hole=0.74,
            sort=False,
            direction="clockwise",
            rotation=0,
            marker=dict(colors=[color, "#E5ECE9"], line=dict(color="#FFFFFF", width=1.5)),
            hoverinfo="none",
            textinfo="none",
        )
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=72,
        width=72,
        annotations=[
            dict(
                text=f"<b style='font-size:13px; color:{color}; font-family:-apple-system, BlinkMacSystemFont, Segoe UI;'>{pct_val}%</b>",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
    )
    return fig

def predict_category(text, r_df):
    if not isinstance(text, str) or r_df.empty:
        return "Groceries"
    t_lower = text.lower()
    for _, r in r_df.iterrows():
        kw = str(r["keyword"]).lower()
        if kw and kw in t_lower:
            return r["destination_category"]
    return "Groceries"

# --- Bottom Navigation ---
current_tab = st.radio(
    "Nav",
    options=["Home", "Analysis", "+", "Savings", "Profile"],
    horizontal=True,
    label_visibility="collapsed",
)

# ==============================================================================
# SCREEN 1: HOME
# ==============================================================================
if current_tab == "Home":
    total_budget = cats_df["monthly_target"].sum()
    total_spent = month_trans["amount"].sum() if not month_trans.empty else 0.0

    hero_col1, hero_col2 = st.columns([1.3, 1])
    with hero_col1:
        st.markdown("<div class='card-shell'><p class='card-shell-header'>Monthly Budget Overview</p>", unsafe_allow_html=True)
        st.plotly_chart(render_hero_donut_spent(total_spent, total_budget), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    
    with hero_col2:
        st.markdown("<div class='card-shell'><p class='card-shell-header'>Target Diagnostics</p>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("Total Budget Cap", f"${total_budget:,.2f}")
        m2.metric("Total Income", f"${month_income:,.2f}")
        
        posted_records = pd.read_sql("SELECT rule_id FROM posted_recurring WHERE month = ?", conn, params=(active_month_str,))
        posted_ids = set(posted_records["rule_id"].tolist()) if not posted_records.empty else set()
        unposted = recurring_df[~recurring_df["id"].isin(posted_ids)]

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        if not unposted.empty:
            st.warning(f"Notice: {len(unposted)} recurring bills pending for {selected_month_date.strftime('%B')} (${unposted['amount'].sum():,.2f})")
            if st.button("Post Monthly Recurring Bills", type="primary"):
                with get_db() as c_conn:
                    for _, r_bill in unposted.iterrows():
                        c_conn.execute("INSERT INTO transactions (date, category, amount, note) VALUES (?, ?, ?, ?)", (selected_month_date.strftime("%Y-%m-01"), r_bill["category"], r_bill["amount"], f"[Recurring] {r_bill['name']}"))
                        c_conn.execute("INSERT INTO posted_recurring (month, rule_id) VALUES (?, ?)", (active_month_str, int(r_bill["id"])))
                    c_conn.commit()
                st.session_state["pending_toast"] = f"Posted recurring bills for {selected_month_date.strftime('%B')}."
                st.rerun()
        else:
            st.success("All recurring monthly bills are logged.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Category Allocations")
    col_left, col_right = st.columns(2, gap="large")
    
    for idx, (_, c_row) in enumerate(cats_df.iterrows()):
        c_name = c_row["name"]
        c_target = c_row["monthly_target"]
        c_spent = month_trans[month_trans["category"] == c_name]["amount"].sum() if not month_trans.empty else 0.0
        c_left_amt = c_target - c_spent
        rem_color = "#0f3923" if c_left_amt >= 0 else "#E74C3C"

        target_column = col_left if (idx % 2 == 0) else col_right

        with target_column:
            with st.container():
                st.markdown("<div class='cat-wrapper'>", unsafe_allow_html=True)
                box_txt, box_donut = st.columns([3.2, 1.2])
                with box_txt:
                    st.markdown(f"<p class='cat-title'>{c_name}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='cat-sub'><b>${c_spent:,.2f}</b> of ${c_target:,.2f}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='cat-rem' style='color: {rem_color};'>${c_left_amt:,.2f} remaining</p>", unsafe_allow_html=True)
                with box_donut:
                    st.plotly_chart(render_mini_gauge(c_spent, c_target), use_container_width=False, config={"displayModeBar": False})
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"### Transactions for {selected_month_date.strftime('%B %Y')}")
    if not month_trans.empty:
        for _, t in month_trans.sort_values(by="date", ascending=False).iterrows():
            st.markdown(
                f"""
                <div class="trans-row">
                    <div>
                        <p class="trans-title">{t['note'] if t['note'] else t['category']}</p>
                        <p class="trans-sub">{t['date']} • {t['category']}</p>
                    </div>
                    <p class="trans-amt">${t['amount']:,.2f}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No living expense transactions recorded for this month yet.")

# ==============================================================================
# SCREEN 2: ANALYSIS
# ==============================================================================
elif current_tab == "Analysis":
    st.markdown("### Spending Analysis")
    
    an_col1, an_col2 = st.columns(2, gap="large")
    with an_col1:
        st.markdown("<div class='card-shell'><p class='card-shell-header'>Month-to-Month Trend</p>", unsafe_allow_html=True)
        if not trans_df.empty:
            month_totals = trans_df.groupby("month")["amount"].sum().reset_index()
            fig_hist = px.bar(
                month_totals,
                x="month",
                y="amount",
                color_discrete_sequence=["#FF5E7E"],
                text_auto=".2s",
            )
            fig_hist.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="Month", showgrid=False),
                yaxis=dict(title="", showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
                height=350,
                margin=dict(l=10, r=10, t=20, b=10),
            )
            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Record transactions to populate monthly trends.")
        st.markdown("</div>", unsafe_allow_html=True)

    with an_col2:
        st.markdown(f"<div class='card-shell'><p class='card-shell-header'>Category Breakdown ({selected_month_date.strftime('%B %Y')})</p>", unsafe_allow_html=True)
        if not month_trans.empty:
            cat_totals = month_trans.groupby("category")["amount"].sum().reset_index()
            fig_pie = px.pie(
                cat_totals,
                values="amount",
                names="category",
                hole=0.45,
                color_discrete_sequence=["#0f3923", "#1A5638", "#257A50", "#36A16D", "#4CC98D", "#E37463", "#FF9F43", "#54A0FF"],
            )
            fig_pie.update_traces(
                textposition="outside",
                textinfo="percent+label",
                rotation=0,
                direction="clockwise",
            )
            fig_pie.update_layout(
                showlegend=False,
                height=390,
                margin=dict(l=30, r=30, t=20, b=40),
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No expenses to chart for this month.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# ACTION MODAL: +
# ==============================================================================
elif current_tab == "+":
    st.markdown("### Add Transactions & Inflow")
    
    tab_exp, tab_inc, tab_edit, tab_import = st.tabs(["Record Expense", "Log Income", "Edit Logged Transactions", "Import Statement (.CSV)"])

    with tab_exp:
        with st.form("quick_log_form"):
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                q_desc = st.text_input("Merchant / Payee / Note")
                q_amt = st.number_input("Amount ($)", min_value=0.01, step=1.0, format="%.2f")
            with q_col2:
                q_dest = st.selectbox("Category or Savings Bucket", all_destinations)
                q_date = st.date_input("Date", value=date.today())

            if st.form_submit_button("Record Transaction", type="primary", use_container_width=True):
                with get_db() as c_conn:
                    if q_dest.startswith("[Bucket] "):
                        b_name = q_dest.replace("[Bucket] ", "")
                        c_conn.execute("INSERT INTO bucket_ledger (date, bucket_name, type, amount, note) VALUES (?, ?, 'Withdrawal', ?, ?)", (q_date.isoformat(), b_name, q_amt, q_desc))
                    else:
                        c_conn.execute("INSERT INTO transactions (date, category, amount, note) VALUES (?, ?, ?, ?)", (q_date.isoformat(), q_dest, q_amt, q_desc))
                    c_conn.commit()
                st.session_state["pending_toast"] = f"✅ Recorded: {q_desc or q_dest} (${q_amt:,.2f})"
                st.rerun()

    with tab_inc:
        with st.form("quick_income_form"):
            i1, i2 = st.columns(2)
            with i1:
                inc_src = st.text_input("Income Source (e.g., Paycheck, Bonus)")
                inc_amt = st.number_input("Amount Received ($)", min_value=0.01, step=50.0, format="%.2f")
            with i2:
                inc_date = st.date_input("Deposit Date", value=date.today())
            if st.form_submit_button("Log Income Deposit", type="primary", use_container_width=True):
                with get_db() as c_conn:
                    c_conn.execute("INSERT INTO income_logs (date, amount, source) VALUES (?, ?, ?)", (inc_date.isoformat(), inc_amt, inc_src))
                    c_conn.commit()
                st.session_state["pending_toast"] = f"💵 Income recorded: {inc_src} (${inc_amt:,.2f})"
                st.rerun()

    with tab_edit:
        st.markdown("#### Modify or Delete Living Expense Transactions")
        if not trans_df.empty:
            edit_base_df = trans_df[["id", "date", "category", "amount", "note"]].sort_values(by="date", ascending=False).copy()
            edit_base_df["date"] = pd.to_datetime(edit_base_df["date"]).dt.date

            updated_trans_df = st.data_editor(
                edit_base_df,
                key="trans_table_editor",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "date": st.column_config.DateColumn("Date", required=True),
                    "category": st.column_config.SelectboxColumn("Category", options=cats_df["name"].tolist(), required=True),
                    "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f", required=True),
                    "note": st.column_config.TextColumn("Description"),
                },
                use_container_width=True,
                num_rows="dynamic",
            )
            if st.button("Save Changes to Transactions", type="primary"):
                with get_db() as c_conn:
                    c_conn.execute("DELETE FROM transactions")
                    for _, r in updated_trans_df.iterrows():
                        if pd.notna(r["amount"]) and float(r["amount"]) > 0:
                            c_conn.execute(
                                "INSERT INTO transactions (id, date, category, amount, note) VALUES (?, ?, ?, ?, ?)",
                                (int(r["id"]) if pd.notna(r["id"]) else None, str(r["date"]), str(r["category"]), float(r["amount"]), str(r["note"]) if pd.notna(r["note"]) else "")
                            )
                    c_conn.commit()
                st.session_state["pending_toast"] = "💾 Transaction ledger updated successfully!"
                st.rerun()
        else:
            st.info("No transactions logged in the database yet.")

    with tab_import:
        uploaded_file = st.file_uploader("Upload CSV bank statement", type=["csv"])
        if uploaded_file:
            raw_csv = pd.read_csv(uploaded_file)
            c1, c2, c3 = st.columns(3)
            with c1:
                col_d = st.selectbox("Date Column", raw_csv.columns)
            with c2:
                col_n = st.selectbox("Merchant / Description Column", raw_csv.columns)
            with c3:
                col_a = st.selectbox("Amount Column", raw_csv.columns)

            parsed_list = []
            for _, r in raw_csv.iterrows():
                try:
                    amt = abs(float(str(r[col_a]).replace("$", "").replace(",", "").strip()))
                    parsed_list.append({
                        "Import": True,
                        "date": pd.to_datetime(r[col_d]).date(),
                        "note": str(r[col_n]),
                        "amount": amt,
                        "destination": predict_category(str(r[col_n]), rules_df),
                    })
                except Exception:
                    continue

            if parsed_list:
                st.markdown("#### Review & Route Transactions")
                edit_df = st.data_editor(
                    pd.DataFrame(parsed_list),
                    column_config={
                        "destination": st.column_config.SelectboxColumn("Target Category / Bucket", options=all_destinations),
                        "amount": st.column_config.NumberColumn(format="$%.2f"),
                    },
                    use_container_width=True,
                )
                if st.button("Commit Import to Database", type="primary", use_container_width=True):
                    with get_db() as c_conn:
                        for _, row in edit_df[edit_df["Import"] == True].iterrows():
                            dest_choice = str(row["destination"])
                            if dest_choice.startswith("[Bucket] "):
                                b_target = dest_choice.replace("[Bucket] ", "")
                                c_conn.execute("INSERT INTO bucket_ledger (date, bucket_name, type, amount, note) VALUES (?, ?, 'Withdrawal', ?, ?)", (str(row['date']), b_target, float(row['amount']), str(row['note'])))
                            else:
                                c_conn.execute("INSERT INTO transactions (date, category, amount, note) VALUES (?, ?, ?, ?)", (str(row['date']), dest_choice, float(row['amount']), str(row['note'])))
                        c_conn.commit()
                    st.session_state["pending_toast"] = "Imported transactions successfully!"
                    st.rerun()

# ==============================================================================
# SCREEN 3: SAVINGS (With One-Click Monthly Deposit Engine)
# ==============================================================================
elif current_tab == "Savings":
    st.markdown("### Savings & Sinking Funds")

    # One-click monthly bucket deposits check
    posted_bucket_rec = pd.read_sql("SELECT 1 FROM posted_bucket_deposits WHERE month = ?", conn, params=(active_month_str,))
    deposits_already_posted = not posted_bucket_rec.empty
    total_monthly_savings_alloc = buckets_df["monthly_allocation"].sum()

    if not deposits_already_posted:
        st.warning(f"Notice: Monthly savings contributions for {selected_month_date.strftime('%B %Y')} (${total_monthly_savings_alloc:,.2f}) have not been posted yet.")
        if st.button(f"Deposit Monthly Bucket Savings (${total_monthly_savings_alloc:,.2f})", type="primary"):
            deposit_date = selected_month_date.strftime("%Y-%m-01")
            with get_db() as c_conn:
                for _, b_row in buckets_df.iterrows():
                    alloc_amt = float(b_row["monthly_allocation"])
                    if alloc_amt > 0:
                        c_conn.execute(
                            "INSERT INTO bucket_ledger (date, bucket_name, type, amount, note) VALUES (?, ?, 'Manual Deposit', ?, ?)",
                            (deposit_date, b_row["name"], alloc_amt, f"Monthly Allocation for {selected_month_date.strftime('%B %Y')}")
                        )
                c_conn.execute("INSERT INTO posted_bucket_deposits (month) VALUES (?)", (active_month_str,))
                c_conn.commit()
            st.session_state["pending_toast"] = f"✅ Deposited ${total_monthly_savings_alloc:,.2f} across all buckets for {selected_month_date.strftime('%B')}!"
            st.rerun()
    else:
        st.success(f"✅ Monthly savings deposits for {selected_month_date.strftime('%B %Y')} are posted.")

    # Aggregate bucket balances
    b_rows = []
    for _, b in buckets_df.iterrows():
        b_name = b["name"]
        logs = bucket_ledger_df[bucket_ledger_df["bucket_name"] == b_name] if not bucket_ledger_df.empty else pd.DataFrame()
        deps = logs[logs["type"].isin(["Auto-Deposit", "Manual Deposit"])]["amount"].sum() if not logs.empty else 0.0
        withd = logs[logs["type"] == "Withdrawal"]["amount"].sum() if not logs.empty else 0.0
        b_rows.append({"Bucket": b_name, "Rate": b["monthly_allocation"], "Balance": deps - withd})
    b_df = pd.DataFrame(b_rows)

    if not bucket_ledger_df.empty:
        bucket_ledger_df["month"] = pd.to_datetime(bucket_ledger_df["date"]).dt.strftime("%Y-%m")
        month_withdrawals = bucket_ledger_df[(bucket_ledger_df["month"] == active_month_str) & (bucket_ledger_df["type"] == "Withdrawal")]
        transfer_sum = month_withdrawals["amount"].sum()
    else:
        month_withdrawals = pd.DataFrame()
        transfer_sum = 0.0

    st.markdown(
        f"""
        <div class="card-shell" style="background: linear-gradient(135deg, #0f3923 0%, #1c5e3d 100%); color:white;">
            <p style="margin:0; font-size:0.85rem; color:#A7C4B5; text-transform:uppercase; font-weight:700;">Reimbursement to Checking ({selected_month_date.strftime('%B %Y')})</p>
            <h1 style="margin:6px 0; font-size:2.4rem; font-weight:800; color:white;">${transfer_sum:,.2f}</h1>
            <p style="margin:0; font-size:0.9rem; color:#D3E3DA;">Lump-sum to transfer from Savings into Checking to cover bucket outflows.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if transfer_sum > 0:
        with st.expander("📋 View Reimbursement Itemization", expanded=False):
            st.dataframe(month_withdrawals[["date", "bucket_name", "amount", "note"]].rename(columns={"bucket_name": "Bucket", "amount": "Amount", "note": "Reason"}), use_container_width=True)

    st.markdown("#### Bucket Solvency ($0 Centered)")
    all_b_names = b_df["Bucket"].tolist()
    sel_buckets = st.multiselect("Filter Buckets", all_b_names, default=all_b_names)
    filtered_b_df = b_df[b_df["Bucket"].isin(sel_buckets)].copy()

    if not filtered_b_df.empty:
        filtered_b_df["Color"] = filtered_b_df["Balance"].apply(lambda v: "#0f3923" if v >= 0 else "#E74C3C")
        fig_solv = go.Figure(
            go.Bar(
                y=filtered_b_df["Bucket"],
                x=filtered_b_df["Balance"],
                orientation="h",
                marker=dict(color=filtered_b_df["Color"]),
                text=filtered_b_df["Balance"].apply(lambda v: f" ${v:,.2f} "),
                textposition="outside",
            )
        )
        fig_solv.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor="#6C7E76", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(autorange="reversed"),
            height=max(360, len(filtered_b_df) * 32),
            margin=dict(l=10, r=40, t=10, b=10),
        )
        st.plotly_chart(fig_solv, use_container_width=True, config={"displayModeBar": False})

    st.markdown("#### Log Savings Inflow / Outflow")
    with st.form("manual_bucket_log"):
        mb1, mb2, mb3, mb4 = st.columns(4)
        with mb1:
            m_target = st.selectbox("Bucket", buckets_df["name"].tolist())
        with mb2:
            m_type = st.selectbox("Action", ["Manual Deposit", "Withdrawal"])
        with mb3:
            m_amt = st.number_input("Amount ($)", min_value=0.01, step=10.0, format="%.2f")
        with mb4:
            m_dt = st.date_input("Date", value=date.today())
        m_note = st.text_input("Memo / Note")

        if st.form_submit_button("Record Entry", type="primary"):
            with get_db() as c_conn:
                c_conn.execute("INSERT INTO bucket_ledger (date, bucket_name, type, amount, note) VALUES (?, ?, ?, ?, ?)", (m_dt.isoformat(), m_target, m_type, m_amt, m_note))
                c_conn.commit()
            st.session_state["pending_toast"] = f"{m_type} of ${m_amt:,.2f} recorded for {m_target}."
            st.rerun()
            
    # Editable Past Savings Ledger
    st.markdown("#### Manage Past Bucket Entries")
    with st.expander("✏️ View & Edit Past Savings Ledger", expanded=False):
        if not bucket_ledger_df.empty:
            edit_b_df = bucket_ledger_df[["id", "date", "bucket_name", "type", "amount", "note"]].sort_values(by="date", ascending=False).copy()
            edit_b_df["date"] = pd.to_datetime(edit_b_df["date"]).dt.date

            updated_b_df = st.data_editor(
                edit_b_df,
                key="bucket_ledger_editor",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "date": st.column_config.DateColumn("Date", required=True),
                    "bucket_name": st.column_config.SelectboxColumn("Bucket", options=buckets_df["name"].tolist(), required=True),
                    "type": st.column_config.SelectboxColumn("Type", options=["Manual Deposit", "Auto-Deposit", "Withdrawal"], required=True),
                    "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f", required=True),
                    "note": st.column_config.TextColumn("Memo / Note"),
                },
                use_container_width=True,
                num_rows="dynamic",
            )

            if st.button("Save Changes to Savings Ledger", type="primary"):
                with get_db() as c_conn:
                    c_conn.execute("DELETE FROM bucket_ledger")
                    for _, r in updated_b_df.iterrows():
                        if pd.notna(r["amount"]) and float(r["amount"]) > 0:
                            c_conn.execute(
                                "INSERT INTO bucket_ledger (id, date, bucket_name, type, amount, note) VALUES (?, ?, ?, ?, ?, ?)",
                                (
                                    int(r["id"]) if pd.notna(r["id"]) else None,
                                    str(r["date"]),
                                    str(r["bucket_name"]),
                                    str(r["type"]),
                                    float(r["amount"]),
                                    str(r["note"]) if pd.notna(r["note"]) else ""
                                )
                            )
                    c_conn.commit()
                st.session_state["pending_toast"] = "💾 Savings ledger updated successfully!"
                st.rerun()
        else:
            st.info("No entries in the savings ledger yet.")

# ==============================================================================
# SCREEN 4: PROFILE & SETTINGS
# ==============================================================================
elif current_tab == "Profile":
    st.markdown("### Settings & Budget Controls")

    # 1. Edit Category Limits
    st.markdown("#### 1. Adjust Monthly Living Expense Targets")
    cat_edit_df = st.data_editor(
        cats_df,
        column_config={"monthly_target": st.column_config.NumberColumn("Target Cap ($)", format="$%.2f")},
        disabled=["name"],
        use_container_width=True,
    )
    if st.button("Save Category Budget Changes", type="primary"):
        with get_db() as c_conn:
            for _, r in cat_edit_df.iterrows():
                c_conn.execute("UPDATE categories SET monthly_target = ? WHERE name = ?", (float(r["monthly_target"]), r["name"]))
            c_conn.commit()
        st.session_state["pending_toast"] = "Category budgets saved."
        st.rerun()

    st.markdown("---")

    # 2. Edit Monthly Savings Bucket Allocations
    st.markdown("#### 2. Adjust Monthly Savings Bucket Contributions")
    bucket_edit_df = st.data_editor(
        buckets_df,
        column_config={"monthly_allocation": st.column_config.NumberColumn("Monthly Contribution ($)", format="$%.2f")},
        disabled=["name"],
        use_container_width=True,
    )
    if st.button("Save Bucket Contribution Changes", type="primary"):
        with get_db() as c_conn:
            for _, r in bucket_edit_df.iterrows():
                c_conn.execute("UPDATE savings_buckets SET monthly_allocation = ? WHERE name = ?", (float(r["monthly_allocation"]), r["name"]))
            c_conn.commit()
        st.session_state["pending_toast"] = "Savings bucket contributions saved."
        st.rerun()

    st.markdown("---")

    # 3. Recurring Monthly Bills
    st.markdown("#### 3. Manage Recurring Monthly Fixed Bills")
    rec_edit = st.data_editor(
        recurring_df[["id", "name", "category", "amount"]],
        column_config={
            "category": st.column_config.SelectboxColumn("Category", options=cats_df["name"].tolist()),
            "amount": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True,
        num_rows="dynamic",
    )
    if st.button("Save Recurring Bills"):
        with get_db() as c_conn:
            c_conn.execute("DELETE FROM recurring_rules")
            for _, row in rec_edit.iterrows():
                if pd.notna(row["name"]) and float(row["amount"]) > 0:
                    c_conn.execute("INSERT INTO recurring_rules (name, category, amount) VALUES (?, ?, ?)", (str(row["name"]), str(row["category"]), float(row["amount"])))
            c_conn.commit()
        st.session_state["pending_toast"] = "Recurring bills updated."
        st.rerun()

    st.markdown("---")

    # 4. Keyword Rules
    st.markdown("#### 4. Auto-Categorization Keyword Rules")
    with st.form("add_rule_form"):
        rk1, rk2 = st.columns(2)
        with rk1:
            in_kw = st.text_input("Merchant Keyword (e.g., 'safeway', 'uber')").strip().lower()
        with rk2:
            in_cat = st.selectbox("Assigns to", all_destinations)
        if st.form_submit_button("Add Auto-Rule"):
            if in_kw:
                with get_db() as c_conn:
                    c_conn.execute("INSERT OR REPLACE INTO keyword_rules (keyword, destination_category) VALUES (?, ?)", (in_kw, in_cat))
                    c_conn.commit()
                st.session_state["pending_toast"] = f"Auto-rule for '{in_kw}' saved."
                st.rerun()

    if not rules_df.empty:
        st.dataframe(rules_df[["keyword", "destination_category"]], use_container_width=True)