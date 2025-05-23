import os
import time
import requests
from datetime import datetime
import pandas as pd
from dhan_market_feed import DhanOptionsMarketFeed

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

print("\U0001F194 Client ID:", CLIENT_ID)
print("\U0001F511 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# Initialize DHAN Market Feed
feed = DhanOptionsMarketFeed(CLIENT_ID, ACCESS_TOKEN)

# --- CONFIG ---
ENTRY_START_TIME = "09:15"
ENTRY_END_TIME = "15:00"
STOP_LOSS_POINTS = 50
TARGET_POINTS = 25
TRAILING_SL_STEP = 5
MAX_ALLOCATION = 70000
QUANTITY = 50
ORDER_TYPE = "LIMIT"
BUFFER = 0.05
DAILY_TRADE_LIMIT = 5

SIGNAL_SYMBOL = "1330"  # NIFTY 50 Index (verify from Dhan)
SYMBOL_CE = "12599298"  # Example NIFTY CE security ID
SYMBOL_PE = "12604674"  # Example NIFTY PE security ID

ce_trades = 0
pe_trades = 0
open_trades = []

# --- UTILS ---
def fetch_candles(symbol, interval, limit=100):
    """Fetch historical candles using DHAN API"""
    endpoint = "/historical"
    params = {
        'security_id': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = feed._make_request(endpoint, params=params)
        return response.get('candles', []) if response else []
    except Exception as e:
        print("❌ Candle fetch error:", e)
    return []

def compute_ema(prices, period):
    return pd.Series(prices).ewm(span=period).mean().tolist()

def get_macd_and_ema_signal(symbol):
    candles = fetch_candles(symbol, "3minute", 100)
    if len(candles) < 30:
        print("⚠️ Not enough candles")
        return False

    close_prices = [x['close'] for x in candles[:-1]]  # skip the forming candle

    ema5 = compute_ema(close_prices, 5)
    ema8 = compute_ema(close_prices, 8)
    ema13 = compute_ema(close_prices, 13)

    ema_up = ema5[-1] > ema8[-1] > ema13[-1] and ema5[-1] > ema5[-2] and ema8[-1] > ema8[-2]
    if not ema_up:
        print("⚠️ EMA condition not met")
        return False

    macd_line = pd.Series(close_prices).ewm(span=12).mean() - pd.Series(close_prices).ewm(span=26).mean()
    signal_line = macd_line.ewm(span=9).mean()
    hist = macd_line - signal_line

    print(f"📊 MACD: {macd_line.iloc[-1]:.2f}, Signal: {signal_line.iloc[-1]:.2f}, Hist: {hist.iloc[-1]:.2f}")

    if macd_line.iloc[-1] <= signal_line.iloc[-1] or hist.iloc[-1] <= 0:
        print("⚠️ MACD condition not met")
        return False

    return True

def get_latest_price(symbol):
    """Get LTP from market feed"""
    data = feed.get_latest_data(symbol)
    return data.get('ltp') if data else None

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
        response = feed._make_request("/orders", method="POST", data=payload)
        if response:
            print(f"✅ Order placed: {symbol} @ {price}")
            return response
        else:
            print("❌ Order error")
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

def initialize_market_feed():
    """Initialize and connect to market feed"""
    if not feed.connect_websocket():
        print("❌ Failed to connect to market feed")
        return False
    
    # Subscribe to required symbols
    feed.subscribe_to_symbols([SIGNAL_SYMBOL, SYMBOL_CE, SYMBOL_PE])
    return True

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not initialize_market_feed():
        exit(1)

    try:
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

            if get_macd_and_ema_signal(symbol):
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
                action = manage_open_trade(
                    trade['entry_price'], 
                    curr_price, 
                    trade['sl'], 
                    trade['tp'], 
                    trade['tsl'], 
                    trade['direction']
                )
                if action == "exit":
                    open_trades.remove(trade)

    except KeyboardInterrupt:
        print("\n🛑 Manual interruption detected")
    finally:
        feed.close_connection()
        print("🏁 Day cycle finished.")
