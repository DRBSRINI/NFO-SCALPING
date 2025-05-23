import os
import time
import logging
from datetime import datetime
from dhan_market_feed import DhanOptionsMarketFeed

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    print("\U0001F680 Bot Started Successfully!")

    # Load credentials
    CLIENT_ID = os.getenv("CLIENT_ID")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

    if not CLIENT_ID or not ACCESS_TOKEN:
        logging.error("Missing DHAN credentials")
        return

    print(f"\U0001F194 Client ID: {CLIENT_ID}")
    print(f"\U0001F511 Access Token: {ACCESS_TOKEN[:6]}...{ACCESS_TOKEN[-6:]}")

    # Initialize market feed
    feed = DhanOptionsMarketFeed(CLIENT_ID, ACCESS_TOKEN)

    # Configuration
    SYMBOLS = ["1330", "12599298", "12604674"]  # NIFTY index and options

    def initialize_feed():
        """Initialize market feed with retry logic"""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logging.info(f"Connection attempt {attempt}/{max_retries}")
            if feed.connect_websocket():
                if feed.subscribe_to_symbols(SYMBOLS):
                    return True
            time.sleep(5)
        return False

    if not initialize_feed():
        logging.error("Failed to initialize market feed")
        return

    try:
        # Main trading loop
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            logging.info(f"Current time: {current_time}")

            # Example: Get latest prices
            for symbol in SYMBOLS:
                data = feed.get_latest_data(symbol)
                if data:
                    logging.info(f"{symbol} LTP: {data.get('ltp')}")

            time.sleep(10)

    except KeyboardInterrupt:
        logging.info("\n\U0001F6A7 Stopping bot...")
    finally:
        feed.close_connection()
        logging.info("\U0001F3C1 Bot stopped")

if __name__ == "__main__":
    main()
