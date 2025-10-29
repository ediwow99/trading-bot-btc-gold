import ssl, certifi, os, requests

# Force Python to use certifi's trusted certificate bundle
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

# Optional: tell requests to always use certifi CA
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

import time
import datetime
import requests
import pandas as pd

# --- SETTINGS ---
API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
INITIAL_BALANCE = 1000.0
TRADE_SIZE = 0.1  # fraction of balance to trade each time

# --- FUNCTIONS ---

def get_price_data():
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": 100}
    response = requests.get(API_URL, params=params)
    data = response.json()

    frame = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close',
        'volume', 'close_time', 'quote_asset_volume',
        'trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
    ])
    frame['time'] = pd.to_datetime(frame['time'], unit='ms')
    frame['close'] = frame['close'].astype(float)
    return frame


def get_signal(df):
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()

    if df['EMA12'].iloc[-1] > df['EMA26'].iloc[-1]:
        return "BUY"
    elif df['EMA12'].iloc[-1] < df['EMA26'].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"


def simulate_trade(signal, balance, position, last_price):
    """ Simulate buying/selling with current balance """
    if signal == "BUY" and position == 0:
        position = balance / last_price
        balance = 0
        action = "🟢 BOUGHT"
    elif signal == "SELL" and position > 0:
        balance = position * last_price
        position = 0
        action = "🔴 SOLD"
    else:
        action = "⚪ HOLD"
    return balance, position, action


# --- MAIN LOOP ---
print("🚀 Starting EMA trading bot (simulation mode)...")
balance = INITIAL_BALANCE
position = 0
last_signal = None

while True:
    try:
        df = get_price_data()
        signal = get_signal(df)
        price = df['close'].iloc[-1]

        # trade only when new signal appears
        if signal != last_signal and signal != "HOLD":
            balance, position, action = simulate_trade(signal, balance, position, price)
            last_signal = signal
        else:
            action = "⚪ HOLD"

        total_value = balance + (position * price)

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"Price: {price:,.2f} | Signal: {signal:<4} | {action} | "
              f"💰 Total: {total_value:,.2f} USDT")

        # wait for next candle
        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
