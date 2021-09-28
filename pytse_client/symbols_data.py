import json
from typing import Dict, Set

from pytse_client import config
from pytse_client.scraper.symbol_scraper import MarketSymbol

ticker_name_to_index_mapping = None


def symbols_information() -> Dict[str, Dict]:
    global ticker_name_to_index_mapping
    if ticker_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/symbols_name.json", "r", encoding="utf8"
        ) as symbols_name:
            ticker_name_to_index_mapping = json.load(symbols_name)
    return ticker_name_to_index_mapping


def get_ticker_index(ticker_symbol: str):
    return symbols_information().get(ticker_symbol, {}).get("index")


def get_ticker_old_index(ticker_symbol: str):
    return symbols_information().get(ticker_symbol, {}).get("old", []).copy()


def all_symbols() -> Set:
    return set(symbols_information().keys())


def append_symbol_to_file(
    market_symbol: MarketSymbol,
):
    global ticker_name_to_index_mapping
    new_symbol = {
        market_symbol.symbol: {
                "index": market_symbol.index,
                "code": market_symbol.code,
                "name": market_symbol.name,
                "old": market_symbol.old
            }
    }
    if ticker_name_to_index_mapping is not None:
        ticker_name_to_index_mapping.update(new_symbol)
    with open(
        f"{config.pytse_dir}/data/symbols_name.json", "r+", encoding="utf8"
    ) as file:
        data = json.load(file)
        data.update(new_symbol)
        file.seek(0)
        json.dump(data, file, ensure_ascii=False, indent=2)
