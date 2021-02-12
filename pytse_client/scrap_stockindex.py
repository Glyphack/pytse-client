import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# from utils.scrape import get_html_table_header_and_rows

class StockIndex:
    def __init__(self, url: str) -> None:
        self._soup = BeautifulSoup(requests.get(url).content, 'html.parser')

    def _table_df_convertor(self, table: str, index=0, extra_headers=None):
        table = self._soup.find_all(class_=f'{table}')[index]
        headers = [th.text for th in table.thead.find_all('th')]
        if extra_headers:
            for header in extra_headers: # insert at specific index
                pass
        rows = [[cell.string for cell in tr if cell != '\n'] for tr in table.tbody.find_all('tr')]
        return pd.DataFrame(data=rows, columns=headers)


    def index_history(self):
        table = self._soup.find(class_='box1 silver tbl z4_4 h250').table # index history table
        headers = [th.text for th in table.thead.find_all('th')]
        rows = [[cell.text for cell in tr.find_all('td')[0:4]] for tr in table.tbody.find_all('tr')]
        return pd.DataFrame(data=rows, columns=headers)

    def current_day_index_history(self):
        return self._table_df_convertor('box1 olive tbl z4_4 h250', index=1, extra_headers=['change','change'])