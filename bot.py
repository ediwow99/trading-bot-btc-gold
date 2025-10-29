import time
import requests
from datetime import datetime

# === CONFIG ===
BALANCE = 1000.0        # Starting balance in USDT
TRADE_AMOUNT = 100       # Amount per trade
INTERVAL = 1             # seconds, fast polling
TAKE_PROFIT = 0.002      # 0.2% profit
STOP_LOSS = 0.001        # 0.1% loss

# === FUNCTIONS ===
last_price = None

def get_price_from_coingecko(coin_id="bitcoin"):
    """Fetch latest price from CoinGecko with caching"""
    global last_price
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = data[coin_id]["usd"]
        last_price = price
        return price
    except:
        return last_price

# === MAIN ===
print("Starting instant scalping bot for BTC...")

balance = BALANCE
holding = 0
entry_price = None

while True:
    price = get_price_from_coingecko("bitcoin")
    if not price:
        print("⚠️ Price unavailable, skipping...")
        time.sleep(INTERVAL)
        continue

    # === Enter position if not holding ===
    if holding == 0 and balance >= TRADE_AMOUNT:
        holding = TRADE_AMOUNT / price
        balance -= TRADE_AMOUNT
        entry_price = price
        print(f"[{datetime.now().strftime('%H:%M:%S')}] BUY at {price:.2f} USD | Holding: {holding:.6f} BTC")

    # === Check take profit / stop loss ===
    elif holding > 0:
        profit_target = entry_price * (1 + TAKE_PROFIT)
        stop_target = entry_price * (1 - STOP_LOSS)

        if price >= profit_target:
            balance += holding * price
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SELL (TP) at {price:.2f} USD | Balance: {balance:.2f} USDT")
            holding = 0
            entry_price = None
        elif price <= stop_target:
            balance += holding * price
            print(f"[{datetime.now().strftime('%H:%M:%S')}] SELL (SL) at {price:.2f} USD | Balance: {balance:.2f} USDT")
            holding = 0
            entry_price = None

    time.sleep(INTERVAL)
