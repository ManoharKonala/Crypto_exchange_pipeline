import time
import requests
import schedule
import sqlite3
from datetime import datetime, timezone
import os

# Constants
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto_arb.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spreads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            price_cg REAL,
            price_kraken REAL,
            spread_pct REAL
        )
    ''')
    conn.commit()
    conn.close()

def job():
    try:
        # Fetch Data
        cg_res = requests.get(COINGECKO_URL, timeout=10)
        cg_res.raise_for_status()
        cg_data = cg_res.json()
        price_cg = float(cg_data['bitcoin']['usd'])

        kr_res = requests.get(KRAKEN_URL, timeout=10)
        kr_res.raise_for_status()
        kr_data = kr_res.json()
        # Kraken Response structure: result -> XXBTZUSD -> c -> [price, volume]
        price_kraken = float(kr_data['result']['XXBTZUSD']['c'][0])
        
        # Calculation
        spread_pct = ((price_kraken - price_cg) / price_cg) * 100
        
        # Timestamp (ISO format for easier SQLite handling)
        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()
        
        # Storage
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO spreads (timestamp, price_cg, price_kraken, spread_pct)
            VALUES (?, ?, ?, ?)
        ''', (timestamp_str, price_cg, price_kraken, spread_pct))
        conn.commit()
        conn.close()
        
        # Console Output
        print(f"[{now.strftime('%H:%M:%S')}] CG: ${price_cg:,.2f} | KR: ${price_kraken:,.2f} | Spread: {spread_pct:.4f}%")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

if __name__ == "__main__":
    print("Initializing SQLite Database...")
    init_db()
    
    print("Starting Crypto Arbitrage Ingestion (SQLite)...")
    print("Press Ctrl+C to stop.")
    
    # Run immediately once to verify
    job()
    
    # Schedule
    schedule.every(30).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
