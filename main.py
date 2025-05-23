import os
import time
import logging
from datetime import datetime
import pandas as pd
from dhan_market_feed import DhanOptionsMarketFeed

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Verify credentials
if not CLIENT_ID or not ACCESS_TOKEN:
    logging.error("Missing DHAN credentials. Please set CLIENT_ID and ACCESS_TOKEN environment variables.")
    exit(1)

print(f"\U0001F194 Client ID: {CLIENT_ID}")
print(f"\U0001F511 Access Token: {ACCESS_TOKEN[:6]}...{ACCESS_TOKEN[-6:]}")

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

SIGNAL_SYMBOL = "1330"  # NIFTY 50 Index
SYMBOL_CE = "12599298"  # Example NIFTY CE
SYMBOL_PE = "12604674"  # Example NIFTY PE

ce_trades = 0
pe_trades = 0
open_trades = []

def initialize_market_feed():
    """Initialize and connect to market feed with retry logic"""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt} to connect to market feed...")
            
            if feed.connect_websocket():
                # Verify connection by checking for initial data
                time.sleep(2)  # Wait for initial data
                
                if feed.connected:
                    # Subscribe to required symbols
                    symbols = [SIGNAL_SYMBOL, SYMBOL_CE, SYMBOL_PE]
                    if feed.subscribe_to_symbols(symbols):
                        logging.info("Market feed initialized successfully")
                        return True
            
            logging.warning(f"Connection attempt {attempt} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            time.sleep(retry_delay)
    
    logging.error(f"Failed to establish market feed connection after {max_retries} attempts")
    return False

# ... [rest of your existing functions remain the same] ...

if __name__ == "__main__":
    if not initialize_market_feed():
        exit(1)

    try:
        # Your main trading loop here
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            logging.info(f"Current time: {current_time}")
            time.sleep(10)  # Example delay
            
    except KeyboardInterrupt:
        logging.info("\n\U0001F6A7 Manual interruption detected")
    finally:
        feed.close_connection()
        logging.info("\U0001F3C1 Trading session ended")
