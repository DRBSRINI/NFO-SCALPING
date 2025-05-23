import requests
import json
import time
from datetime import datetime
import pandas as pd
import websocket
import threading
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dhan_market_feed.log'),
        logging.StreamHandler()
    ]
)

class DhanOptionsMarketFeed:
    """
    A class to handle Nifty options market data from DHAN API
    """
    
    def __init__(self, client_id, access_token):
        """
        Initialize the DHAN market feed with client credentials
        
        Args:
            client_id (str): DHAN client ID
            access_token (str): DHAN access token
        """
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = "https://api.dhan.co"
        self.ws_url = "wss://api.dhan.co/ws"
        self.headers = {
            'access-token': self.access_token,
            'Content-Type': 'application/json'
        }
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.market_data = {}
        self.option_chain = {}
        
    def _make_request(self, endpoint, method='GET', params=None, data=None):
        """
        Make HTTP requests to DHAN API
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method
            params (dict): Query parameters
            data (dict): Request body
            
        Returns:
            dict: Response data
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None
    
    def get_nifty_option_chain(self, expiry_date=None):
        """
        Fetch Nifty option chain
        
        Args:
            expiry_date (str): Expiry date in 'YYYY-MM-DD' format
            
        Returns:
            dict: Option chain data
        """
        endpoint = "/options"
        params = {'symbol': 'NIFTY'}
        
        if expiry_date:
            params['expiryDate'] = expiry_date
            
        data = self._make_request(endpoint, params=params)
        if data:
            self.option_chain = data
            logging.info(f"Successfully fetched NIFTY option chain for expiry: {expiry_date}")
        return data
    
    def get_historical_data(self, symbol, exchange='NFO', instrument='OPTIDX', 
                           from_date=None, to_date=None, expiry_date=None):
        """
        Fetch historical data for an option
        
        Args:
            symbol (str): Symbol name (e.g., 'NIFTY')
            exchange (str): Exchange (default: 'NFO')
            instrument (str): Instrument type (default: 'OPTIDX')
            from_date (str): Start date in 'YYYY-MM-DD' format
            to_date (str): End date in 'YYYY-MM-DD' format
            expiry_date (str): Expiry date in 'YYYY-MM-DD' format
            
        Returns:
            dict: Historical data
        """
        endpoint = "/historical"
        params = {
            'symbol': symbol,
            'exchange': exchange,
            'instrument': instrument
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        if expiry_date:
            params['expiryDate'] = expiry_date
            
        return self._make_request(endpoint, params=params)
    
    def on_ws_message(self, ws, message):
        """
        Handle incoming WebSocket messages
        """
        try:
            data = json.loads(message)
            security_id = data.get('security_id')
            
            if security_id:
                # Store the latest market data
                self.market_data[security_id] = data
                
                # Log the update
                logging.debug(f"Market data update: {data}")
                
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse WebSocket message: {e}")
    
    def on_ws_error(self, ws, error):
        """
        Handle WebSocket errors
        """
        logging.error(f"WebSocket error: {error}")
        self.connected = False
    
    def on_ws_close(self, ws, close_status_code, close_msg):
        """
        Handle WebSocket close events
        """
        logging.info("WebSocket connection closed")
        self.connected = False
        self.ws = None
        
        # Attempt to reconnect
        self.connect_websocket()
    
    def on_ws_open(self, ws):
        """
        Handle WebSocket open events
        """
        logging.info("WebSocket connection established")
        self.connected = True
        
        # Resubscribe to previously subscribed symbols
        if self.subscribed_symbols:
            self.subscribe_to_symbols(list(self.subscribed_symbols))
    
    def connect_websocket(self):
        """
        Establish WebSocket connection for live market data
        """
        if self.ws is not None:
            self.ws.close()
            
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open,
            header=[f'access-token: {self.access_token}']
        )
        
        # Start WebSocket in a separate thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection to establish
        retries = 0
        max_retries = 5
        while not self.connected and retries < max_retries:
            time.sleep(1)
            retries += 1
            
        return self.connected
    
    def subscribe_to_symbols(self, symbols):
        """
        Subscribe to market data for specific symbols
        
        Args:
            symbols (list): List of symbols to subscribe to
        """
        if not self.connected:
            logging.error("WebSocket not connected. Cannot subscribe.")
            return False
            
        subscription_msg = {
            "action": "subscribe",
            "symbols": symbols
        }
        
        try:
            self.ws.send(json.dumps(subscription_msg))
            self.subscribed_symbols.update(symbols)
            logging.info(f"Subscribed to symbols: {symbols}")
            return True
        except Exception as e:
            logging.error(f"Failed to subscribe: {e}")
            return False
    
    def unsubscribe_from_symbols(self, symbols):
        """
        Unsubscribe from market data for specific symbols
        
        Args:
            symbols (list): List of symbols to unsubscribe from
        """
        if not self.connected:
            logging.error("WebSocket not connected. Cannot unsubscribe.")
            return False
            
        unsubscribe_msg = {
            "action": "unsubscribe",
            "symbols": symbols
        }
        
        try:
            self.ws.send(json.dumps(unsubscribe_msg))
            self.subscribed_symbols.difference_update(symbols)
            logging.info(f"Unsubscribed from symbols: {symbols}")
            return True
        except Exception as e:
            logging.error(f"Failed to unsubscribe: {e}")
            return False
    
    def get_latest_data(self, security_id):
        """
        Get the latest market data for a specific security
        
        Args:
            security_id (str): Security ID to fetch data for
            
        Returns:
            dict: Latest market data or None if not available
        """
        return self.market_data.get(security_id)
    
    def get_option_greeks(self, security_id):
        """
        Extract option Greeks from market data
        
        Args:
            security_id (str): Security ID to fetch Greeks for
            
        Returns:
            dict: Greeks data or None if not available
        """
        data = self.get_latest_data(security_id)
        if data:
            return {
                'delta': data.get('delta'),
                'gamma': data.get('gamma'),
                'theta': data.get('theta'),
                'vega': data.get('vega'),
                'iv': data.get('iv')
            }
        return None
    
    def get_ltp(self, security_id):
        """
        Get last traded price for a security
        
        Args:
            security_id (str): Security ID
            
        Returns:
            float: Last traded price or None if not available
        """
        data = self.get_latest_data(security_id)
        return data.get('ltp') if data else None
    
    def close_connection(self):
        """
        Cleanly close the WebSocket connection
        """
        if self.ws:
            self.ws.close()
            self.ws = None
        self.connected = False
        logging.info("Connection closed")


# Example usage
if __name__ == "__main__":
    # Initialize with your DHAN credentials
    client_id = "YOUR_CLIENT_ID"
    access_token = "YOUR_ACCESS_TOKEN"
    
    feed = DhanOptionsMarketFeed(client_id, access_token)
    
    # Fetch NIFTY option chain for nearest expiry
    option_chain = feed.get_nifty_option_chain()
    print("Option Chain:", json.dumps(option_chain, indent=2))
    
    # Connect to WebSocket for live data
    if feed.connect_websocket():
        # Subscribe to some NIFTY options
        nifty_ce = "NIFTY23DEC22400CE"  # Example call option
        nifty_pe = "NIFTY23DEC22400PE"  # Example put option
        
        feed.subscribe_to_symbols([nifty_ce, nifty_pe])
        
        # Keep running for some time to receive updates
        try:
            for _ in range(10):
                time.sleep(1)
                print(f"LTP for {nifty_ce}: {feed.get_ltp(nifty_ce)}")
                print(f"LTP for {nifty_pe}: {feed.get_ltp(nifty_pe)}")
                print(f"Greeks for {nifty_ce}: {feed.get_option_greeks(nifty_ce)}")
        except KeyboardInterrupt:
            pass
        finally:
            feed.close_connection()
