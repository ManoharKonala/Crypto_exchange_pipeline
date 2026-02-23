import time
import requests
import schedule
from pymongo import MongoClient
from datetime import datetime, timezone

# Constants
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
MONGO_URI_LOCAL = "mongodb://localhost:27017/"
DB_NAME = "crypto_arb_db"
COLLECTION_NAME = "spreads"

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
        
        # Timestamp
        now = datetime.now(timezone.utc)
        
        # Document
        doc = {
            "timestamp": now,
            "price_cg": price_cg,
            "price_kraken": price_kraken,
            "spread_pct": spread_pct
        }
        
        # Storage
        client = MongoClient(MONGO_URI_LOCAL)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        collection.insert_one(doc)
        client.close()
        
        # Console Output
        print(f"[{now.strftime('%H:%M:%S')}] CG: ${price_cg:,.2f} | KR: ${price_kraken:,.2f} | Spread: {spread_pct:.2f}%")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")

if __name__ == "__main__":
    print("Starting Crypto Arbitrage Ingestion...")
    print("Press Ctrl+C to stop.")
    
    # Run immediately once to verify
    job()
    
    # Schedule
    schedule.every(30).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
