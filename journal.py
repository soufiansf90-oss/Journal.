import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3

# --- UI CONFIG ---
st.set_page_config(page_title="Elite 369 Tracker", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .status-card { border-radius: 10px; padding: 20px; margin: 10px 0; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
conn = sqlite3.connect('elite_tracker.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, type TEXT, 
              entry REAL, exit REAL, pnl REAL, status TEXT, setup TEXT, emotion TEXT)''')
conn.commit()

# --- HEADER ---
st.title("🚀 Elite 369 Trading Journal")
st.markdown("---")

# --- SIDEBAR: ADD TRADE ---
with st.sidebar:
    st.header("➕ Log New Trade")
    with st.form("trade_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.now())
        pair = st.text_input("Pair (e.g. XAUUSD)", "NAS100")
        t_type = st.selectbox("Type", ["BUY", "SELL"])
        pnl = st.number_input("P&L ($)", value=0.0)
        setup = st.selectbox("Setup", ["SMC", "ICT", "Liq Sweep", "Breakout"])
        emotion = st.select_slider("Mindset", options=["🔥 Focus", "😐 Normal", "😨 Fear", "😡 Revenge"])
        if st.form_submit_button("Submit to Journal"):
            c.execute("INSERT INTO trades (date, pair, type, pnl, setup, emotion) VALUES (?,?,?,?,?,?)",
                      (str(date), pair, t_type, pnl, setup, emotion))
            conn.commit()
            st.success("Trade Recorded!")
            st.rerun()

# --- DATA PROCESSING ---
df = pd.read_sql_query("SELECT * FROM trades", conn)

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # --- TOP METRICS ---
    total_pnl = df['pnl'].sum()
    win_rate = (len(df[df['pnl'] > 0]) / len(df)) * 100
    total_trades = len(df)
    avg_trade = df['pnl'].mean()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Net P&L", f"${total_pnl:,.2f}")
    m2.metric("Win Rate", f"{win_rate:.1f}%")
    m3.metric("Total Trades", total_trades)
    m4.metric("Avg. Trade", f"${avg_trade:.2f}")

    # --- CHARTS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Equity Curve")
        df['cum_pnl'] = df['pnl'].cumsum()
        fig_equity = px.area(df, x='date', y='cum_pnl', template="plotly_dark", 
                             line_color="#00ffcc", title="Growth Over Time")
        st.plotly_chart(fig_equity, use_container_width=True)

    with col2:
        st.subheader("📊 Profit by Pair")
        fig_pair = px.bar(df.groupby('pair')['pnl'].sum().reset_index(), 
                          x='pair', y='pnl', color='pnl', template="plotly_dark")
        st.plotly_chart(fig_pair, use_container_width=True)

    # --- RECENT JOURNAL ---
    st.subheader("📜 Recent Activity")
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
else:
    st.info("👋 Your journal is empty. Add your first trade from the sidebar!")

