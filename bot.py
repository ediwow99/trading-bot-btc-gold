import os
import pandas as pd
import numpy as np
from binance.client import Client
from dotenv import load_dotenv
import time

# Load API keys
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# Connect to Binance Testnet
client = Client(api_key, api_secret, testnet=True)

symbol = "BTCUSDT"
interval = "1m"  # 1-minute candles
limit = 100      # how many candles to fetch

def get_data():
    """Fetch recent price data (OHLCV) from Binance."""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["timestamp", "close"]]

def compute_signals(df):
    """Compute EMA crossover signals."""
    df["ema_fast"] = df["close"].ewm(span=5, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=20, adjust=False).mean()

    # Generate signals
    df["signal"] = np.where(df["ema_fast"] > df["ema_slow"], "BUY", "SELL")
    return df

def main():
    print("🚀 Starting EMA strategy bot on Binance Testnet...")
    while True:
        df = get_data()
        df = compute_signals(df)
        last = df.iloc[-1]

        print(f"[{last['timestamp']}] Price: {last['close']:.2f} | Fast EMA: {last['ema_fast']:.2f} | Slow EMA: {last['ema_slow']:.2f} | Signal: {last['signal']}")
        time.sleep(10)  # wait 10 seconds before fetching again

if __name__ == "__main__":
    main()
