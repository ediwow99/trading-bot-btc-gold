import os
import pandas as pd
import numpy as np
import time
from binance.client import Client
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# Connect to Binance Testnet
client = Client(api_key, api_secret, testnet=True)

# --- Config ---
symbol = "BTCUSDT"
interval = "1m"
limit = 100

# --- Simulated wallet ---
starting_balance = 1000.0
balance_usdt = starting_balance
balance_btc = 0.0
last_signal = None
last_ema_fast = None
last_ema_slow = None

def get_data():
    """Fetch BTC data (OHLCV)."""
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
    df["signal"] = np.where(df["ema_fast"] > df["ema_slow"], "BUY", "SELL")
    return df

def simulate_trade(price, signal):
    """Simulate buy/sell trades."""
    global balance_usdt, balance_btc, last_signal

    if signal == "BUY" and last_signal != "BUY":
        if balance_usdt > 0:
            balance_btc = balance_usdt / price
            balance_usdt = 0
            last_signal = "BUY"
            print(f"🟢 Bought BTC at {price:.2f}")

    elif signal == "SELL" and last_signal != "SELL":
        if balance_btc > 0:
            balance_usdt = balance_btc * price
            balance_btc = 0
            last_signal = "SELL"
            print(f"🔴 Sold BTC at {price:.2f}")

def main():
    global balance_usdt, balance_btc, last_ema_fast, last_ema_slow

    print("🚀 Starting EMA trading bot (simulation mode)...\n")
    while True:
        df = get_data()
        df = compute_signals(df)
        last = df.iloc[-1]
        price = last["close"]
        signal = last["signal"]
        ema_fast = last["ema_fast"]
        ema_slow = last["ema_slow"]

        # Detect crossover manually
        if last_ema_fast and last_ema_slow:
            if last_ema_fast <= last_ema_slow and ema_fast > ema_slow:
                print("📈 Crossover detected → Potential BUY zone")
            elif last_ema_fast >= last_ema_slow and ema_fast < ema_slow:
                print("📉 Crossunder detected → Potential SELL zone")

        # Try trade
        simulate_trade(price, signal)

        # Compute wallet value
        total_value = balance_usdt + balance_btc * price
        profit = total_value - starting_balance
        profit_percent = (profit / starting_balance) * 100

        # Display details
        print(
            f"[{last['timestamp']}] Price: {price:.2f} | Signal: {signal} | "
            f"EMA5: {ema_fast:.2f} | EMA20: {ema_slow:.2f} | "
            f"💰 USDT: {balance_usdt:.2f} | ₿ BTC: {balance_btc:.6f} | "
            f"Total: {total_value:.2f} USDT | 📈 PnL: {profit:+.2f} USDT ({profit_percent:+.2f}%)"
        )

        # Save last EMAs for crossover check
        last_ema_fast, last_ema_slow = ema_fast, ema_slow

        time.sleep(5)

if __name__ == "__main__":
    main()
