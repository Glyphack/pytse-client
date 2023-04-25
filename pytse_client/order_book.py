import os
from pathlib import Path
import json
import pandas as pd
from pytse_client import utils
from pytse_client.config import ORDER_BOOK_HIST_PATH
from pytse_client.tse_settings import TICKER_ORDER_BOOK
from pytse_client.utils.request_session import requests_retry_session

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
    "ask": "pMeof",
    "vol_bid": "qTitMeDem",
    "vol_ask": "qTitMeof",
    "num_bid": "zOrdMeDem",
    "num_ask": "zOrdMeof",
}


def get_order_book(index, date, to_csv=False, base_path=None):
    session = requests_retry_session()
    url = TICKER_ORDER_BOOK.format(
        index=index, date=date
    )

    print(url)
    response = session.get(url, headers=headers, timeout=10)
    data = json.loads(response.content)
    print(data)
    session.close()

    # data cleanning

    df = pd.DataFrame()

    if to_csv:
        base_path = base_path or ORDER_BOOK_HIST_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)

        path = os.path.join(base_path, "orderbook.csv")
        df.to_csv(path, index=False)

    return df
