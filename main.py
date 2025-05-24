import os
import time
from datetime import datetime, timedelta
import pandas as pd
from dhan_market_feed import DhanOptionsMarketFeed

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

print("\U0001F194 Client ID:", CLIENT_ID)
print("\U0001F511 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

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

SYMBOL_CE = "12599298"
SYMBOL_PE = "12604674"

ce_trades = 0
pe_trades = 0
open_trades = []

# Store tick data
tick_data = {SYMBOL_CE: [], SYMBOL_PE: []}

def on_tick(tick):
    symbol = tick['instrument_token']
    price = tick['last_traded_price']
    timestamp = datetime.now()
    tick_data[symbol].append((timestamp, price))

def generate_candle(symbol):
    now = datetime.now()
    start = now - timedelta(minutes=3)
    recent_ticks = [p for p in tick_data[symbol] if p[0] >= start]
    if not recent_ticks:
        return None
    prices = [p[1] for p in recent_ticks]
    candle = {
        'open': prices[0],
        'high': max(prices),
        'low': min(prices),
        'close': prices[-1],
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S")
    }
    return candle

def compute_ema(prices, period):
    return pd.Series(prices).ewm(span=period).mean().tolist()

def check_strategy(symbol):
    candle = generate_candle(symbol)
    if not candle:
        print("⚠️ Not enough ticks for candle generation")
        return False

    close_prices = [p[1] for p in tick_data[symbol][-100:]]
    if len(close_prices) < 30:
        return False

    ema5 = compute_ema(close_prices, 5)
    ema8 = compute_ema(close_prices, 8)
    ema13 = compute_ema(close_prices, 13)

    if not (ema5[-1] > ema8[-1] > ema13[-1] and ema5[-1] > ema5[-2] and ema8[-1] > ema8[-2]):
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
    headers = {
        "access-token": ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        response = requests.post("https://api.dhan.co/orders", headers=headers, json=payload)
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

# --- START FEED ---
feed = DhanOptionsMarketFeed(CLIENT_ID, ACCESS_TOKEN)
feed.on_tick = on_tick
feed.subscribe([
    {"instrument_token": SYMBOL_CE, "segment": "NFO", "exchange": "NSE"},
    {"instrument_token": SYMBOL_PE, "segment": "NFO", "exchange": "NSE"}
])
feed.start()

print("📡 WebSocket started. Monitoring for signals...")

try:
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time >= ENTRY_END_TIME:
            print("⏹️ Entry window closed.")
            break

        if ce_trades < DAILY_TRADE_LIMIT and check_strategy(SYMBOL_CE):
            last_price = tick_data[SYMBOL_CE][-1][1] if tick_data[SYMBOL_CE] else None
            if last_price:
                limit_price = round(last_price + BUFFER, 2)
                order = place_order(SYMBOL_CE, QUANTITY, limit_price)
                if order:
                    ce_trades += 1
                    open_trades.append({"symbol": SYMBOL_CE, "entry_price": limit_price, "sl": STOP_LOSS_POINTS,
                                         "tp": TARGET_POINTS, "tsl": TRAILING_SL_STEP, "direction": "CE"})

        if pe_trades < DAILY_TRADE_LIMIT and check_strategy(SYMBOL_PE):
            last_price = tick_data[SYMBOL_PE][-1][1] if tick_data[SYMBOL_PE] else None
            if last_price:
                limit_price = round(last_price - BUFFER, 2)
                order = place_order(SYMBOL_PE, QUANTITY, limit_price)
                if order:
                    pe_trades += 1
                    open_trades.append({"symbol": SYMBOL_PE, "entry_price": limit_price, "sl": STOP_LOSS_POINTS,
                                         "tp": TARGET_POINTS, "tsl": TRAILING_SL_STEP, "direction": "PE"})

        for trade in open_trades[:]:
            last_price = tick_data[trade['symbol']][-1][1] if tick_data[trade['symbol']] else None
            if not last_price:
                continue
            action = manage_open_trade(trade['entry_price'], last_price, trade['sl'], trade['tp'], trade['tsl'], trade['direction'])
            if action == "exit":
                open_trades.remove(trade)

        time.sleep(5)

except KeyboardInterrupt:
    print("🛑 Interrupted by user")
finally:
    feed.stop()
    print("🏁 Day cycle finished.")
