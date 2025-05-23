import websocket
import threading
import time
import json
import logging
from datetime import datetime

class DhanOptionsMarketFeed:
    def __init__(self, client_id, access_token):
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dhan_feed.log'),
                logging.StreamHandler()
            ]
        )
        
        self.client_id = str(client_id)
        self.access_token = str(access_token)
        self.base_url = "https://api.dhan.co"
        self.ws_url = "wss://api.dhan.co/websocket"
        self.headers = {
            'access-token': self.access_token,
            'Content-Type': 'application/json',
            'client-id': self.client_id
        }
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.market_data = {}
        self.keep_running = True

    def connect_websocket(self):
        """Establish WebSocket connection with proper headers"""
        if self.ws is not None:
            self.ws.close()

        # Correct way to pass headers in websocket-client
        header = [
            f"access-token: {self.access_token}",
            f"client-id: {self.client_id}"
        ]

        try:
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
            self.keep_running = True
            self.ws_thread.start()

            # Wait for connection to establish
            timeout = 10  # seconds
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            return self.connected
        except Exception as e:
            logging.error(f"WebSocket initialization failed: {e}")
            return False

    def _run_websocket(self):
        """Run WebSocket with proper error handling"""
        while self.keep_running:
            try:
                self.ws.run_forever(
                    ping_interval=30,
                    ping_timeout=10,
                    sslopt={"cert_reqs": "CERT_NONE"}
                )
            except Exception as e:
                logging.error(f"WebSocket runtime error: {e}")
                time.sleep(5)  # Wait before reconnecting
            finally:
                self.connected = False

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            security_id = str(data.get('security_id'))
            if security_id:
                self.market_data[security_id] = data
                logging.debug(f"Market update: {security_id} - {data.get('ltp')}")
        except Exception as e:
            logging.error(f"Message processing error: {e}")

    def _on_error(self, ws, error):
        if isinstance(error, str):
            logging.error(f"WebSocket error: {error}")
        else:
            logging.error(f"WebSocket error: {str(error)}")
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        logging.info(f"WebSocket connection closed (code: {close_status_code}, message: {close_msg})")
        self.connected = False

    def _on_open(self, ws):
        logging.info("WebSocket connection successfully established")
        self.connected = True
        if self.subscribed_symbols:
            self.subscribe_to_symbols(list(self.subscribed_symbols))

    def subscribe_to_symbols(self, symbols):
        """Subscribe to market data for specific symbols"""
        if not self.connected:
            logging.error("Cannot subscribe - WebSocket not connected")
            return False

        try:
            subscription_msg = {
                "action": "subscribe",
                "symbols": [str(s) for s in symbols]
            }
            self.ws.send(json.dumps(subscription_msg))
            self.subscribed_symbols.update(str(s) for s in symbols)
            logging.info(f"Subscribed to symbols: {symbols}")
            return True
        except Exception as e:
            logging.error(f"Subscription failed: {e}")
            return False

    def get_latest_data(self, security_id):
        """Get the latest market data for a security"""
        return self.market_data.get(str(security_id))

    def close_connection(self):
        """Cleanly close the WebSocket connection"""
        self.keep_running = False
        if self.ws:
            self.ws.close()
        self.connected = False
        logging.info("WebSocket connection terminated")
