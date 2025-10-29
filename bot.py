import json
import time
from datetime import datetime
try:
    from websocket import create_connection
except ImportError:
    print("❌ Error: websocket-client not installed")
    print("Please run: pip install websocket-client")
    exit(1)

# === CONFIG ===
BALANCE = 1000.0        # Starting balance in USDT
TRADE_AMOUNT = 100      # Amount per trade
TAKE_PROFIT = 0.0015    # 0.15% profit (easier to hit)
STOP_LOSS = 0.0015      # 0.15% loss
SYMBOL = "btcusdt"      # Trading pair (lowercase)
EXCHANGE = "gate"       # Options: gate, htx (huobi), bitfinex

# === EXCHANGE CONFIGS ===
EXCHANGE_CONFIGS = {
    "gate": {
        "ws_url": "wss://api.gateio.ws/ws/v4/",
        "symbol_format": lambda s: f"{s[:-4]}_{s[-4:]}".upper()  # BTC_USDT
    },
    "htx": {  # Huobi
        "ws_url": "wss://api.huobi.pro/ws",
        "symbol_format": lambda s: s.lower()  # btcusdt
    },
    "bitfinex": {
        "ws_url": "wss://api-pub.bitfinex.com/ws/2",
        "symbol_format": lambda s: f"t{s.upper()}"  # tBTCUSDT
    }
}

# === VARIABLES ===
balance = BALANCE
holding = 0
entry_price = None
trade_count = 0
last_price = None

# === FUNCTIONS ===
def connect_gate():
    """Connect to Gate.io WebSocket"""
    ws = create_connection(EXCHANGE_CONFIGS["gate"]["ws_url"])
    
    symbol = EXCHANGE_CONFIGS["gate"]["symbol_format"](SYMBOL)
    
    subscribe_msg = {
        "time": int(time.time()),
        "channel": "spot.trades",
        "event": "subscribe",
        "payload": [symbol]
    }
    ws.send(json.dumps(subscribe_msg))
    
    response = ws.recv()
    print(f"📡 Gate.io subscription: {response}")
    
    return ws

def connect_htx():
    """Connect to HTX (Huobi) WebSocket"""
    ws = create_connection(EXCHANGE_CONFIGS["htx"]["ws_url"])
    
    symbol = EXCHANGE_CONFIGS["htx"]["symbol_format"](SYMBOL)
    
    subscribe_msg = {
        "sub": f"market.{symbol}.trade.detail",
        "id": "id1"
    }
    ws.send(json.dumps(subscribe_msg))
    
    # HTX sends gzip compressed data, need to handle it
    response = ws.recv()
    print(f"📡 HTX subscription response received")
    
    return ws

def connect_bitfinex():
    """Connect to Bitfinex WebSocket"""
    ws = create_connection(EXCHANGE_CONFIGS["bitfinex"]["ws_url"])
    
    symbol = EXCHANGE_CONFIGS["bitfinex"]["symbol_format"](SYMBOL)
    
    subscribe_msg = {
        "event": "subscribe",
        "channel": "trades",
        "symbol": symbol
    }
    ws.send(json.dumps(subscribe_msg))
    
    # Wait for subscription confirmation
    while True:
        response = ws.recv()
        data = json.loads(response)
        if isinstance(data, dict) and data.get('event') == 'subscribed':
            print(f"📡 Bitfinex subscription: {response}")
            break
    
    return ws

def get_price_gate(ws):
    """Get price from Gate.io WebSocket"""
    try:
        result = ws.recv()
        data = json.loads(result)
        
        if data.get('event') == 'update' and 'result' in data:
            trades = data['result']
            if trades and len(trades) > 0:
                return float(trades[0]['price'])
        
        return None
    except Exception as e:
        return None

def get_price_htx(ws):
    """Get price from HTX WebSocket"""
    import gzip
    
    try:
        result = ws.recv()
        
        # HTX uses gzip compression
        try:
            data = json.loads(gzip.decompress(result).decode('utf-8'))
        except:
            data = json.loads(result)
        
        # Handle ping
        if 'ping' in data:
            ws.send(json.dumps({'pong': data['ping']}))
            return None
        
        # Extract price
        if 'tick' in data and 'data' in data['tick']:
            trades = data['tick']['data']
            if trades and len(trades) > 0:
                return float(trades[0]['price'])
        
        return None
    except Exception as e:
        return None

