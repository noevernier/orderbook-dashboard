from orderbook import OrderBook
import asyncio
import websockets
import json
import pandas as pd
from threading import Thread
import time
import requests

class OrderBookAggregator:
    def __init__(self, symbol='BTCUSDT'):
        self.symbol = symbol
        self.ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@depth@100ms"
        self.api_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
        self.order_book = OrderBook()
        self.websocket = None
        self.best_bid = None
        self.best_ask = None

        self.cleaner_thread = Thread(target=self.periodic_clean)
        self.cleaner_thread.start()

    async def connect(self):
        while True:
            try:
                print(f"Connecting to {self.ws_url}")
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as websocket:
                    self.websocket = websocket
                    print("WebSocket connected.")
                    await self.listen()
            except Exception as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(5)

    async def listen(self):
        while True:
            try:
                data = await self.websocket.recv()
                self.process_message(json.loads(data))
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def get_best_bid_ask(self):
        try:
            response = requests.get(self.api_url)
            data = response.json()
            self.best_bid = float(data['bids'][0][0])
            self.best_ask = float(data['asks'][0][0])
        except Exception as e:
            print(f"Error fetching snapshot from API: {e}")
            self.best_bid, self.best_ask = None, None

    def clean_order_book(self):
        if self.best_bid is None or self.best_ask is None:
            return

        for price in list(self.order_book.bid.keys()):
            if price > self.best_bid:
                self.order_book.update('bid', price, 0)

        for price in list(self.order_book.ask.keys()):
            if price < self.best_ask:
                self.order_book.update('ask', price, 0)

    def periodic_clean(self, interval=10):
        while True:
            self.get_best_bid_ask()
            self.clean_order_book()
            time.sleep(interval)

    def process_message(self, message):
        bids = message['b']
        asks = message['a']

        for bid in bids:
            price, amount = float(bid[0]), float(bid[1])
            self.order_book.update('bid', price, amount)

        for ask in asks:
            price, amount = float(ask[0]), float(ask[1])
            self.order_book.update('ask', price, amount)

    def get_last_snapshot(self, current_time, tick_size=10, depth=1000):
        ask_df, bid_df = self.order_book.get_levels(tick_size=tick_size, depth=depth)
        ask_df['side'] = 'ask'
        bid_df['side'] = 'bid'
        snapshot_df = pd.concat([ask_df, bid_df], ignore_index=True)
        snapshot_df['timestamp'] = current_time
        return snapshot_df
    
    def get_spread(self):
        self.get_best_bid_ask()
        return self.best_ask - self.best_bid
    
    def get_volume_ask(self):
        return sum(self.order_book.ask.values())
    
    def get_volume_bid(self):
        return sum(self.order_book.bid.values())
