import json
import time
from datetime import datetime
from websocket import create_connection

# === CONFIG ===
BALANCE = 1000.0        # Starting balance in USDT
TRADE_AMOUNT = 100      # Amount per trade
TAKE_PROFIT = 0.001     # 0.1% profit
STOP_LOSS = 0.001       # 0.1% loss
SYMBOL = "BTCUSDT"      # Trading pair (uppercase for Bybit)
EXCHANGE = "bybit"      # Options: bybit, okx, kucoin

# === EXCHANGE WEBSOCKET URLS ===
WEBSOCKET_URLS = {
    "bybit": f"wss://stream.bybit.com/v5/public/linear",
    "okx": f"wss://ws.okx.com:8443/ws/v5/public",
    "kucoin": f"wss://ws-api-spot.kucoin.com/"  # Requires token setup
}

# === VARIABLES ===
balance = BALANCE
holding = 0
entry_price = None
trade_count = 0
last_price = None

# === FUNCTIONS ===
def connect_bybit():
    """Connect to Bybit WebSocket for real-time price updates"""
    ws = create_connection(WEBSOCKET_URLS["bybit"])
    
    # Subscribe to trades stream
    subscribe_msg = {
        "op": "subscribe",
        "args": [f"publicTrade.{SYMBOL}"]
    }
    ws.send(json.dumps(subscribe_msg))
    
    # Wait for subscription confirmation
    response = ws.recv()
    print(f"📡 Bybit subscription: {response}")
    
    return ws

def connect_okx():
    """Connect to OKX WebSocket for real-time price updates"""
    ws = create_connection(WEBSOCKET_URLS["okx"])
    
    # Subscribe to trades stream
    subscribe_msg = {
        "op": "subscribe",
        "args": [{
            "channel": "trades",
            "instId": f"{SYMBOL.replace('USDT', '-USDT')}"
        }]
    }
    ws.send(json.dumps(subscribe_msg))
    
    # Wait for subscription confirmation
    response = ws.recv()
    print(f"📡 OKX subscription: {response}")
    
    return ws

def get_price_bybit(ws):
    """Get instant price from Bybit WebSocket"""
    try:
        result = ws.recv()
        data = json.loads(result)
        
        # Handle heartbeat
        if data.get('op') == 'ping':
            ws.send(json.dumps({"op": "pong"}))
            return None
        
        # Extract price from trade data
        if 'data' in data and len(data['data']) > 0:
            return float(data['data'][0]['p'])
        
        return None
    except Exception as e:
        return None

def get_price_okx(ws):
    """Get instant price from OKX WebSocket"""
    try:
        result = ws.recv()
        data = json.loads(result)
        
        # Extract price from trade data
        if 'data' in data and len(data['data']) > 0:
            return float(data['data'][0]['px'])
        
        return None
    except Exception as e:
        return None

def format_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]

# === MAIN LOOP ===
print(f"🚀 Real-Time Scalping Bot Started!")
print(f"   Exchange: {EXCHANGE.upper()}")
print(f"   Symbol: {SYMBOL}")
print(f"   Starting Balance: {BALANCE:.2f} USDT")
print(f"   Take Profit: {TAKE_PROFIT*100}% | Stop Loss: {STOP_LOSS*100}%")
print(f"   Press Ctrl+C to stop\n")

