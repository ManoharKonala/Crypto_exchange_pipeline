import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import timezone, timedelta

# ─── Config ───────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "crypto_arb_db"
COLLECTION = "spreads"
IST = timezone(timedelta(hours=5, minutes=30))

st.set_page_config(
    page_title="₿ Arbitrage Scanner",
    page_icon="📈",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #f7931a, #ffb347, #f7931a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        color: #8892b0;
        font-size: 1rem;
        font-weight: 400;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(247, 147, 26, 0.15);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-value.spread-positive { color: #00e676; }
    .metric-value.spread-negative { color: #ff5252; }
    .metric-value.price { color: #64ffda; }

    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(247,147,26,0.3), transparent);
        margin: 1.5rem 0;
    }

    /* Chart container */
    .chart-section h3 {
        color: #ccd6f6;
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }

    /* Info box */
    .info-box {
        background: rgba(100, 255, 218, 0.06);
        border-left: 3px solid #64ffda;
        border-radius: 0 8px 8px 0;
        padding: 0.8rem 1.2rem;
        color: #8892b0;
        font-size: 0.85rem;
        margin-top: 1rem;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        background: rgba(0, 230, 118, 0.15);
        color: #00e676;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #f7931a, #e8850f);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ffb347, #f7931a);
        box-shadow: 0 4px 20px rgba(247, 147, 26, 0.4);
        transform: translateY(-1px);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        color: #ccd6f6;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>₿ Bitcoin Arbitrage Scanner</h1>
    <p>Real-time spread monitoring &mdash; Kraken vs CoinGecko Global Average</p>
</div>
""", unsafe_allow_html=True)

# ─── DB Connection ────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return MongoClient(MONGO_URI)

try:
    client = get_client()
    db = client[DB_NAME]
    collection = db[COLLECTION]

    # Controls row
    ctrl_col1, ctrl_col2 = st.columns([1, 5])
    with ctrl_col1:
        if st.button("🔄  Refresh"):
            st.rerun()
    with ctrl_col2:
        st.markdown('<span class="status-badge">● PIPELINE ACTIVE</span>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ─── Fetch Data ───────────────────────────────────────────────
    items = list(collection.find().sort("timestamp", -1).limit(100))

    if items:
        df = pd.DataFrame(items)
        # Convert UTC timestamps to IST for display
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize("UTC").dt.tz_convert(IST)
        latest = df.iloc[0]

        # ─── Metric Cards ────────────────────────────────────────
        spread_val = latest["spread_pct"]
        spread_class = "spread-positive" if spread_val >= 0 else "spread-negative"
        spread_icon = "▲" if spread_val >= 0 else "▼"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Current Spread</div>
                <div class="metric-value {spread_class}">{spread_icon} {spread_val:.4f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Kraken Price</div>
                <div class="metric-value price">${latest['price_kraken']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CoinGecko Price</div>
                <div class="metric-value price">${latest['price_cg']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ─── Spread Chart ────────────────────────────────────────
        st.markdown('<div class="chart-section"><h3>📈 Spread Trend (Last 100 Points)</h3></div>', unsafe_allow_html=True)

        df_chart = df.sort_values(by="timestamp")

        fig = go.Figure()

        # Gradient fill area
        fig.add_trace(go.Scatter(
            x=df_chart["timestamp"],
            y=df_chart["spread_pct"],
            mode="lines+markers",
            name="Spread %",
            line=dict(color="#f7931a", width=2.5, shape="spline"),
            marker=dict(size=5, color="#ffb347", line=dict(width=1, color="#f7931a")),
            fill="tozeroy",
            fillcolor="rgba(247, 147, 26, 0.08)",
            hovertemplate="<b>%{x|%H:%M:%S}</b><br>Spread: %{y:.4f}%<extra></extra>"
        ))

        # Zero line
        fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#8892b0"),
            xaxis=dict(
                title="Time (IST)",
                gridcolor="rgba(255,255,255,0.04)",
                tickformat="%H:%M:%S",
                showline=False,
            ),
            yaxis=dict(
                title="Spread %",
                gridcolor="rgba(255,255,255,0.04)",
                zerolinecolor="rgba(255,255,255,0.1)",
                showline=False,
                ticksuffix="%",
            ),
            margin=dict(l=40, r=20, t=20, b=40),
            height=400,
            hovermode="x unified",
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

        # ─── Price Comparison Chart ──────────────────────────────
        st.markdown('<div class="chart-section"><h3>💰 Price Comparison</h3></div>', unsafe_allow_html=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_chart["timestamp"], y=df_chart["price_kraken"],
            name="Kraken",
            line=dict(color="#64ffda", width=2, shape="spline"),
            hovertemplate="<b>Kraken</b><br>$%{y:,.2f}<extra></extra>"
        ))
        fig2.add_trace(go.Scatter(
            x=df_chart["timestamp"], y=df_chart["price_cg"],
            name="CoinGecko",
            line=dict(color="#f7931a", width=2, shape="spline"),
            hovertemplate="<b>CoinGecko</b><br>$%{y:,.2f}<extra></extra>"
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#8892b0"),
            xaxis=dict(
                title="Time (IST)",
                gridcolor="rgba(255,255,255,0.04)",
                tickformat="%H:%M:%S",
                showline=False,
            ),
            yaxis=dict(
                title="Price (USD)",
                gridcolor="rgba(255,255,255,0.04)",
                showline=False,
                tickprefix="$",
            ),
            margin=dict(l=40, r=20, t=20, b=40),
            height=350,
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="center", x=0.5,
                font=dict(size=12)
            ),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # ─── Stats Summary ───────────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="info-box">
            <strong>Stats</strong> &mdash;
            Data points: <strong>{len(df)}</strong> &ensp;|&ensp;
            Avg Spread: <strong>{df['spread_pct'].mean():.4f}%</strong> &ensp;|&ensp;
            Max Spread: <strong>{df['spread_pct'].max():.4f}%</strong> &ensp;|&ensp;
            Min Spread: <strong>{df['spread_pct'].min():.4f}%</strong>
        </div>
        """, unsafe_allow_html=True)

        # Raw data
        with st.expander("📋 View Raw Data"):
            st.dataframe(df.drop(columns=["_id"], errors="ignore"), use_container_width=True)

    else:
        st.warning("⏳ No data found. Make sure `ingest.py` is running and collecting data.")

except Exception as e:
    st.error(f"❌ MongoDB connection error: {e}")
