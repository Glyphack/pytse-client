import locale
import logging
import re
from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup
from pytse_client import config, tse_settings
from pytse_client.utils import requests_retry_session
from pytse_client.utils.persian import replace_arabic
from requests import HTTPError

logger = logging.getLogger(config.LOGGER_NAME)


@dataclass
class MarketSymbol:
    code: str
    symbol: str
    name: str
    index: str
    old: List[int]

    def __hash__(self):
        """Hash function is used for deduplication"""
        return hash(self.symbol)

    def __lt__(self, other):
        return not locale.strcoll(other.symbol, self.symbol) < 0

    def __eq__(self, other):
        return locale.strcoll(other.symbol, self.symbol) == 0


def get_market_symbols_from_symbols_list_page() -> List[MarketSymbol]:
    """uses SYMBOLS_LIST_URL and scrapes symbols information from the page

    :return: list of all market symbols
    :rtype: List[MarketSymbol]
    """
    url = tse_settings.SYMBOLS_LIST_URL
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    table = soup.find("table")
    market_symbols = []
    # Theres no thead or tbody in this table tag
    # so we eliminate first loop since its the table headers.
    table_rows = table.find_all("tr")[1:]
    for table_row in table_rows:
        row_data = table_row.find_all("td")
        # escape old symbols
        if row_data[7].a.text.startswith("حذف-"):
            continue
        market_symbols.append(
            MarketSymbol(
                code=row_data[0].text,
                symbol=replace_arabic(row_data[6].a.text),
                name=replace_arabic(row_data[7].a.text).replace("\u200c", ""),
                index=row_data[6].a.get("href").partition("inscode=")[2],
                old=[],
            )
        )
    return market_symbols


def get_market_symbols_from_market_watch_page() -> List[MarketSymbol]:
    """get symbols list from market watch page

    :return: list of market symbols
    :rtype: List[MarketSymbol]
    """
    response = requests.get(tse_settings.MARKET_WATCH_INIT_URL)

    # response contain different groups for different data
    response_groups = response.text.split("@")

    if len(response_groups) < 3:
        logger.error(
            "symbols information from market watch page is not valid",
            extra={"response": response},
        )

    symbols_data = response_groups[2].split(";")

    market_symbols = []
    for symbol_data in symbols_data:
        data = symbol_data.split(",")
        symbol_name_ends_with_number = re.search(r"\d+$", data[2])

        # if symbol name ends with number it's some kind of symbol
        # like 'حق تقدم' and we don't want it
        if symbol_name_ends_with_number:
            continue

        market_symbols.append(
            MarketSymbol(
                code=replace_arabic(data[1]),
                symbol=replace_arabic(data[2]),
                index=replace_arabic(data[0]),
                name=replace_arabic(data[3]).replace("\u200c", ""),
                old=[],
            )
        )

    return market_symbols


def add_old_indexes_to_market_symbols(
    symbols: List[MarketSymbol],
) -> List[MarketSymbol]:
    """
    get old symbols list from search page

    Parameters
    ----------
    market_symbols : List[MarketSymbol]
        list of market symbols.

    Returns
    -------
    List[MarketSymbol]
        list of market symbols.

    """
    market_symbols = []

    for symbol in symbols:
        index, old_ids = get_symbol_ids(symbol.symbol)
        if index is None:
            index = symbol.index
        market_symbols.append(
            MarketSymbol(
                code=symbol.code,
                symbol=symbol.symbol,
                index=index,
                name=symbol.name,
                old=old_ids,
            )
        )

    return market_symbols


def get_symbol_ids(symbol_name: str):
    url = tse_settings.TSE_SYMBOL_ID_URL.format(symbol_name.strip())
    response = requests_retry_session().get(url, timeout=10)
    try:
        response.raise_for_status()
    except HTTPError:
        raise Exception(f"{symbol_name}: Sorry, tse server did not respond")

    symbols = response.text.split(";")
    index = None
    old_ids = []
    for symbol_full_info in symbols:
        if symbol_full_info.strip() == "":
            continue
        symbol_full_info = symbol_full_info.split(",")
        if replace_arabic(symbol_full_info[0]) == symbol_name:
            if symbol_full_info[7] == "1":
                index = symbol_full_info[2]  # active symbol id
            else:
                old_ids.append(symbol_full_info[2])  # old symbol id

    return index, old_ids
