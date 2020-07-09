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
    return tickers_dict().get(ticker_symbol)


def all_symbols() -> Set:
    return set(tickers_dict().keys())


def append_symbol_to_file(symbol_id: str, symbol_name: str):
    new_symbol = {symbol_name.strip(): symbol_id.strip()}
    with open(
        f"{config.pytse_dir}/data/symbols_name.json",
        "r+",
        encoding="utf8"
    ) as file:
        data = json.load(file)
        data.update(new_symbol)
        file.seek(0)
        json.dump(data, file, ensure_ascii=False, indent=2)