def get_price_bitfinex(ws):
    """Get price from Bitfinex WebSocket"""
    try:
        result = ws.recv()
        data = json.loads(result)
        
        # Bitfinex sends array format for trades
        if isinstance(data, list) and len(data) > 1:
            if data[1] == 'te':  # Trade executed
                # Format: [CHANNEL_ID, "te", [ID, MTS, AMOUNT, PRICE]]
                if len(data) > 2 and isinstance(data[2], list) and len(data[2]) >= 4:
                    return float(data[2][3])
        
        return None
    except Exception as e:
        return None

def format_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]

# === MAIN LOOP ===
print(f"🚀 Real-Time Scalping Bot Started!")
print(f"   Exchange: {EXCHANGE.upper()} (Philippines-compliant)")
print(f"   Symbol: {SYMBOL.upper()}")
print(f"   Starting Balance: {BALANCE:.2f} USDT")
print(f"   Take Profit: {TAKE_PROFIT*100}% | Stop Loss: {STOP_LOSS*100}%")
print(f"   Press Ctrl+C to stop\n")

try:
    # Connect based on selected exchange
    if EXCHANGE == "gate":
        ws = connect_gate()
        get_price = get_price_gate
    elif EXCHANGE == "htx":
        ws = connect_htx()
        get_price = get_price_htx
    elif EXCHANGE == "bitfinex":
        ws = connect_bitfinex()
        get_price = get_price_bitfinex
    else:
        raise ValueError(f"Unsupported exchange: {EXCHANGE}")
    
    print(f"✅ Connected to {EXCHANGE.upper()} WebSocket\n")
    
    tick_count = 0
    last_status_time = time.time()
    
    while True:
        # Get real-time price
        price = get_price(ws)
        
        if not price:
            continue
        
        last_price = price
        tick_count += 1
        
        # Calculate current portfolio value
        total_value = balance + (holding * price if holding > 0 else 0)
        pnl_amount = total_value - BALANCE
        pnl_percent = (pnl_amount / BALANCE) * 100
        
        # === SHOW STATUS EVERY 5 SECONDS ===
        current_time = time.time()
        if current_time - last_status_time >= 5:
            status = "IN POSITION" if holding > 0 else "WAITING"
            print(f"📊 [{format_time()}] Status: {status}")
            print(f"   Price: ${price:,.2f} | Balance: ${balance:.2f} USDT")
            print(f"   Portfolio Value: ${total_value:.2f} USDT")
            print(f"   Total PnL: ${pnl_amount:+.2f} USDT ({pnl_percent:+.2f}%)")
            if holding > 0:
                unrealized_pnl = (price - entry_price) * holding
                unrealized_pct = ((price - entry_price) / entry_price) * 100
                print(f"   Unrealized P/L: ${unrealized_pnl:+.2f} ({unrealized_pct:+.3f}%)")
            print()
            last_status_time = current_time
        
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
                balance += holding * price
                profit = (price - entry_price) * holding
                profit_pct = ((price - entry_price) / entry_price) * 100
                
                print(f"🟢 [{format_time()}] TAKE PROFIT #{trade_count}")
                print(f"   Entry: ${entry_price:,.2f} → Exit: ${price:,.2f}")
                print(f"   Trade Profit: ${profit:,.2f} (+{profit_pct:.3f}%)")
                print(f"   Balance: ${balance:.2f} USDT")
                print(f"   Total PnL: ${pnl_amount:+.2f} ({pnl_percent:+.2f}%)")
                print(f"   Ticks: {tick_count}\n")
                
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
                print(f"   Ticks: {tick_count}\n")
                
                holding = 0
                entry_price = None
                tick_count = 0
            
            else:
                # Show live position status every 50 ticks
                if tick_count % 50 == 0:
                    unrealized_pnl = (price - entry_price) * holding
                    unrealized_pct = ((price - entry_price) / entry_price) * 100
                    distance_to_tp = ((profit_target - price) / price) * 100
                    distance_to_sl = ((price - stop_target) / price) * 100
                    
                    print(f"📊 [{format_time()}] In Position (Tick #{tick_count})")
                    print(f"   Current: ${price:,.2f} | Entry: ${entry_price:,.2f}")
                    print(f"   Unrealized: ${unrealized_pnl:+.2f} ({unrealized_pct:+.3f}%)")
                    print(f"   To TP: {distance_to_tp:.3f}% | To SL: {distance_to_sl:.3f}%\n")

except KeyboardInterrupt:
    print("\n🛑 Shutting down bot...")
    
    try:
        ws.close()
    except:
        pass
    
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
