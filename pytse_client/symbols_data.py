import json
from typing import Set, Dict

from pytse_client import config

ticker_name_to_index_mapping = None


def tickers_dict() -> Dict:
    global ticker_name_to_index_mapping
    if ticker_name_to_index_mapping is None:
        with open(
                f"{config.pytse_dir}/data/symbols_name.json",
                "r",
                encoding="utf8"
        ) as symbols_name:
            ticker_name_to_index_mapping = json.load(symbols_name)
    return ticker_name_to_index_mapping


def get_ticker_index(ticker_symbol: str):
    return tickers_dict()[ticker_symbol]


def all_symbols() -> Set:
    return set(tickers_dict().keys())
