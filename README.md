# No-KYC Crypto Arbitrage Scanner

This project is a real-time data pipeline that detects price differences for Bitcoin (BTC) between a global average (CoinGecko) and a specific exchange (Kraken).

## Features
- **Zero Authentication:** Uses only public APIs.
- **Rate Limit Aware:** Scheduled to run every 30 seconds.
- **Data Persistence:** Stores data in a local MongoDB database.
- **Visual Dashboard:** Streamlit dashboard to visualize spread history.

## Setup

1.  **Prerequisites:**
    - Python 3.12+
    - MongoDB installed and running locally on port 27017.

2.  **Installation:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Running the Ingestion Script:**
    ```bash
    python src/ingest.py
    ```

4.  **Running the Dashboard:**
    ```bash
    streamlit run src/dashboard.py
    ```

## Project Structure
- `src/ingest.py`: Main data fetcher and logic engine.
- `src/dashboard.py`: Streamlit frontend for visualization.
