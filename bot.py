import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# === CONFIG ===
BALANCE = 1000.0        # Starting balance in USDT
TRADE_AMOUNT = 100      # Amount per trade
TAKE_PROFIT = 0.002     # 0.2% profit (reasonable for high-speed)
STOP_LOSS = 0.002       # 0.2% loss
SYMBOL = "BTC/USDT"     # Trading pair
CHECK_INTERVAL = 0.1    # Check price every 0.1 seconds (10 times per second)

# === EXCHANGE API ===
# Using multiple exchanges for fastest response
EXCHANGES = {
    "gate": "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT",
    "htx": "https://api.huobi.pro/market/detail/merged?symbol=btcusdt",
    "mexc": "https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT"
}

# === VARIABLES ===
balance = BALANCE
holding = 0
entry_price = None
trade_count = 0
last_price = None
last_status_time = time.time()
price_checks = 0

# === FUNCTIONS ===
def get_price_multi_exchange():
    """Get price from multiple exchanges simultaneously - returns fastest response"""
    global last_price, price_checks
    
    def fetch_gate():
        try:
            r = requests.get(EXCHANGES["gate"], timeout=0.5)
            data = r.json()
            return float(data[0]['last'])
        except:
            return None
    
    def fetch_htx():
        try:
            r = requests.get(EXCHANGES["htx"], timeout=0.5)
            data = r.json()
            return float(data['tick']['close'])
        except:
            return None
    
    def fetch_mexc():
        try:
            r = requests.get(EXCHANGES["mexc"], timeout=0.5)
            data = r.json()
            return float(data['price'])
        except:
            return None
    
    # Use ThreadPoolExecutor to fetch from all exchanges simultaneously
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(fetch_gate),
            executor.submit(fetch_htx),
            executor.submit(fetch_mexc)
        ]
        
        # Return first successful response
        for future in futures:
            try:
                price = future.result(timeout=0.3)
                if price:
                    last_price = price
                    price_checks += 1
                    return price
            except:
                continue
    
    return last_price  # Return last known price if all fail

def format_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]

# === MAIN LOOP ===
print(f"🚀 Ultra-Fast Scalping Bot Started!")
print(f"   Symbol: {SYMBOL}")
print(f"   Starting Balance: {BALANCE:.2f} USDT")
print(f"   Take Profit: {TAKE_PROFIT*100}% | Stop Loss: {STOP_LOSS*100}%")
print(f"   Speed: Checking price every {CHECK_INTERVAL}s")
print(f"   Press Ctrl+C to stop\n")

