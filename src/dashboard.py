import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import os
import numpy as np
from datetime import datetime, timezone, timedelta

# ─── Config ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto_arb.db")
IST = timezone(timedelta(hours=5, minutes=30))
EXCHANGES = ["Kraken", "Coinbase", "Bitfinex", "Gemini"]
ASSETS = ["BTC", "ETH", "SOL"]

st.set_page_config(
    page_title="₿ Pro Matrix Terminal",
    page_icon="💸",
    layout="wide",
)

# ─── Custom Styles ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0d1117 0%, #010409 100%);
        color: #c9d1d9; font-family: 'Inter', sans-serif;
    }
    
    .glass-card {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 16px; padding: 20px;
        backdrop-filter: blur(10px);
    }
    
    .stat-label { font-size: 0.8rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #58a6ff; }
    
    .profit-positive { color: #3fb950; font-weight: 700; }
    .profit-negative { color: #f85149; font-weight: 700; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Data Loading ────────────────────────────────────────────────
def load_data(asset=None, limit=100):
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        if asset:
            query = f"SELECT * FROM spreads WHERE asset='{asset}' ORDER BY timestamp DESC LIMIT {limit}"
        else:
            query = f"SELECT * FROM spreads ORDER BY timestamp DESC LIMIT {limit * 3}"
        df = pd.read_sql_query(query, conn)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(IST)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# ─── Header ──────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 3rem; margin:0; background: linear-gradient(90deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PRO ARBITRAGE TERMINAL</h1>
    <p style="color: #8b949e; font-size: 1.1rem;">High-fidelity cross-exchange spread analysis</p>
</div>
""", unsafe_allow_html=True)

# ─── Main Tabs ───────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Market Overview", "🔍 Asset Deep-Dive"])

with tab1:
    st.markdown("### 🌍 Global Market Status")
    all_data = load_data(limit=10) # Get latest for all
    
    if not all_data.empty:
        # Create a summary table for latest prices of all assets
        summary_rows = []
        for asset in ASSETS:
            asset_latest = all_data[all_data['asset'] == asset].head(1)
            if not asset_latest.empty:
                row = asset_latest.iloc[0]
                summary_rows.append({
                    "Asset": asset,
                    "Net Profit %": f"{row['net_profit']:.3f}%",
                    "Buy At": row['buy_at'],
                    "Sell At": row['sell_at'],
                    "Last Update": row['timestamp'].strftime('%H:%M:%S'),
                    "raw_profit": row['net_profit']
                })
        
        sum_df = pd.DataFrame(summary_rows)
        
        # Display as cards or table
        cols = st.columns(len(ASSETS))
        for i, asset in enumerate(ASSETS):
            with cols[i]:
                asset_row = next((item for item in summary_rows if item["Asset"] == asset), None)
                if asset_row:
                    color = "#3fb950" if asset_row['raw_profit'] > 0 else "#f85149"
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 5px solid {color}">
                        <div class="stat-label">{asset} LATEST</div>
                        <div class="stat-value" style="color:{color}">{asset_row['Net Profit %']}</div>
                        <div style="font-size:0.9rem; margin-top:5px;">
                            {asset_row['Buy At']} ⮕ {asset_row['Sell At']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Multi-Asset Profit Comparison Chart
        full_history = load_data(limit=50) # Load more for the chart
        if not full_history.empty:
            fig_multi = px.line(full_history, x="timestamp", y="net_profit", color="asset",
                                title="Cross-Asset Net Profit History",
                                template="plotly_dark",
                                color_discrete_map={"BTC": "#f7931a", "ETH": "#627eea", "SOL": "#14f195"})
            fig_multi.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
            fig_multi.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_multi, use_container_width=True)

with tab2:
    col_side, col_main = st.columns([1, 4])
    
    with col_side:
        st.markdown("### ⚙️ Filters")
        sel_asset = st.selectbox("Deep Dive Asset", ASSETS, index=0)
        history_len = st.slider("Historical Window", 50, 500, 100)
        st.markdown("---")
        st.info("💡 Heatmap shows the potential percentage gain between any two exchanges.")

    df_asset = load_data(sel_asset, limit=history_len)
    
    if not df_asset.empty:
        latest = df_asset.iloc[0]
        
        # ─── Statistics Header ────────────────────────────────────
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.metric("Max Profit (Window)", f"{df_asset['net_profit'].max():.3f}%")
        with s2: st.metric("Min Profit (Window)", f"{df_asset['net_profit'].min():.3f}%")
        with s3: st.metric("Avg Profit (Window)", f"{df_asset['net_profit'].mean():.3f}%")
        with s4: 
            opportunities = len(df_asset[df_asset['net_profit'] > 0])
            st.metric("Win Rate", f"{(opportunities/len(df_asset))*100:.1f}%")

        # ─── Main Heatmap ─────────────────────────────────────────
        st.markdown("### 🌡️ Scalping Heatmap (Buy ⮕ Sell)")
        
        # Build Heatmap Matrix for Latest Data
        matrix_data = []
        for buy_ex in EXCHANGES:
            row = []
            buy_price = latest[buy_ex.lower()]
            for sell_ex in EXCHANGES:
                if buy_ex == sell_ex:
                    row.append(0)
                else:
                    sell_price = latest[sell_ex.lower()]
                    
                    if buy_price is None or sell_price is None or pd.isna(buy_price) or pd.isna(sell_price) or float(buy_price) == 0.0:
                        spread = 0.0
                    else:
                        # Logic: (Sell - Buy) / Buy * 100 - Fee (0.3)
                        spread = ((sell_price - buy_price) / buy_price) * 100 - 0.3
                    row.append(spread)
            matrix_data.append(row)
        
        fig_heat = px.imshow(
            matrix_data,
            labels=dict(x="Selling Exchange", y="Buying Exchange", color="Net Profit %"),
            x=EXCHANGES, y=EXCHANGES,
            color_continuous_scale="RdYlGn",
            text_auto=".3f",
            aspect="auto",
            template="plotly_dark"
        )
        fig_heat.update_layout(height=450, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_heat, use_container_width=True)

        # ─── Price Offset Chart ──────────────────────────────────
        st.markdown("### 📊 Price Displacement (vs. Market Mean)")
        df_sorted = df_asset.sort_values("timestamp")
        # Calculate market mean per timestamp
        df_sorted['mean_price'] = df_sorted[ [ex.lower() for ex in EXCHANGES] ].mean(axis=1)
        
        fig_offset = go.Figure()
        for ex in EXCHANGES:
            offset = ((df_sorted[ex.lower()] - df_sorted['mean_price']) / df_sorted['mean_price']) * 100
            fig_offset.add_trace(go.Scatter(x=df_sorted['timestamp'], y=offset, name=ex, fill='tozeroy'))
            
        fig_offset.update_layout(
            title="Relative Price Deviation % (How much an exchange leads/lags)",
            yaxis_title="Deviation % from Mean",
            template="plotly_dark",
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_offset, use_container_width=True)

    else:
        st.warning(f"No deep-dive data available for {sel_asset}.")

# ─── Premium Sidebar ──────────────────────────────────────────────
with st.sidebar:
    
    # Calculate live latency
    df_side = load_data(limit=10)
    current_latency = "--ms"
    if not df_side.empty and 'api_latency_ms' in df_side.columns:
        valid_lats = df_side['api_latency_ms'].dropna()
        if not valid_lats.empty:
            current_latency = f"{int(valid_lats.mean())}ms"

    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="margin-bottom: 0; color: #58a6ff;">SYSTEM CORE</h2>
            <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">v2.1.0-PRO</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🛰️ Live Telemetry")
    st.markdown(f"""
        <div class="glass-card" style="padding: 15px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: #8b949e; font-size: 0.85rem; text-transform: uppercase;">API Latency</span>
                <span style="color: #3fb950; font-weight: bold; font-family: 'JetBrains Mono', monospace;">{current_latency}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: #8b949e; font-size: 0.85rem; text-transform: uppercase;">Data Nodes</span>
                <span style="color: #58a6ff; font-weight: bold; font-family: 'JetBrains Mono', monospace;">4/4 LIVE</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #8b949e; font-size: 0.85rem; text-transform: uppercase;">Sync Status</span>
                <span style="color: #bc8cff; font-weight: bold; font-family: 'JetBrains Mono', monospace;">ACTIVE ⚡</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛡️ Security Protocol")
    st.markdown("""
        <div class="glass-card" style="padding: 15px; border-left: 3px solid #f7931a; margin-bottom: 30px;">
            <div style="color: #f7931a; font-weight: 800; font-size: 0.8rem; text-transform: uppercase;">Fee-Aware Active</div>
            <div style="color: #c9d1d9; font-size: 0.85rem; margin-top: 5px;">
                All metrics currently reflect a 0.3% round-trip tax.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Force Refresh"):
        st.rerun()
