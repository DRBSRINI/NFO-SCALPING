import os
import time
import requests
from datetime import datetime, timedelta
print("🚀 Bot Started Successfully!")

# === ENVIRONMENT VARIABLES ===
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
APP_NAME = os.getenv("APP_NAME", "SSAA")

# === DHAN API ENDPOINTS ===
ORDER_URL = "https://api.dhan.co/orders"
LTP_URL = "https://api.dhan.co/market/quote"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Access-Token": ACCESS_TOKEN,
    "Client-Id": CLIENT_ID
}

# === SYMBOL CONFIG ===
SYMBOL = "NIFTY 50"
EXCHANGE_SEGMENT = "NSE"
INSTRUMENT = {
    "securityId": "1333",  # Example for NIFTY index
    "symbol": SYMBOL,
    "exchangeSegment": EXCHANGE_SEGMENT
}

# === SIGNAL STRATEGY ===
def is_buy_signal(candles):
    if len(candles) < 3:
        return False
    c1 = candles[-3]
    c2 = candles[-2]
    return c2["close"] > c2["open"] and c2["close"] > c1["close"]

# === HISTORICAL DATA ===
def fetch_ohlc(symbol):
    url = f"https://api.dhan.co/market/quotes/historical"
    params = {
        "securityId": INSTRUMENT["securityId"],
        "exchangeSegment": INSTRUMENT["exchangeSegment"],
        "instrument": SYMBOL,
        "interval": "3minute",
        "fromDate": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "toDate": datetime.now().strftime("%Y-%m-%d")
    }
    res = requests.get(url, headers=HEADERS, params=params)
    return res.json().get("data", [])

# === PLACE ORDER ===
def place_order():
    order_payload = {
        "securityId": INSTRUMENT["securityId"],
        "exchangeSegment": INSTRUMENT["exchangeSegment"],
        "transactionType": "BUY",
        "orderType": "MARKET",
        "productType": "INTRADAY",
        "quantity": 25,
        "price": 0.0,
        "disclosedQuantity": 0,
        "orderValidity": "DAY",
        "afterMarketOrder": False
    }
    response = requests.post(ORDER_URL, headers=HEADERS, json=order_payload)
    print("📤 Order Response:", response.json())

# === MAIN ===
if __name__ == "__main__":
    while True:
        try:
            candles = fetch_ohlc(SYMBOL)
            if is_buy_signal(candles):
                print("✅ Buy Signal Triggered")
                place_order()
            else:
                print("❌ No Signal")
        except Exception as e:
            print("⚠️ Error:", e)

        time.sleep(180)  # wait for 3 minutes
