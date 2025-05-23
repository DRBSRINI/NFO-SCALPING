import os
import time
import json
import threading
from datetime import datetime
import websocket

print("\U0001F680 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

print("\U0001F194 Client ID:", CLIENT_ID)
print("\U0001F511 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# DhanOptionsMarketFeed WebSocket client class
class DhanOptionsMarketFeed:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.ws = None
        self.thread = None

    def on_message(self, ws, message):
        print("📥 Received Message:", message)

    def on_error(self, ws, error):
        print("❌ WebSocket Error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 WebSocket Closed")

    def on_open(self, ws):
        print("✅ WebSocket Connection Opened")
        # Replace this payload with actual subscription details per Dhan's documentation
        subscribe_payload = {
            "security_id": "12599298",
            "subscription_mode": "FULL"
        }
        ws.send(json.dumps(subscribe_payload))

    def run(self):
        url = "wss://streamapi.dhan.co/market-feed"  # Replace with the actual Dhan WebSocket URL
        headers = [
            f"access-token: {self.access_token}",
            f"client-id: {self.client_id}"
        ]
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=headers
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

# --- MAIN EXECUTION ---
def main():
    print("🚀 Initializing Dhan Options Market Feed...")
    feed = DhanOptionsMarketFeed(CLIENT_ID, ACCESS_TOKEN)
    feed.run()

if __name__ == "__main__":
    main()
