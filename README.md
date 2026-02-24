# ₿ Pro Arbitrage Matrix Terminal

A professional-grade, real-time cryptocurrency arbitrage scanner. This tool monitors price discrepancies across multiple exchanges and multiple assets, accounting for trading fees to identify actual net-profit opportunities.

## 🚀 Pro Features
- **Multi-Asset Ingestion**: Tracks **BTC, ETH, and SOL** simultaneously.
- **Multi-Exchange Matrix**: Real-time Bid/Ask data from **Kraken, Coinbase, Bitfinex, and Gemini**.
- **Fee-Aware Modeling**: Automatically subtracts a **0.3% round-trip fee** from gross spreads.
- **Interactive Terminal**: 
    - **Market Overview**: Global heat-check of all tracked assets.
    - **Deep-Dive Analytics**: Individual asset performance, heatmaps, and price displacement charts.
- **Zero Authentication**: Built 100% on public APIs (No KYC/API Keys required for monitoring).
- **SQLite Backend**: Efficient, serverless local data persistence.

## 🛠️ Setup

1.  **Installation**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start Data Ingestion**:
    The ingestion engine cycles through assets every 30 seconds.
    ```bash
    python src/ingest.py
    ```

3.  **Launch the Dashboard**:
    Open the high-fidelity interactive terminal.
    ```bash
    streamlit run src/dashboard.py
    ```

## 📂 Project Structure
- `src/ingest.py`: Multi-threaded data logic, Bid/Ask scrapers, and SQLite persistence.
- `src/dashboard.py`: Streamlit-based Pro Terminal with interactive Plotly visualizations.
- `crypto_arb.db`: Local SQLite database (Auto-created).

## 📊 Analytics Deep Dive
- **Net Profit**: Gross Spread minus simulated exchange fees.
- **Price Displacement**: Measures how much a specific exchange price deviates from the global market mean.
- **Scalping Heatmap**: Inter-exchange profitability matrix (Buy on X ⮕ Sell on Y).

---
*Developed for high-fidelity crypto market monitoring.*
