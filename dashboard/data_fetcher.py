import requests
import pandas as pd
import csv
from datetime import datetime
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()
SERVER_IP = os.getenv("SERVER_IP")

class DataFetcher:
    def __init__(self, url, file_name, interval=60):
        self.url = url
        self.file_name = file_name
        self.interval = interval
        self.columns = ["timestamp", "price", "amount", "side"]
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        try:
            with open(self.file_name, 'x', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
        except FileExistsError:
            pass 

    def fetch_data(self):
        data = requests.get(self.url).json()
        df = pd.DataFrame(data, columns=self.columns)
        df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M')  
        return df

    def append_to_csv(self, df):
        with open(self.file_name, 'a', newline='') as f:
            df.to_csv(f, header=False, index=False)

    def start(self):
        while True:
            df = self.fetch_data()
            self.append_to_csv(df)
            time.sleep(self.interval)

url = f"http://{SERVER_IP}:5000/snapshot/20/500"
file_name = "data_snapshot.csv"

fetcher = DataFetcher(url, file_name)
fetcher.start()