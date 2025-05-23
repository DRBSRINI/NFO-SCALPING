import websocket
import json
import threading
import time
import os

# Load your credentials from environment or hardcoded for testing
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN") or "your_access_token_here"
CLIENT_ID = os.getenv("CLIENT_ID") or "your_client_id_here"

# ✅ List of instruments to subscribe — in correct Dhan format
INSTRUMENTS = ["NSE|12599298", "NSE|12604674"]  # CE and PE example

def on_message(ws, message):
    print("📩 Message received:", message)

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 WebSocket closed:", close_status_code, close_msg)

def on_open(ws):
    print("✅ WebSocket connection established!")

    # ✅ Properly formatted subscription payload
    subscribe_payload = {
        "msg_type": "subscribe",
        "instrument_type": "security",
        "params": {
            "mode": "FULL",
            "instruments": INSTRUMENTS
        }
    }

    ws.send(json.dumps(subscribe_payload))
    print("📡 Subscription sent:", subscribe_payload)

def start_websocket():
    ws_url = "wss://api.dhan.co/market/feed"  # Dhan's market feed endpoint

    headers = {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID
    }

    # Setup WebSocket
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        header=[f"{k}: {v}" for k, v in headers.items()]
    )

    # Run in a thread so it doesn't block
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    # Keep alive manually or via async loop
    while True:
        time.sleep(1)

# Entry
if __name__ == "__main__":
    print("🚀 Starting Dhan WebSocket...")
    start_websocket()