try:
    # Connect based on selected exchange
    if EXCHANGE == "bybit":
        ws = connect_bybit()
        get_price = get_price_bybit
    elif EXCHANGE == "okx":
        ws = connect_okx()
        get_price = get_price_okx
    else:
        raise ValueError(f"Unsupported exchange: {EXCHANGE}")
    
    print(f"✅ Connected to {EXCHANGE.upper()} WebSocket\n")
    
    tick_count = 0
    
    while True:
        # Get real-time price (updates multiple times per second)
        price = get_price(ws)
        
        if not price:
            continue
        
        last_price = price
        tick_count += 1
        
        # Calculate current portfolio value
        total_value = balance + (holding * price if holding > 0 else 0)
        pnl_amount = total_value - BALANCE
        pnl_percent = (pnl_amount / BALANCE) * 100
        
        # === ENTER POSITION ===
        if holding == 0 and balance >= TRADE_AMOUNT:
            holding = TRADE_AMOUNT / price
            balance -= TRADE_AMOUNT
            entry_price = price
            trade_count += 1
            
            print(f"🟢 [{format_time()}] BUY #{trade_count}")
            print(f"   Price: ${price:,.2f}")
            print(f"   Amount: {holding:.6f} BTC")
            print(f"   Entry: ${entry_price:,.2f}")
            print(f"   Target TP: ${entry_price * (1 + TAKE_PROFIT):,.2f} (+{TAKE_PROFIT*100}%)")
            print(f"   Target SL: ${entry_price * (1 - STOP_LOSS):,.2f} (-{STOP_LOSS*100}%)\n")
        
        # === EXIT POSITION ===
        elif holding > 0 and entry_price:
            profit_target = entry_price * (1 + TAKE_PROFIT)
            stop_target = entry_price * (1 - STOP_LOSS)
            
            # Check if TP or SL is hit
            if price >= profit_target:
                # TAKE PROFIT
                balance += holding * price
                profit = (price - entry_price) * holding
                profit_pct = ((price - entry_price) / entry_price) * 100
                
                print(f"🟢 [{format_time()}] TAKE PROFIT #{trade_count}")
                print(f"   Entry: ${entry_price:,.2f} → Exit: ${price:,.2f}")
                print(f"   Trade Profit: ${profit:,.2f} (+{profit_pct:.3f}%)")
                print(f"   Balance: ${balance:.2f} USDT")
                print(f"   Total PnL: ${pnl_amount:+.2f} ({pnl_percent:+.2f}%)")
                print(f"   Ticks processed: {tick_count}\n")
                
                holding = 0
                entry_price = None
                tick_count = 0
                
            elif price <= stop_target:
                # STOP LOSS
                balance += holding * price
                loss = (price - entry_price) * holding
                loss_pct = ((price - entry_price) / entry_price) * 100
                
                print(f"🔴 [{format_time()}] STOP LOSS #{trade_count}")
                print(f"   Entry: ${entry_price:,.2f} → Exit: ${price:,.2f}")
                print(f"   Trade Loss: ${loss:,.2f} ({loss_pct:.3f}%)")
                print(f"   Balance: ${balance:.2f} USDT")
                print(f"   Total PnL: ${pnl_amount:+.2f} ({pnl_percent:+.2f}%)")
                print(f"   Ticks processed: {tick_count}\n")
                
                holding = 0
                entry_price = None
                tick_count = 0
            
            else:
                # Show live position status every 100 ticks
                if tick_count % 100 == 0:
                    unrealized_pnl = (price - entry_price) * holding
                    unrealized_pct = ((price - entry_price) / entry_price) * 100
                    distance_to_tp = ((profit_target - price) / price) * 100
                    distance_to_sl = ((price - stop_target) / price) * 100
                    
                    print(f"📊 [{format_time()}] In Position (Tick #{tick_count})")
                    print(f"   Current: ${price:,.2f} | Entry: ${entry_price:,.2f}")
                    print(f"   Unrealized: ${unrealized_pnl:+.2f} ({unrealized_pct:+.3f}%)")
                    print(f"   Distance to TP: {distance_to_tp:.3f}% | SL: {distance_to_sl:.3f}%")
                    print(f"   Portfolio: ${total_value:.2f} USDT\n")

except KeyboardInterrupt:
    print("\n🛑 Shutting down bot...")
    
    # Close WebSocket
    try:
        ws.close()
    except:
        pass
    
    # Final calculation
    if holding > 0 and last_price:
        print(f"⚠️  Still holding {holding:.6f} BTC")
        print(f"   Last price: ${last_price:,.2f}")
        total_value = balance + (holding * last_price)
    else:
        total_value = balance
    
    pnl_amount = total_value - BALANCE
    pnl_percent = (pnl_amount / BALANCE) * 100
    
    win_rate = "N/A"
    if trade_count > 0:
        print(f"\n📈 FINAL RESULTS")
        print(f"   Starting Balance: ${BALANCE:.2f} USDT")
        print(f"   Final Balance: ${total_value:.2f} USDT")
        print(f"   Total Trades: {trade_count}")
        print(f"   Profit/Loss: ${pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
    
    print(f"\n👋 Bot stopped successfully")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nBot crashed. Please restart.")
