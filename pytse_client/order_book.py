import os
from pathlib import Path
import json
import pandas as pd

from pytse_client.config import ORDER_BOOK_HIST_PATH
from pytse_client.tse_settings import TICKER_ORDER_BOOK
from pytse_client.utils.request_session import requests_retry_session
from pytse_client.symbols_data import get_ticker_index

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Pragma': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
}

keys = {
    "date": "hEven",
    "refID": "refID",
    "depth": "number",
    "bid": "pMeDem",
    "ask": "pMeOf",
    "vol_bid": "qTitMeDem",
    "vol_ask": "qTitMeOf",
    "num_bid": "zOrdMeDem",
    "num_ask": "zOrdMeOf",
}


reversed_keys = {val: key for key, val in keys.items()}
valid_keys = [key for key in keys]


def get_order_book(symbol_name, date, to_csv=False, base_path=None):
    index = get_ticker_index(symbol_name)
    date = date.strftime('%Y%m%d')
    print(f"symbol index is {index}")
    print(f"date is {date}")
    session = requests_retry_session(retries=5, backoff_factor=0.1)
    url = TICKER_ORDER_BOOK.format(
        index=index, date=date
    )

    response = session.get(url, headers=headers, timeout=10)
    data = json.loads(response.content)
    session.close()

    df = pd.json_normalize(data['bestLimitsHistory'])
    if len(df) == 0:
        return pd.DataFrame(columns=valid_keys)
    df.rename(columns=reversed_keys, inplace=True)
    df = df.loc[:, valid_keys]
    df['date'] = pd.to_datetime(
        date + " " + df['date'].astype(str), format='%Y%m%d %H%M%S')
    df = df.sort_values(["date", "depth"], ascending=[True, True])
    df.set_index("date", inplace=True)

    if to_csv:
        base_path = base_path or ORDER_BOOK_HIST_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)

        path = os.path.join(base_path, "orderbook.csv")
        df.to_csv(path, index=False)

    return df
