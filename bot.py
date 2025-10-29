import os
from binance.client import Client
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# Connect to Binance Testnet
client = Client(api_key, api_secret, testnet=True)

# Fetch latest Bitcoin price
ticker = client.get_symbol_ticker(symbol="BTCUSDT")
print(f"Current BTC Price: {ticker['price']}")
