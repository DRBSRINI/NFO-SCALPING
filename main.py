import os
import time
import requests
from datetime import datetime

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

print("🆔 Client ID:", CLIENT_ID)
print("🔑 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# Headers for API
HEADERS = {
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- CONFIG ---
ENTRY_START_TIME = "09:26"
ENTRY_END_TIME = "15:00"
MAX_TRADES_PER_TYPE = 5
STOP_LOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_STEP = 5
MAX_ALLOCATION = 70000
QUANTITY = 50  # 1 lot assumed to be 50
ORDER_TYPE = "LIMIT"
BUFFER = 0.05

# --- PLACEHOLDER FUNCTIONS ---
def get_latest_price(symbol):
    """Simulate fetching latest price for symbol from Dhan."""
    url = f"https://api.dhan.co/market/quote/{symbol}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data['close']
    else:
        print(f"Failed to fetch price for {symbol}:", response.text)
        return None

def get_multitimeframe_signal():
    """Simulate checking multi-timeframe signals. Replace with real indicator logic."""
    # Placeholder: All conditions return True to simulate entry
    return True

def place_order(symbol, side, qty, price):
    """Place order via Dhan API."""
    url = "https://api.dhan.co/orders"
    payload = {
        "security_id": symbol,
        "exchange_segment": "NSE",
        "transaction_type": side,
        "order_type": ORDER_TYPE,
        "quantity": qty,
        "price": price,
        "product_type": "INTRADAY",
        "validity": "DAY"
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"✅ Order placed: {side} {symbol} @ {price}")
        return response.json()
    else:
        print("❌ Order failed:", response.text)
        return None

# --- STRATEGY EXECUTION LOOP ---
ce_trades = 0
pe_trades = 0

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    if current_time < ENTRY_START_TIME:
        print("Waiting for entry window to begin...")
        time.sleep(30)
        continue

    if current_time >= ENTRY_END_TIME:
        print("Entry window closed.")
        break

    if ce_trades >= MAX_TRADES_PER_TYPE and pe_trades >= MAX_TRADES_PER_TYPE:
        print("Max trades executed. Halting new entries.")
        break

    if get_multitimeframe_signal():
        option_type = "CE" if ce_trades < MAX_TRADES_PER_TYPE else "PE"
        symbol = f"NIFTY{option_type}ATM"  # Replace with real logic to find ATM symbol
        price = get_latest_price(symbol)
        if not price:
            continue

        limit_price = round(price + BUFFER if option_type == "CE" else price - BUFFER, 2)
        order_response = place_order(symbol, "BUY", QUANTITY, limit_price)

        if order_response:
            if option_type == "CE":
                ce_trades += 1
            else:
                pe_trades += 1
        time.sleep(60)  # wait before checking again
    else:
        print("No entry conditions met.")
        time.sleep(30)

print("Trading cycle complete.")
