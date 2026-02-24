import time
import requests
import schedule
import sqlite3
from datetime import datetime, timezone
import os

# ─── Config ───────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "crypto_arb.db")

# Assets to track
ASSETS = ["BTC", "ETH", "SOL"]

# Standard Trading Fee (Avg 0.15% per trade, buy + sell = 0.3%)
TRADING_FEE_PCT = 0.15 

# 🔔 Telegram Alerts Config
# Set these in your Environment Variables for real usage
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
PROFIT_THRESHOLD = 0.5  # Trigger alert if net_profit > 0.5%

# State to handle anti-spam (last alert time per asset)
LAST_ALERTS = {} 
COOLDOWN_SECONDS = 600 # 10 minutes

PROVIDERS = {
    "Kraken": {
        "url": lambda s: f"https://api.kraken.com/0/public/Ticker?pair={s}USD" if s != "BTC" else "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
        "parser": lambda r, s: (
            float(r["result"][list(r["result"].keys())[0]]["a"][0]), # ASK (Buy Price)
            float(r["result"][list(r["result"].keys())[0]]["b"][0])  # BID (Sell Price)
        )
    },
    "Coinbase": {
        "url": lambda s: f"https://api.coinbase.com/v2/prices/{s}-USD/spot",
        "parser": lambda r, s: (float(r["data"]["amount"]), float(r["data"]["amount"])) # Coinbase Spot doesn't give bid/ask easily, using spot for both
    },
    "Bitfinex": {
        "url": lambda s: f"https://api-pub.bitfinex.com/v2/ticker/t{s}USD",
        "parser": lambda r, s: (float(r[2]), float(r[0])) # ASK is index 2, BID is index 0
    },
    "Gemini": {
        "url": lambda s: f"https://api.gemini.com/v1/pubticker/{s.lower()}usd",
        "parser": lambda r, s: (float(r["ask"]), float(r["bid"]))
    }
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we need to migrate (if 'asset' column is missing)
    cursor.execute("PRAGMA table_info(spreads)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if columns and "asset" not in columns:
        print("Migrating database to Pro schema...")
        cursor.execute("DROP TABLE spreads")
    
    # New schema with asset and net_profit support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spreads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            asset TEXT,
            best_spread REAL,
            net_profit REAL,
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

def fetch_data(name, config, symbol):
    try:
        url = config["url"](symbol)
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return config["parser"](res.json(), symbol)
    except Exception as e:
        return None

def send_telegram_alert(asset, spread, buy_at, sell_at):
    if not BOT_TOKEN or not CHAT_ID:
        return
    
    # Anti-spam check
    now = time.time()
    if asset in LAST_ALERTS:
        if now - LAST_ALERTS[asset] < COOLDOWN_SECONDS:
            return
            
    message = (
        f"🚀 *Arbitrage Detected: {asset}*\n\n"
        f"💰 *Net Profit:* `{spread:.3f}%` (After Fees)\n"
        f"🛒 *Buy:* {buy_at}\n"
        f"💹 *Sell:* {sell_at}\n\n"
        f"🌐 [Open Matrix Dashboard](http://localhost:8501)"
    )
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        LAST_ALERTS[asset] = now
        print(f"🔔 Telegram Alert sent for {asset}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def job():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for asset in ASSETS:
        try:
            asks = {} # Prices we BUY at
            bids = {} # Prices we SELL at
            
            for name, config in PROVIDERS.items():
                data = fetch_data(name, config, asset)
                if data:
                    asks[name], bids[name] = data
            
            if len(asks) < 2:
                continue

            # Pure Arb Logic: Buy at lowest ASK, Sell at highest BID
            min_exchange = min(asks, key=asks.get)
            max_exchange = max(bids, key=bids.get)
            
            buy_price = asks[min_exchange]
            sell_price = bids[max_exchange]
            
            # Spread calculation
            gross_spread = ((sell_price - buy_price) / buy_price) * 100
            
            # Net Profit after trading fees (Approx 0.3% total for round trip)
            net_profit = gross_spread - (TRADING_FEE_PCT * 2)
            
            now = datetime.now(timezone.utc)
            
            cursor.execute('''
                INSERT INTO spreads (timestamp, asset, best_spread, net_profit, buy_at, sell_at, kraken, coinbase, bitfinex, gemini)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.isoformat(), 
                asset,
                gross_spread,
                net_profit,
                min_exchange, 
                max_exchange,
                asks.get("Kraken"),
                asks.get("Coinbase"),
                asks.get("Bitfinex"),
                asks.get("Gemini")
            ))
            
            # Console output
            status = "🔥 PROFIT" if net_profit > 0 else "❄️ Watch"
            print(f"[{now.strftime('%H:%M:%S')}] {asset} | {status} | Net: {net_profit:.3f}% | Buy: {min_exchange} Sell: {max_exchange}")
            
            # 🔔 Trigger Telegram Alert
            if net_profit >= PROFIT_THRESHOLD:
                send_telegram_alert(asset, net_profit, min_exchange, max_exchange)
            
        except Exception as e:
            print(f"Error processing {asset}: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"🚀 Multi-Asset Ingest started: {', '.join(ASSETS)}")
    print(f"Fees Integrated: {TRADING_FEE_PCT*2}% total round-trip")
    
    job()
    schedule.every(30).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
