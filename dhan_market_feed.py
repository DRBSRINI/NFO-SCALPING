# dhan_market_feed.py

import websocket
import json
import threading
import time
import os

class DhanOptionsMarketFeed:
    def __init__(self, instruments):
        self.instruments = instruments
        self.token = os.getenv("ACCESS_TOKEN") or "your_access_token"
        self.client_id = os.getenv("CLIENT_ID") or "your_client_id"

    def on_message(self, ws, message):
        print("📩", message)

    def on_error(self, ws, error):
        print("❌ WebSocket error:", error)

    def on_close(self, ws, *args):
        print("🔌 Connection closed", args)

    def on_open(self, ws):
        payload = {
            "msg_type": "subscribe",
            "instrument_type": "security",
            "params": {
                "mode": "FULL",
                "instruments": self.instruments
            }
        }
        ws.send(json.dumps(payload))
        print("📡 Subscribed:", self.instruments)

    def run(self):
        ws = websocket.WebSocketApp(
            "wss://api.dhan.co/market/feed",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            header=[
                f"access-token: {self.token}",
                f"client-id: {self.client_id}"
            ]
        )
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
        while True:
            time.sleep(1)
