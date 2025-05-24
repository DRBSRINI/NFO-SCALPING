import websocket
import threading
import json

class DhanOptionsMarketFeed:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.instruments = []
        self.ws = None
        self.on_tick = None

    def subscribe(self, instruments):
        self.instruments = instruments

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if self.on_tick:
                self.on_tick(data)
        except Exception as e:
            print("⚠️ WebSocket message error:", e)

    def on_open(self, ws):
        print("🟢 WebSocket connected.")
        for inst in self.instruments:
            ws.send(json.dumps({
                "action": "subscribe",
                "params": {
                    "exchange": inst["exchange"],
                    "segment": inst["segment"],
                    "instrument_token": inst["instrument_token"]
                }
            }))

    def on_error(self, ws, error):
        print("❌ WebSocket error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔴 WebSocket closed: {close_status_code} - {close_msg}")

    def start_websocket(self):
        url = "wss://marketfeed.dhan.co"  # Replace with the correct URL if needed

        headers = {
            "access-token": self.access_token,
            "client-id": self.client_id
        }

        self.ws = websocket.WebSocketApp(
            url,
            header=[f"{k}: {v}" for k, v in headers.items()],
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error
        )

        # Run WebSocket in background thread
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def stop(self):
        if self.ws:
            self.ws.close()
