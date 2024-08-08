from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread
import asyncio
from orderbook_aggregator import OrderBookAggregator
import datetime

app = Flask(__name__)
CORS(app)

order_book_aggregator = OrderBookAggregator()

@app.route('/snapshot/<int:tick_size>/<int:depth>', methods=['GET'])
def snapshot(tick_size, depth):
    current_time = datetime.datetime.now()
    current_time = int(current_time.timestamp() * 1e6)
    df = order_book_aggregator.get_last_snapshot(current_time, tick_size, depth)
    return jsonify(df.to_dict(orient='records'))

@app.route('/volume_ask', methods=['GET'])
def volume_ask():
    return jsonify(order_book_aggregator.get_volume_ask())

@app.route('/volume_bid', methods=['GET'])
def volume_bid():
    return jsonify(order_book_aggregator.get_volume_bid())

@app.route('/spread', methods=['GET'])
def spread():
    return jsonify(order_book_aggregator.get_spread())

async def main():
    websocket_task = asyncio.create_task(order_book_aggregator.connect())
    flask_thread = Thread(target=lambda: app.run(port=5000, debug=True, use_reloader=False))
    flask_thread.start()
    await websocket_task

if __name__ == '__main__':
    asyncio.run(main())
