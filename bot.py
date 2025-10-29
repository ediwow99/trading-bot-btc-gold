import time
import requests
from datetime import datetime

# === CONFIG ===
BALANCE = 1000.0       # Starting balance in USDT
TRADE_AMOUNT = 100      # Amount per trade
INTERVAL = 0.5          # seconds, very fast scalping
TAKE_PROFIT = 0.001     # 0.1% profit
STOP_LOSS = 0.001       # 0.1% loss

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
print("🚀 True instant scalping bot for BTC started! Ctrl+C to stop.\n")

try:
    while True:
        price = get_price_from_coingecko("bitcoin")
        if not price:
            time.sleep(INTERVAL)
            continue

        total_value = balance + (holding * price if holding > 0 else 0)
        pnl_percent = ((total_value - BALANCE) / BALANCE) * 100
        pnl_amount = total_value - BALANCE

        # === ENTER POSITION ===
        if holding == 0 and balance >= TRADE_AMOUNT:
            holding = TRADE_AMOUNT / price
            balance -= TRADE_AMOUNT
            entry_price = price
            print(f"[{datetime.now().strftime('%H:%M:%S')}] BUY at {price:.2f} USD | Holding: {holding:.6f} BTC")

        # === EXIT POSITION ===
        elif holding > 0:
            # Exit immediately on small TP or SL
            profit_target = entry_price * (1 + TAKE_PROFIT)
            stop_target = entry_price * (1 - STOP_LOSS)

            if price >= profit_target or price <= stop_target:
                balance += holding * price
                action = "TP" if price >= profit_target else "SL"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SELL ({action}) at {price:.2f} USD | "
                      f"Balance: {balance:.2f} USDT | PnL: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
                holding = 0
                entry_price = None

        # === STATUS ===
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Price: {price:.2f} USD | "
              f"Balance: {balance:.2f} USDT | PnL: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    total_value = balance + (holding * price if holding > 0 else 0)
    pnl_percent = ((total_value - BALANCE) / BALANCE) * 100
    pnl_amount = total_value - BALANCE
    print(f"\n🚪 Bot stopped. Final Balance: {total_value:.2f} USDT | "
          f"Profit/Loss: {pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
