import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os
from datetime import datetime, timezone, timedelta

# ─── Config ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto_arb.db")
IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(
    page_title="₿ Arbitrage Matrix",
    page_icon="🕸️",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    .main-header { text-align: center; padding: 1.5rem 0; }
    .main-header h1 {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #f7931a, #ffb347);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    .matrix-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }

    .opp-badge {
        background: rgba(100, 255, 218, 0.1);
        border: 1px solid #64ffda;
        color: #64ffda;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    # Check if new columns exist, otherwise fallback or wait
    try:
        df = pd.read_sql_query("SELECT * FROM spreads ORDER BY timestamp DESC LIMIT 100", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

st.markdown('<div class="main-header"><h1>₿ Crypto Arbitrage Matrix</h1><p>Real-time monitoring across Kraken, Coinbase, Bitfinex, and Gemini</p></div>', unsafe_allow_html=True)

df = load_data()

if not df.empty and "best_spread" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(IST)
    latest = df.iloc[0]

    # ─── Top Opportunity Dial ─────────────────────────────────────
    st.markdown(f"""
    <div class="opp-badge">
        <h2 style="margin:0; font-size: 1.5rem;">🔥 Best Opportunity: {latest['best_spread']:.4f}%</h2>
        <p style="margin:5px 0 0 0; font-size: 1.1rem;">
            Buy on <strong style="color:white">{latest['buy_at']}</strong> ⮕ 
            Sell on <strong style="color:white">{latest['sell_at']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Metric Matrix ────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    exchanges = ["Kraken", "Coinbase", "Bitfinex", "Gemini"]
    cols = [col1, col2, col3, col4]
    
    for i, ex in enumerate(exchanges):
        price = latest[ex.lower()]
        with cols[i]:
            is_low = (ex == latest['buy_at'])
            is_high = (ex == latest['sell_at'])
            border = "2px solid #64ffda" if is_low else ("2px solid #ff5252" if is_high else "1px solid rgba(255,255,255,0.1)")
            label = " (LOWEST)" if is_low else (" (HIGHEST)" if is_high else "")
            
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border:{border}; border-radius:12px; padding:1rem; text-align:center;">
                <div style="font-size:0.8rem; color:#8892b0; text-transform:uppercase;">{ex}{label}</div>
                <div style="font-size:1.5rem; font-weight:700;">${price:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    # ─── Trend Chart ──────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    df_chart = df.sort_values(by="timestamp")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_chart["timestamp"], y=df_chart["best_spread"],
        mode="lines+markers",
        line=dict(color="#f7931a", width=3, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(247, 147, 26, 0.1)",
        name="Market Spread %"
    ))
    
    fig.update_layout(
        title="Maximum Market Spread Over Time",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8892b0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", ticksuffix="%"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Detailed Matrix Chart ────────────────────────────────────
    fig2 = go.Figure()
    for ex in exchanges:
        fig2.add_trace(go.Scatter(
            x=df_chart["timestamp"], y=df_chart[ex.lower()],
            name=ex, line=dict(width=2, shape="spline")
        ))
    
    fig2.update_layout(
        title="Exchange Price Comparison",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8892b0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)

    if st.button("🔄 Refresh Data"):
        st.rerun()

else:
    st.info("Waiting for Price Matrix data... Ensure ingest.py is running.")
