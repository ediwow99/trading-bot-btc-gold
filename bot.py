import time
import requests
import pandas as pd
from datetime import datetime

# === CONFIG ===
BALANCE = 1000.0      # Starting balance in USDT
TRADE_AMOUNT = 100     # Amount per simulated trade
INTERVAL = 5           # seconds
EMA_SHORT = 5
EMA_LONG = 20

# === FUNCTIONS ===

def get_price_from_coingecko(coin_id="bitcoin"):
    """Fetch the latest price from CoinGecko"""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data[coin_id]["usd"]
    except Exception as e:
        print(f"⚠️ Error fetching {coin_id} price: {e}")
        return None

def calculate_ema(prices, span):
    """Calculate EMA"""
    return pd.Series(prices).ewm(span=span, adjust=False).mean().iloc[-1]

def get_signal(prices):
    """Generate trading signal based on EMA crossover"""
    if len(prices) < EMA_LONG:
        return "WAIT"
    short_ema = calculate_ema(prices[-EMA_SHORT:], EMA_SHORT)
    long_ema = calculate_ema(prices[-EMA_LONG:], EMA_LONG)
    if short_ema > long_ema:
        return "BUY"
    elif short_ema < long_ema:
        return "SELL"
    else:
        return "HOLD"

# === MAIN ===
print("Choose your trading asset:")
print("1️⃣  Bitcoin (BTC)")
print("2️⃣  Gold (XAU/USD)")

choice = input("Enter your choice (1 or 2): ").strip()

if choice == "1":
    coin_id = "bitcoin"
    symbol = "BTC"
elif choice == "2":
    coin_id = "gold"
    symbol = "GOLD"
else:
    print("❌ Invalid choice. Exiting.")
    exit()

prices = []
balance = BALANCE
holding = 0
initial_balance = BALANCE

print(f"\n🚀 Starting EMA trading bot for {symbol} (CoinGecko simulation)...\n")

while True:
    price = get_price_from_coingecko(coin_id)

    if price:
        prices.append(price)
        signal = get_signal(prices)

        # === Simulate trades ===
        if signal == "BUY" and balance >= TRADE_AMOUNT:
            holding += TRADE_AMOUNT / price
            balance -= TRADE_AMOUNT
        elif signal == "SELL" and holding > 0:
            balance += holding * price
            holding = 0

        total_value = balance + (holding * price)
        profit_percent = ((total_value - initial_balance) / initial_balance) * 100

        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{symbol}: {price:,.2f} USD | Signal: {signal:<4} | "
            f"💰 Total: {total_value:,.2f} USDT | 📈 P/L: {profit_percent:+.2f}%"
        )
    else:
        print("❌ Skipping update due to fetch error")

    time.sleep(INTERVAL)
