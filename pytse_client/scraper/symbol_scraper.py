import logging
import re
from dataclasses import dataclass
from typing import List

import requests
from bs4 import BeautifulSoup
from pytse_client import config, tse_settings
from pytse_client.utils.persian import replace_arabic

logger = logging.getLogger(config.LOGGER_NAME)


@dataclass
class MarketSymbol:
    code: str
    symbol: str
    name: str
    index: int

    def __hash__(self) -> int:
        """
        Hash function is used to deduplicate list of market symbols
        """
        return int(self.index)


def get_market_symbols_from_symbols_list_page() -> List[MarketSymbol]:
    """uses SYMBOLS_LIST_URL and scrapes symbols information from the page

    :return: list of all market symbols
    :rtype: List[MarketSymbol]
    """
    url = tse_settings.SYMBOLS_LIST_URL
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    table = soup.find("table")
    market_symbols = []
    # Theres no thead or tbody in this table tag
    # so we eliminate first loop since its the table headers.
    table_rows = table.find_all('tr')[1:]
    for table_row in table_rows:
        row_data = table_row.find_all('td')
        market_symbols.append(
            MarketSymbol(
                code=row_data[0].text,
                symbol=replace_arabic(row_data[6].a.text),
                name=replace_arabic(row_data[7].a.text).replace('\u200c', ''),
                index=row_data[6].a.get('href').partition('inscode=')[2],
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

    if len(response_groups) < 3 or response_groups[2].split(";"):
        logger.error(
            "symbols information from market watch page is not valid",
            extra={"response": response}
        )

    symbols_data = response_groups[2].split(";")

    market_symbols = []
    for symbol_data in symbols_data:
        data = symbol_data.split(",")
        symbol_name_ends_with_number = re.search(r'\d+$', data[2])

        # if symbol name ends with number it's some kind of symbol
        # like 'حق تقدم' and we don't want it
        if symbol_name_ends_with_number:
            continue

        market_symbols.append(
            MarketSymbol(
                code=replace_arabic(data[1]),
                symbol=replace_arabic(data[2]),
                index=replace_arabic(data[0]),
                name=replace_arabic(data[3])
            )
        )

    return market_symbols
