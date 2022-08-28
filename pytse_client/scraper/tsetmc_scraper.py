import re
from typing import List, Optional


def scrape_daily_info_page_for_date(daily_info_page: str) -> Optional[str]:
    daily_info_page_date = re.findall("DEven='(.*?)'", daily_info_page)
    if len(daily_info_page_date) != 1:
        return
    return daily_info_page_date[0]
