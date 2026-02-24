import time
import requests
import schedule
import sqlite3
from datetime import datetime, timezone
import os

# ─── Config ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto_arb.db")

PROVIDERS = {
    "Kraken": {
        "url": "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
        "parser": lambda r: float(r["result"]["XXBTZUSD"]["c"][0])
    },
    "Coinbase": {
        "url": "https://api.coinbase.com/v2/prices/BTC-USD/spot",
        "parser": lambda r: float(r["data"]["amount"] or 0)
    },
    "Bitfinex": {
        "url": "https://api-pub.bitfinex.com/v2/ticker/tBTCUSD",
        "parser": lambda r: float(r[6])  # LAST_PRICE is index 6
    },
    "Gemini": {
        "url": "https://api.gemini.com/v1/pubticker/btcusd",
        "parser": lambda r: float(r["last"])
    }
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we need to migrate from the old schema
    cursor.execute("PRAGMA table_info(spreads)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if columns and "kraken" not in columns:
        print("Old schema detected. Migrating to Price Matrix schema...")
        cursor.execute("DROP TABLE spreads")
    
    # New schema for Matrix
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spreads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            best_spread REAL,
            buy_at TEXT,
            sell_at TEXT,
            kraken REAL,
            coinbase REAL,
            bitfinex REAL,
            gemini REAL
        )
    ''')
    conn.commit()
    conn.close()

def fetch_price(name, config):
    try:
        res = requests.get(config["url"], timeout=10)
        res.raise_for_status()
        return config["parser"](res.json())
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

def job():
    try:
        prices = {}
        for name, config in PROVIDERS.items():
            price = fetch_price(name, config)
            if price:
                prices[name] = price
        
        if len(prices) < 2:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Not enough price data (Providers active: {list(prices.keys())})")
            return

        # Find Min and Max
        min_exchange = min(prices, key=prices.get)
        max_exchange = max(prices, key=prices.get)
        
        min_price = prices[min_exchange]
        max_price = prices[max_exchange]
        
        best_spread = ((max_price - min_price) / min_price) * 100
        
        # Timestamp
        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()
        
        # Storage
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO spreads (timestamp, best_spread, buy_at, sell_at, kraken, coinbase, bitfinex, gemini)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp_str, 
            best_spread, 
            min_exchange, 
            max_exchange,
            prices.get("Kraken"),
            prices.get("Coinbase"),
            prices.get("Bitfinex"),
            prices.get("Gemini")
        ))
        conn.commit()
        conn.close()
        
        # Console Output
        print(f"[{now.strftime('%H:%M:%S')}] Best Spread: {best_spread:.4f}% | Buy: {min_exchange} (${min_price:,.2f}) | Sell: {max_exchange} (${max_price:,.2f})")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Critical Error: {e}")

if __name__ == "__main__":
    print("Initializing SQLite Database (Price Matrix)...")
    init_db()
    
    print("Starting Multi-Exchange Ingestion...")
    print(f"Tracking: {', '.join(PROVIDERS.keys())}")
    
    # Run immediately once
    job()
    
    # Schedule
    schedule.every(30).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
