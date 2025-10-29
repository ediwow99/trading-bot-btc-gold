import time
import requests
import pandas as pd
from datetime import datetime

# === CONFIG ===
BALANCE = 1000.0      # Starting balance in USDT
TRADE_AMOUNT = 100     # Amount per simulated trade
INTERVAL = 3           # seconds, fast for scalping
EMA_SHORT = 3
EMA_LONG = 8
SCALP_THRESHOLD = 0.05  # % difference between EMAs to trigger trade

# === FUNCTIONS ===
last_price = None  # cache last known price

def get_price_from_coingecko(coin_id="bitcoin"):
    """Fetch latest price from CoinGecko with caching and rate-limit handling"""
    global last_price
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    backoff = 1  # start with 1 second backoff

    while True:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            price = data[coin_id]["usd"]
            last_price = price  # update cache
            return price

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                print(f"⚠️ Rate limit hit. Waiting {backoff}s before retry...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)  # exponential backoff max 60s
            else:
                print(f"❌ HTTP error fetching {coin_id}: {e}. Using last cached price.")
                return last_price

        except requests.exceptions.RequestException as e:
            print(f"❌ Request error fetching {coin_id}: {e}. Using last cached price.")
            return last_price

def calculate_ema(prices, span):
    """Calculate EMA"""
    return pd.Series(prices).ewm(span=span, adjust=False).mean().iloc[-1]

def get_signal(prices):
    """Scalping signal based on short EMA crossover and small price moves"""
    if len(prices) < EMA_LONG:
        return "WAIT"
    
    short_ema = calculate_ema(prices[-EMA_SHORT:], EMA_SHORT)
    long_ema = calculate_ema(prices[-EMA_LONG:], EMA_LONG)
    
    diff_percent = ((short_ema - long_ema) / long_ema) * 100
    
    if diff_percent > SCALP_THRESHOLD:
        return "BUY"
    elif diff_percent < -SCALP_THRESHOLD:
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

print(f"\n🚀 Starting scalping EMA bot for {symbol}...\n")

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
