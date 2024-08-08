import pandas as pd
from BTrees.OOBTree import OOBTree # type: ignore

class OrderBook:
    def __init__(self):
        self.bid = OOBTree()
        self.ask = OOBTree()

    def clear(self):
        self.bid.clear()
        self.ask.clear()

    def update(self, side, price, amount):
        if amount != 0:
            if side == 'bid':
                self.bid[price] = amount
            else:
                self.ask[price] = amount
        else:
            if side == 'bid':
                if price in self.bid:
                    del self.bid[price]
            else:
                if price in self.ask:
                    del self.ask[price]

    def get_levels(self, tick_size=10, depth=1000):
        ask_df = pd.DataFrame.from_dict(self.ask, orient='index', columns=['amount']).reset_index().rename(columns={'index': 'price'})
        bid_df = pd.DataFrame.from_dict(self.bid, orient='index', columns=['amount']).reset_index().rename(columns={'index': 'price'})

        ask_df['price'] = ask_df['price'].apply(lambda x: round(x / tick_size) * tick_size)
        bid_df['price'] = bid_df['price'].apply(lambda x: round(x / tick_size) * tick_size)

        ask_df = ask_df.groupby('price').agg({'amount': 'sum'}).reset_index()
        bid_df = bid_df.groupby('price').agg({'amount': 'sum'}).reset_index()

        mid_price = (ask_df['price'].min() + bid_df['price'].max()) / 2
        ask_df = ask_df[ask_df['price'] <= mid_price * (1 + depth / 10000)]
        bid_df = bid_df[bid_df['price'] >= mid_price * (1 - depth / 10000)]

        return ask_df, bid_df