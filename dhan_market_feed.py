import websocket
import threading
import time
import json
import logging
from datetime import datetime

class DhanOptionsMarketFeed:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = "https://api.dhan.co"
        self.ws_url = "wss://api.dhan.co/websocket"  # Updated WebSocket URL
        self.headers = {
            'access-token': self.access_token,
            'Content-Type': 'application/json'
        }
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.market_data = {}

    def connect_websocket(self):
        """Establish WebSocket connection with proper headers"""
        if self.ws is not None:
            self.ws.close()

        # Add authentication headers to WebSocket
        header = [
            f"access-token: {self.access_token}",
            f"client-id: {self.client_id}"
        ]

        self.ws = websocket.WebSocketApp(
            self.ws_url,
            header=header,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        # Start WebSocket in a separate thread
        self.ws_thread = threading.Thread(target=self._run_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        # Wait for connection to establish
        timeout = 10  # seconds
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        return self.connected

    def _run_websocket(self):
        """Run WebSocket with reconnect logic"""
        while True:
            try:
                self.ws.run_forever(
                    ping_interval=30,
                    ping_timeout=10,
                    sslopt={"cert_reqs": "CERT_NONE"}
                )
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
            
            if not self.connected:
                logging.info("Attempting to reconnect...")
                time.sleep(5)
                continue
            else:
                break

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            security_id = data.get('security_id')
            if security_id:
                self.market_data[security_id] = data
                logging.debug(f"Market update: {data}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse message: {e}")

    def _on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        logging.info("WebSocket connection closed")
        self.connected = False

    def _on_open(self, ws):
        logging.info("WebSocket connection established")
        self.connected = True
        if self.subscribed_symbols:
            self.subscribe_to_symbols(list(self.subscribed_symbols))

    # ... (rest of your existing methods)