try:
    print("⚡ Fetching initial price...\n")
    
    while True:
        loop_start = time.time()
        
        # Get real-time price from fastest exchange
        price = get_price_multi_exchange()
        
        if not price:
            time.sleep(CHECK_INTERVAL)
            continue
        
        # Calculate current portfolio value
        total_value = balance + (holding * price if holding > 0 else 0)
        pnl_amount = total_value - BALANCE
        pnl_percent = (pnl_amount / BALANCE) * 100
        
        # === SHOW STATUS EVERY 5 SECONDS ===
        current_time = time.time()
        if current_time - last_status_time >= 5:
            status = "IN POSITION 📈" if holding > 0 else "WAITING 💤"
            checks_per_sec = price_checks / 5
            print(f"📊 [{format_time()}] {status}")
            print(f"   Price: ${price:,.2f} | Speed: {checks_per_sec:.1f} checks/sec")
            print(f"   Balance: ${balance:.2f} USDT | Portfolio: ${total_value:.2f} USDT")
            print(f"   Total PnL: ${pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
            if holding > 0:
                unrealized_pnl = (price - entry_price) * holding
                unrealized_pct = ((price - entry_price) / entry_price) * 100
                profit_target = entry_price * (1 + TAKE_PROFIT)
                stop_target = entry_price * (1 - STOP_LOSS)
                print(f"   Entry: ${entry_price:,.2f} | Unrealized: ${unrealized_pnl:+.2f} ({unrealized_pct:+.3f}%)")
                print(f"   Need: ${profit_target - price:+.2f} to TP | ${price - stop_target:+.2f} from SL")
            print()
            last_status_time = current_time
            price_checks = 0
        
        # === ENTER POSITION ===
        if holding == 0 and balance >= TRADE_AMOUNT:
            holding = TRADE_AMOUNT / price
            balance -= TRADE_AMOUNT
            entry_price = price
            trade_count += 1
            
            print(f"🟢 [{format_time()}] 📈 BUY (LONG) #{trade_count}")
            print(f"   Price: ${price:,.2f}")
            print(f"   Amount: {holding:.6f} BTC (${TRADE_AMOUNT:.2f})")
            print(f"   Entry: ${entry_price:,.2f}")
            print(f"   Target TP: ${entry_price * (1 + TAKE_PROFIT):,.2f} (+{TAKE_PROFIT*100}%)")
            print(f"   Target SL: ${entry_price * (1 - STOP_LOSS):,.2f} (-{STOP_LOSS*100}%)")
            print(f"   Balance After: ${balance:.2f} USDT")
            print(f"   Portfolio Value: ${balance + (holding * price):.2f} USDT\n")
        
        # === EXIT POSITION ===
        elif holding > 0 and entry_price:
            profit_target = entry_price * (1 + TAKE_PROFIT)
            stop_target = entry_price * (1 - STOP_LOSS)
            
            # Check if TP or SL is hit
            if price >= profit_target:
                # TAKE PROFIT
                sell_value = holding * price
                balance += sell_value
                profit = (price - entry_price) * holding
                profit_pct = ((price - entry_price) / entry_price) * 100
                
                print(f"🟢 [{format_time()}] 📉 SELL (TAKE PROFIT) #{trade_count}")
                print(f"   Entry: ${entry_price:,.2f} → Exit: ${price:,.2f}")
                print(f"   Sold: {holding:.6f} BTC for ${sell_value:.2f}")
                print(f"   Trade Profit: ${profit:,.2f} (+{profit_pct:.3f}%)")
                print(f"   Balance After: ${balance:.2f} USDT")
                print(f"   Total PnL: ${pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)\n")
                
                holding = 0
                entry_price = None
                
            elif price <= stop_target:
                # STOP LOSS
                sell_value = holding * price
                balance += sell_value
                loss = (price - entry_price) * holding
                loss_pct = ((price - entry_price) / entry_price) * 100
                
                print(f"🔴 [{format_time()}] 📉 SELL (STOP LOSS) #{trade_count}")
                print(f"   Entry: ${entry_price:,.2f} → Exit: ${price:,.2f}")
                print(f"   Sold: {holding:.6f} BTC for ${sell_value:.2f}")
                print(f"   Trade Loss: ${loss:,.2f} ({loss_pct:.3f}%)")
                print(f"   Balance After: ${balance:.2f} USDT")
                print(f"   Total PnL: ${pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)\n")
                
                holding = 0
                entry_price = None
        
        # Sleep for remaining time to maintain CHECK_INTERVAL
        elapsed = time.time() - loop_start
        sleep_time = max(0, CHECK_INTERVAL - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\n🛑 Shutting down bot...")
    
    if holding > 0 and last_price:
        print(f"⚠️  Still holding {holding:.6f} BTC @ ${last_price:,.2f}")
        total_value = balance + (holding * last_price)
    else:
        total_value = balance
    
    pnl_amount = total_value - BALANCE
    pnl_percent = (pnl_amount / BALANCE) * 100
    
    print(f"\n📈 FINAL RESULTS")
    print(f"   Starting: ${BALANCE:.2f} USDT")
    print(f"   Final: ${total_value:.2f} USDT")
    print(f"   Trades: {trade_count}")
    print(f"   P/L: ${pnl_amount:+.2f} ({pnl_percent:+.2f}%)")
    print(f"\n👋 Bot stopped")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
