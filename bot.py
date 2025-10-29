import time
import requests
from datetime import datetime

# === CONFIG ===
BALANCE = 1000.0        # Starting balance in USDT
TRADE_AMOUNT = 100       # Amount per trade
INTERVAL = 5             # seconds, updates every 5 seconds
TAKE_PROFIT = 0.002      # 0.2%
STOP_LOSS = 0.001        # 0.1%

# === VARIABLES ===
balance = BALANCE
holding = 0
entry_price = None
last_price = None

# === FUNCTIONS ===
def get_price_from_coingecko(coin_id="bitcoin"):
    global last_price
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        last_price = data[coin_id]["usd"]
        return last_price
    except:
        return last_price

# === MAIN LOOP ===
print("🚀 Instant scalping bot for BTC started! Type Ctrl+C to exit.\n")

try:
    while True:
        price = get_price_from_coingecko("bitcoin")
        if not price:
            print("⚠️ Price unavailable, skipping...")
            time.sleep(INTERVAL)
            continue

        total_value = balance + (holding * price if holding > 0 else 0)
        pnl_percent = ((total_value - BALANCE) / BALANCE) * 100
        pnl_amount = total_value - BALANCE

        # === Enter trade if not holding ===
        if holding == 0 and balance >= TRADE_AMOUNT:
            holding = TRADE_AMOUNT / price
            balance -= TRADE_AMOUNT
            entry_price = price
            print(f"[{datetime.now().strftime('%H:%M:%S')}] BUY at {price:.2f} USD | Holding: {holding:.6f} BTC")

        # === Exit trade on take profit or stop loss ===
        elif holding > 0:
            profit_target = entry_price * (1 + TAKE_PROFIT)
            stop_target = entry_price * (1 - STOP_LOSS)

            if price >= profit_target or price <= stop_target:
                balance += holding * price
                action = "TP" if price >= profit_target else "SL"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SELL ({action}) at {price:.2f} USD | "
                      f"Balance: {balance:.2f} USDT | PnL: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
                holding = 0
                entry_price = None

        # === Display current status ===
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Current Price: {price:.2f} USD | "
              f"Balance: {balance:.2f} USDT | PnL: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    # Exit manually
    total_value = balance + (holding * price if holding > 0 else 0)
    pnl_percent = ((total_value - BALANCE) / BALANCE) * 100
    pnl_amount = total_value - BALANCE
    print(f"\n🚪 Bot stopped by user. Final Balance: {total_value:.2f} USDT | "
          f"Profit/Loss: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
