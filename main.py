import os
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
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
QUANTITY = 50
ORDER_TYPE = "LIMIT"
BUFFER = 0.05
DAILY_TRADE_LIMIT = 5

# Replace these with correct and active instrument tokens
SYMBOL_CE = "12599298"  # Check via Dhan's instrument API
SYMBOL_PE = "12604674"

tick_data = {SYMBOL_CE: [], SYMBOL_PE: []}
ce_trades = 0
pe_trades = 0
open_trades = []

# ---- TICK HANDLER ----
def on_tick(tick):
    print(f"📥 Tick received: {tick}")
    symbol = tick.get('instrument_token')
    price = tick.get('last_traded_price')
    if symbol and price:
        tick_data[symbol].append((datetime.now(), price))

# ---- CANDLE GENERATION ----
def generate_candle(symbol):
    now = datetime.now()
    start = now - timedelta(minutes=3)
    recent_ticks = [p for p in tick_data[symbol] if p[0] >= start]
    if not recent_ticks:
        print("⚠️ Not enough ticks for candle generation")
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

# ---- EMA / MACD ----
def compute_ema(prices, period):
    return pd.Series(prices).ewm(span=period).mean().tolist()

def check_strategy(symbol):
    candle = generate_candle(symbol)
    if not candle:
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

# ---- ORDER ----
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

# ---- SL/TP ----
def manage_open_trade(entry_price, current_price, sl, tp, tsl, direction):
    move = current_price - entry_price if direction == "CE" else entry_price - current_price
    if move >= tp:
        print("🎯 Target hit. Closing position.")
        return "exit"
    elif move <= -sl:
        print("🛑 Stoploss hit. Closing position.")
        return "exit"
    elif move >= tsl:
        print("🔁 Trailing SL active")
    return "hold"

# ---- START WEBSOCKET ----
feed = DhanOptionsMarketFeed(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
feed.on_tick = on_tick


feed.subscribe_instruments([
    {"instrument_token": SYMBOL_CE, "segment": "NFO", "exchange": "NSE"},
    {"instrument_token": SYMBOL_PE, "segment": "NFO", "exchange": "NSE"}
])

feed.start_websocket()
print("📡 WebSocket started. Waiting for ticks...")

# ---- STRATEGY LOOP ----
try:
    while True:
        now = datetime.now()
        if now.strftime("%H:%M") >= ENTRY_END_TIME:
            print("⏹️ Entry window closed.")
            break

        for symbol, direction in [(SYMBOL_CE, "CE"), (SYMBOL_PE, "PE")]:
            trades = ce_trades if direction == "CE" else pe_trades
            if trades < DAILY_TRADE_LIMIT and check_strategy(symbol):
                last_price = tick_data[symbol][-1][1] if tick_data[symbol] else None
                if last_price:
                    price = round(last_price + BUFFER if direction == "CE" else last_price - BUFFER, 2)
                    order = place_order(symbol, QUANTITY, price)
                    if order:
                        open_trades.append({
                            "symbol": symbol,
                            "entry_price": price,
                            "sl": STOP_LOSS_POINTS,
                            "tp": TARGET_POINTS,
                            "tsl": TRAILING_SL_STEP,
                            "direction": direction
                        })
                        if direction == "CE":
                            ce_trades += 1
                        else:
                            pe_trades += 1
        # Manage active trades
        for trade in open_trades[:]:
            current = tick_data[trade['symbol']][-1][1] if tick_data[trade['symbol']] else None
            if current:
                status = manage_open_trade(
                    trade['entry_price'], current, trade['sl'], trade['tp'], trade['tsl'], trade['direction']
                )
                if status == "exit":
                    open_trades.remove(trade)

        time.sleep(5)

except KeyboardInterrupt:
    print("🛑 Interrupted manually")

finally:
    feed.close_feed()
    print("🏁 Day complete. WebSocket closed.")
