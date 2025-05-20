import os
import time
import requests
from datetime import datetime, timedelta

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

print("\U0001F194 Client ID:", CLIENT_ID)
print("\U0001F511 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# Headers for API
HEADERS = {
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- CONFIG ---
ENTRY_START_TIME = "09:26"
ENTRY_END_TIME = "15:00"
STOP_LOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_STEP = 5
MAX_ALLOCATION = 70000
QUANTITY = 50
ORDER_TYPE = "LIMIT"
BUFFER = 0.05
DAILY_TRADE_LIMIT = 5
SYMBOL_CE = "NIFTY_CE_ATM"
SYMBOL_PE = "NIFTY_PE_ATM"

ce_trades = 0
pe_trades = 0
open_trades = []

# --- UTILS ---
def fetch_candles(symbol, interval, limit=2):
    url = f"https://api.dhan.co/market/candles?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['candles']
        else:
            print(f"❌ Candle fetch error ({interval}):", response.text)
            return []
    except Exception as e:
        print("❌ Candle API Exception:", e)
        return []

def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        diff = closes[-i] - closes[-i - 1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_multitimeframe_signal(symbol):
    intervals = {"3m": "3minute", "15m": "15minute", "1h": "1hour"}
    prices = {}

    for label, interval in intervals.items():
        candles = fetch_candles(symbol, interval)
        if len(candles) < 2:
            return False
        c0 = candles[-1]['close']
        c1 = candles[-2]['close']
        prices[label] = (c0, c1)

    # Rule checks
    for key in prices:
        c0, c1 = prices[key]
        if c0 <= c1:
            return False
        if (c0 - c1) / c1 < 0.01:
            return False

    rsi_candles = fetch_candles(symbol, "3minute", limit=16)
    if len(rsi_candles) < 15:
        return False
    close_prices = [x['close'] for x in rsi_candles]
    rsi = compute_rsi(close_prices)
    if rsi is None or rsi < 35 or rsi > 65:
        return False

    return True

def get_latest_price(symbol):
    url = f"https://api.dhan.co/market/quote/{symbol}"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()['close']
    except Exception as e:
        print("❌ Price fetch failed:", e)
    return None

def place_order(symbol, qty, price):
    payload = {
        "security_id": symbol,
        "exchange_segment": "NSE",
        "transaction_type": "BUY",
        "order_type": ORDER_TYPE,
        "quantity": qty,
        "price": price,
        "product_type": "INTRADAY",
        "validity": "DAY"
    }
    try:
        response = requests.post("https://api.dhan.co/orders", headers=HEADERS, json=payload)
        if response.status_code == 200:
            print(f"✅ Order placed: {symbol} @ {price}")
            return response.json()
        else:
            print("❌ Order error:", response.text)
    except Exception as e:
        print("❌ Order exception:", e)
    return None

def manage_open_trade(entry_price, current_price, sl, tp, tsl, direction):
    move = current_price - entry_price if direction == "CE" else entry_price - current_price
    if move >= tp:
        print("🎯 Target hit. Close position.")
        return "exit"
    elif move <= -sl:
        print("🛑 Stoploss hit. Close position.")
        return "exit"
    elif move >= tsl:
        print("🔁 Trail SL active")
    return "hold"

# --- STRATEGY LOOP ---
while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    if current_time < ENTRY_START_TIME:
        print("⏳ Waiting to start...")
        time.sleep(30)
        continue

    if current_time >= ENTRY_END_TIME:
        print("⏹️ Entry window closed.")
        break

    if ce_trades >= DAILY_TRADE_LIMIT and pe_trades >= DAILY_TRADE_LIMIT:
        print("✅ Max trades done for the day.")
        break

    option_type = "CE" if ce_trades < DAILY_TRADE_LIMIT else "PE"
    symbol = SYMBOL_CE if option_type == "CE" else SYMBOL_PE

    if get_multitimeframe_signal(symbol):
        price = get_latest_price(symbol)
        if not price:
            continue

        limit_price = round(price + BUFFER if option_type == "CE" else price - BUFFER, 2)
        order = place_order(symbol, QUANTITY, limit_price)
        if order:
            trade = {
                "symbol": symbol,
                "entry_price": limit_price,
                "sl": STOP_LOSS_POINTS,
                "tp": TARGET_POINTS,
                "tsl": TRAILING_SL_STEP,
                "direction": option_type
            }
            open_trades.append(trade)
            if option_type == "CE":
                ce_trades += 1
            else:
                pe_trades += 1
        time.sleep(60)
    else:
        print("❌ No entry match")
        time.sleep(30)

    for trade in open_trades[:]:
        curr_price = get_latest_price(trade['symbol'])
        if curr_price is None:
            continue
        action = manage_open_trade(trade['entry_price'], curr_price, trade['sl'], trade['tp'], trade['tsl'], trade['direction'])
        if action == "exit":
            open_trades.remove(trade)

print("🏁 Day cycle finished.")
