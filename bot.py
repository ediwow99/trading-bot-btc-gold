import os
import pandas as pd
import numpy as np
import time
from binance.client import Client
from dotenv import load_dotenv

# Load API keys
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# Connect to Binance Testnet
client = Client(api_key, api_secret, testnet=True)

symbol = "BTCUSDT"
interval = "1m"
limit = 100

# Simulated wallet
balance_usdt = 1000.0  # starting money
balance_btc = 0.0
last_signal = None

def get_data():
    """Fetch recent BTC data (OHLCV)."""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["timestamp", "close"]]

def compute_signals(df):
    """EMA crossover strategy."""
    df["ema_fast"] = df["close"].ewm(span=5, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=20, adjust=False).mean()
    df["signal"] = np.where(df["ema_fast"] > df["ema_slow"], "BUY", "SELL")
    return df

def simulate_trade(price, signal):
    """Simulate buy/sell and update balances."""
    global balance_usdt, balance_btc, last_signal

    if signal == "BUY" and last_signal != "BUY":
        if balance_usdt > 0:
            balance_btc = balance_usdt / price
            balance_usdt = 0
            last_signal = "BUY"
            print(f"\n🟢 Bought BTC at {price:.2f}")
            show_balances(price)

    elif signal == "SELL" and last_signal != "SELL":
        if balance_btc > 0:
            balance_usdt = balance_btc * price
            balance_btc = 0
            last_signal = "SELL"
            print(f"\n🔴 Sold BTC at {price:.2f}")
            show_balances(price)

def show_balances(price):
    """Print current balance and total value."""
    total_value = balance_usdt + balance_btc * price
    print(f"💰 USDT: {balance_usdt:.2f} | ₿ BTC: {balance_btc:.6f} | Total Value: {total_value:.2f} USDT")

def main():
    print("🚀 Starting EMA trading bot (simulation mode)...")
    while True:
        df = get_data()
        df = compute_signals(df)
        last = df.iloc[-1]
        price = last["close"]
        signal = last["signal"]

        simulate_trade(price, signal)

        total_value = balance_usdt + balance_btc * price
        print(f"[{last['timestamp']}] Price: {price:.2f} | Signal: {signal} | 💰 Total: {total_value:.2f} USDT")

        time.sleep(5)  # update every 5 seconds

if __name__ == "__main__":
    main()
