import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

# from utils.scrape import get_html_table_header_and_rows

class StockIndex:
    def __init__(self, url: str, path: str) -> None:
        self._soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        self._path = path

    @property
    def path(self):
        if not self._path:
            return 'scrap_files'
        return self._path

    def _table_scraper(self, table: str, index=0, extra_headers=None):
        """Given the class of table's html tag, will return rows, headers of that table"""
        table = self._soup.find_all(class_=f'{table}')[index]
        headers = [th.text for th in table.thead.find_all('th')]
        if extra_headers:
            for index,header in enumerate(extra_headers): # insert at specific index
                headers.insert(index+1, header)
        rows = [[cell.string for cell in tr if cell != '\n'] for tr in table.tbody.find_all('tr')]
        print(headers,rows)
        return rows, headers

    def index_organizations(self): # شرکت های موجود در شاخص
        rows, headers = self._table_scraper('box1 olive tbl z4_4 h250', index=0, extra_headers=['درصد','درصد'])
        headers.pop(-1) # 30 days header
        for row in rows:
            row.pop(-1) # 30 days cell <img>
        return pd.DataFrame(data=rows, columns=headers)

    def index_history(self): # سابقه شاخص
        table = self._soup.find(class_='box1 silver tbl z4_4 h250').table # index history table
        headers = [th.text for th in table.thead.find_all('th')]
        rows = [[cell.text for cell in tr.find_all('td')[0:4]] for tr in table.tbody.find_all('tr')]
        return pd.DataFrame(data=rows, columns=headers)

    def current_day_index_history(self): # سابقه شاخص روز جاری
        rows, headers = self._table_scraper('box1 olive tbl z4_4 h250', index=1)
        return pd.DataFrame(data=rows, columns=headers)

    def index_by_date(self): # نمودار شاخص
        history_index = requests.get(
            'http://www.tsetmc.com/tsev2/chart/data/Index.aspx?i=32097828799138957&t=value').text
        data = dict([i.split(',') for i in history_index.split(';')])
        df = pd.Series(data=data).to_frame()
        df = df.rename(columns={0:'مقدار'})
        df['تاریخ'] = df.index
        df = df[['تاریخ', 'مقدار']] # reposition
        return df

    def __write_to_csv(self, df, file_name):
        current_path = f'{self.path}/{file_name}.csv'
        Path(self.path).mkdir(parents=True, exist_ok=True)
        df.to_csv(current_path, index=False)
        return current_path 

    def all_to_csv(self): 
        dfs = {
            'سابقه شاخص' : self.index_history(),
            'شرکت های موجود در شاخص': self.index_organizations(),
            'سابقه شاخص روز جاری ': self.current_day_index_history(),
            'نمودار شاخص' : self.index_by_date() 
        }
        for key, value in dfs.items():
            self.__write_to_csv(value, key)
        return self.path 

si = StockIndex('http://www.tsetmc.com/Loader.aspx?ParTree=15131J&i=32097828799138957', 'سابقه')
print(si.all_to_csv())