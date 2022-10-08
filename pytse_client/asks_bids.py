import os
from pathlib import Path

import pandas as pd
from pytse_client import utils
from pytse_client.config import ASKS_BIDS_PATH
from pytse_client.ticker_statisticals import get_keys_of_asks_bids
from pytse_client.tse_settings import MARKET_WATCH_URL
from pytse_client.utils.request_session import requests_retry_session

keys_of_asks_bids = get_keys_of_asks_bids()


def get_asks_and_bids(to_csv=False, base_path=None):
    session = requests_retry_session()
    raw_text = session.get(MARKET_WATCH_URL, timeout=10).text
    session.close()
    raw_tickers = raw_text.split("@")[3].split(";")
    ticker_ls = [raw.split(",") for raw in raw_tickers]

    df = pd.DataFrame(ticker_ls, columns=keys_of_asks_bids)
    index_to_symbols_map = utils.map_index_to_symbols()

    # filter df only if id is in index_to_symbols_map
    df = df[df["id"].isin(index_to_symbols_map.keys())]
    # create symbol based on map
    df["symbol"] = df["id"].map(
        lambda id: index_to_symbols_map.get(id)["symbol"]
    )

    if to_csv:
        base_path = base_path or ASKS_BIDS_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)

        path = os.path.join(base_path, "bids_asks.csv")
        df.to_csv(path, index=False)

    return df
