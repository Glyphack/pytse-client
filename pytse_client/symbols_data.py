import json
from typing import Dict, List, Optional, Set

from pytse_client import config
from pytse_client.scraper.symbol_scraper import MarketSymbol

ticker_name_to_index_mapping = None
financial_index_name_to_index_mapping = None


def financial_indexes_information() -> Dict[str, Dict]:
    global financial_index_name_to_index_mapping
    if financial_index_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/indices_name.json", "r", encoding="utf8"
        ) as symbols_name:
            financial_index_name_to_index_mapping = json.load(symbols_name)
    return financial_index_name_to_index_mapping


def symbols_information() -> Dict[str, Dict]:
    global ticker_name_to_index_mapping
    if ticker_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/symbols_name.json", "r", encoding="utf8"
        ) as symbols_name:
            ticker_name_to_index_mapping = json.load(symbols_name)
    return ticker_name_to_index_mapping


def get_financial_index(financial_index_name: str):
    return (
        financial_indexes_information()
        .get(financial_index_name, {})
        .get("index")
    )


def get_ticker_index(ticker_symbol: str) -> Optional[str]:
    return symbols_information().get(ticker_symbol, {}).get("index")


def get_ticker_old_index(ticker_symbol: str) -> List[str]:
    """
    Returns list of deactivated ticket indexes with this symbol.
    Deactivated symbols contain historical data but not real time.
    Args:
        ticker_symbol: symbol name in persian

    Returns: index of old(deactivated) tickers with this symbol


    """
    return symbols_information().get(ticker_symbol, {}).get("old", []).copy()


def all_symbols() -> Set:
    return set(symbols_information().keys())


def all_financial_index() -> Set:
    return set(financial_indexes_information().keys())


def append_symbol_to_file(
    market_symbol: MarketSymbol,
):
    global ticker_name_to_index_mapping
    new_symbol = {
        market_symbol.symbol: {
            "index": market_symbol.index,
            "code": market_symbol.code,
            "name": market_symbol.name,
            "old": market_symbol.old,
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
