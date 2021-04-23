from time import sleep
from pytse_client import Ticker
symbols = ["شکبیر", "برکت"]

for symbol in symbols:
    print(f"downloading {symbol}")
    Ticker(symbol).get_shareholders_history().to_csv(f"str(symbol).csv")
    print(f"downloaded {symbol} complete")
    # sleep between to avoid getting blocked
    sleep(50)
