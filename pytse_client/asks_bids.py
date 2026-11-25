import os
from pathlib import Path

import pandas as pd

from pytse_client import symbols_data
from pytse_client.config import ASKS_BIDS_PATH
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.market import parse_market_watch

keys_of_asks_bids = [
    "id",
    "row_number",
    "num_of_sellers",
    "number_of_buyers",
    "buy_price",
    "sell_price",
    "buy_volume",
    "sell_volume",
]


def get_asks_and_bids(to_csv=False, base_path=None):
    market_watch = parse_market_watch(client.api.call_market_watch())
    ticker_ls = [
        {
            "id": instrument.ins_code,
            "row_number": level.level,
            "num_of_sellers": level.sell_count,
            "number_of_buyers": level.buy_count,
            "buy_price": float(level.buy_price),
            "sell_price": float(level.sell_price),
            "buy_volume": level.buy_volume,
            "sell_volume": level.sell_volume,
        }
        for instrument in market_watch
        for level in instrument.best_limits
    ]

    df = pd.DataFrame(ticker_ls, columns=keys_of_asks_bids)
    index_to_symbols_map = symbols_data.map_index_to_symbols()

    df = df[df["id"].isin(index_to_symbols_map.keys())]
    df["symbol"] = df["id"].map(lambda id: index_to_symbols_map[id]["symbol"])

    if to_csv:
        base_path = base_path or ASKS_BIDS_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)

        path = os.path.join(base_path, "bids_asks.csv")
        df.to_csv(path, index=False)

    return df
