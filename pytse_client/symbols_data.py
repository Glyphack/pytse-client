import json
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import requests

from pytse_client import config
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.instrument import (
    InstrumentSearchResult,
    parse_instrument_info,
    parse_instrument_search,
)
from pytse_client.utils.persian import replace_arabic

logger = logging.getLogger(config.LOGGER_NAME)

ticker_name_to_index_mapping = None
financial_index_name_to_index_mapping = None


@dataclass
class MarketSymbol:
    code: str
    symbol: str
    name: str
    index: str
    old: list[str]

    def json_value(self) -> dict:
        return {
            "index": self.index,
            "code": self.code,
            "name": self.name,
            "old": self.old,
        }


def unique_ids(ids: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(filter(None, ids)))


def clean_symbol(symbol: str) -> str:
    return replace_arabic(symbol.strip())


def clean_name(name: str) -> str:
    return replace_arabic(name.strip()).replace("\u200c", "").strip()


def financial_indexes_information() -> dict[str, dict]:
    global financial_index_name_to_index_mapping
    if financial_index_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/indices_name.json", "r", encoding="utf8"
        ) as symbols_name:
            financial_index_name_to_index_mapping = json.load(symbols_name)
    return financial_index_name_to_index_mapping


def symbols_information() -> dict[str, dict]:
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


def get_ticker_index(ticker_symbol: str) -> str | None:
    return symbols_information().get(ticker_symbol, {}).get("index")


def get_ticker_old_index(ticker_symbol: str) -> list[str]:
    """Indexes of the deleted instruments of the symbol, they have history
    but no realtime data."""
    return symbols_information().get(ticker_symbol, {}).get("old", []).copy()


def all_symbols() -> set:
    return set(symbols_information().keys())


def map_index_to_symbols() -> dict[str, dict]:
    """
    The symbols by their index:
    {<index>: {"code": <code>, "name": <name>, "old": [...],
    "symbol": <symbol>}}
    """
    return {
        info["index"]: {
            **{key: value for key, value in info.items() if key != "index"},
            "symbol": symbol,
        }
        for symbol, info in symbols_information().items()
    }


def all_financial_index() -> set:
    return set(financial_indexes_information().keys())


def append_symbol_to_file(
    market_symbol: MarketSymbol,
):
    new_symbol = {market_symbol.symbol: market_symbol.json_value()}
    if ticker_name_to_index_mapping is not None:
        ticker_name_to_index_mapping.update(new_symbol)
    with open(
        f"{config.pytse_dir}/data/symbols_name.json", "r+", encoding="utf8"
    ) as file:
        data = json.load(file)
        data.update(new_symbol)
        file.seek(0)
        json.dump(data, file, ensure_ascii=False, indent=2)


def match_search_results(
    results: Sequence[InstrumentSearchResult],
    symbol_name: str,
    preferred_index: str | None = None,
) -> tuple[InstrumentSearchResult | None, list[str]]:
    """The active instrument (None if all are deleted) and the old ones."""
    symbol_name = clean_symbol(symbol_name)
    rows = [
        row for row in results if clean_symbol(row.symbol or "") == symbol_name
    ]
    active_rows = [row for row in rows if not row.is_deleted]
    old_ids = [row.ins_code for row in rows if row.is_deleted]
    active = next(
        (row for row in active_rows if row.ins_code == preferred_index),
        active_rows[0] if active_rows else None,
    )
    return active, unique_ids(old_ids)


def get_symbol_info(symbol_name: str) -> MarketSymbol | None:
    """Look up a symbol that is missing from symbols_name.json.

    Returns None when no active instrument has exactly this symbol.
    """
    symbol = clean_symbol(symbol_name)
    if not symbol:
        return None
    results = parse_instrument_search(
        client.api.call_instrument_search(symbol)
    )
    active, old_ids = match_search_results(results, symbol)
    if active is None:
        return None
    index = active.ins_code
    code = ""
    name = clean_name(active.name or "")
    try:
        info = parse_instrument_info(client.api.call_instrument_info(index))
        code = (info.isin or "").strip()
        name = name or clean_name(info.name or "")
    except (requests.RequestException, KeyError, TypeError, ValueError):
        logger.warning("cannot read the ISIN of %s (%s)", symbol, index)
    return MarketSymbol(
        code=code,
        symbol=symbol,
        name=name,
        index=index,
        old=[old for old in old_ids if old != index],
    )
