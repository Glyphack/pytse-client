import ast
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ShareholderData:
    shares: float
    percentage: float
    instrument_id: str
    name: str


def scrape_daily_info_page_for_shareholder_data(
    daily_info_page: str
) -> Optional[List[ShareholderData]]:
    """
    scrapes and returns shareholders data from a day info page like:
    http://cdn.tsetmc.com/Loader.aspx?ParTree=15131P&i=34557241988629814&d=20200201
    """
    shareholder_data_str = re.findall(
        'ShareHolderData=(.*?);', daily_info_page
    )
    if shareholder_data_str == "[]":
        return
    shareholders_data = ast.literal_eval(shareholder_data_str[0])
    return [
        ShareholderData(
            shares=shareholder_data[2],
            percentage=shareholder_data[3],
            instrument_id=shareholder_data[1],
            name=shareholder_data[5],
        ) for shareholder_data in shareholders_data
    ]


def scrape_daily_info_page_for_date(
    daily_info_page: str
) -> Optional[List[ShareholderData]]:
    daily_info_page_date = re.findall("DEven='(.*?)'", daily_info_page)
    if len(daily_info_page_date) != 1:
        return
    return daily_info_page_date[0]
