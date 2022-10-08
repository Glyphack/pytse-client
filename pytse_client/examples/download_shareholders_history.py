import datetime

from pytse_client import Ticker

symbols = [
    "شکبیر",
    "برکت",
]
from_times = [
    datetime.timedelta(days=90),
    datetime.timedelta(days=150),
]
for symbol, from_when in zip(symbols, from_times):
    print(f"downloading {symbol}")
    Ticker(symbol).get_shareholders_history(from_when=from_when).to_csv(
        f"{symbol}.csv"
    )
    print(f"downloaded {symbol}")
