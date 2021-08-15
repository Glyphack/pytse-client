import requests
import json
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup


@dataclass
class MarketSymbols:
    code: str  # 0
    symbol: str  # 6
    name: str  # 7
    index: int  # 6 or 7

def replace_arabic(string: str):
    return string.replace('ك', 'ک').replace('ي', 'ی').strip()

def get_soup(url) -> BeautifulSoup:
    response = requests.get(url)
    return BeautifulSoup(response.content, 'html.parser')


# Theres no thead or tbody in this table tag,
# so we elimante first loop since its the table headers.


def get_market_symbols() -> List[MarketSymbols]:
    url = 'http://www.tsetmc.com/Loader.aspx?ParTree=111C1417' # لیست نماد های بازار های عادی
    soup = get_soup(url)
    table = soup.find("table")
    market_symbols = []
    table_rows = table.find_all('tr')[1:]  # remove table header.
    for table_row in table_rows:
        row_data = table_row.find_all('td')
        market_symbols.append(MarketSymbols(
            code=row_data[0].text,
            symbol=replace_arabic(row_data[6].a.text),
            name=replace_arabic(row_data[7].a.text).replace('\u200c', ''),
            index=row_data[6].a.get('href').partition('inscode=')[2]
        ))
    return market_symbols


def write_symbols_to_json(
    market_symbols: MarketSymbols,
    filename: str, 
    path: str
) -> None:
    with open(
        f'{path}/{filename}.json',
        'w',
        encoding='utf8'
    ) as file:
        data = {obj.symbol: obj.index for obj in market_symbols}
        json.dump(data, file, ensure_ascii=False, indent=2)
