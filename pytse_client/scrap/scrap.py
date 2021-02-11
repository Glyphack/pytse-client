from sys import exc_info
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

from requests.api import head


class MainPageInfo:
    def __init__(self, path=None) -> None:
        self._soup = BeautifulSoup(requests.get('http://www.tsetmc.com/').content, 'lxml') 
        self._blue_tables = self._soup.find_all(class_='box1 blue tbl z1_4 h210') # includes overall tables
        self._white_tables_1 = self._soup.find_all(class_='box1 white tbl z1_4 h210') # includes stock index effiency tables
        self._white_tables_2 = self._soup.find_all(class_='box1 white tbl z3_4 h210') # includes chosen stocks
        self._white_tables_3 = self._soup.find_all(class_='box1 white tbl z4_4 h210') # includes 2 high transactions and 1 optional transaction.
        self._path = path

    @property
    def path(self):
        if not self._path:
            return 'scrap_files'
        return self._path

    def __write_to_csv(self, df, file_name):
        current_path = f'{self.path}/{file_name}.csv'
        Path(self.path).mkdir(parents=True, exist_ok=True)
        df.to_csv(current_path, index=False)
        return current_path 

    def overrall_data(self):
        info = {}
        for table in self._blue_tables:
            table_header = table.find(class_='header').get_text()
            table_data = table.tbody.find_all('td')
            extracted_data = {}
            for i, tr in enumerate(table_data):
                if i % 2 == 0:
                    if tr.div:
                        extracted_data[f'{tr.text}'] = f'{table_data[i+1].text} | {tr.div.text}'
                    else:
                        extracted_data[f'{tr.text}'] = table_data[i+1].text
            info[table_header] = extracted_data
        return info
        
    def overall_csv(self):
        series = [pd.Series(data) for data in self.overrall_data().values()]
        combined = pd.concat(series, axis=1)
        Path(self.path).mkdir(parents=True, exist_ok=True)
        current_path = f'{self.path}/بازار بورس در یک نگاه.csv'
        combined.to_csv(current_path, header=list(self.overrall_data().keys()))
        return current_path

    def stock_effiency_table_data(self, df=False):
        tables = [] # Extract stock effiency tables
        for table in self._white_tables_1:
            for header_pointer in table.find_all(class_='header pointer'):
                if header_pointer.text == 'تاثیر در شاخص':
                    tables.append(table)
        headers = [] 
        for table in tables:
            for th in table.thead.tr.find_all('th'):
                if th.text in headers:
                    continue
                headers.append(th.text)
        rows = [] 
        for table in tables:
            data_set = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                data_set.append(td.text)
                if index % 3 == 0:                              # For appending distinct rows to a row list,   
                    rows.append(data_set)  # we use this way based on number of cells in a row.
                    data_set = []
        return pd.DataFrame(data=rows, columns=headers)

    def stock_effiency_table_csv(self, file_name='تاثیر در شاخص'):
        return self.__write_to_csv(self.stock_effiency_table_data(), file_name)

    def chosen_stock_index_data(self):
        headers = []
        for table in self._white_tables_2:
            for th in table.thead.tr.find_all('th'):
                headers.append(th.text)
        rows = []
        for table in self._white_tables_2:
            data_set = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                data_set.append(td.text)
                if index % 7 == 0:
                    rows.append(data_set)
                    data_set = []
        return pd.DataFrame(data=rows, columns=headers)

    def chosen_stock_index_csv(self, file_name='شاخص های منتخب'):
        return self.__write_to_csv(self.chosen_stock_index_data(), file_name)

    def high_transaction_data(self):
        tables = []
        for table in self._white_tables_3:
            if table.find(class_='header pointer').text == 'نمادهای پرتراکنش':
                tables.append(table)
        headers = []
        for table in tables:
            for index, header in enumerate(table.thead.find_all('th'), start=1):
                if '\r\n' in header.text or header.text in headers:
                    continue
                headers.append(header.text)
        rows = []
        for table in tables:
            row = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                if '\u200c' in td.text:
                    td.text.replace('\u200c', '')
                row.append(td.text)
                if index % 10 == 0:
                    rows.append(row)
                    row = []
        for row in rows:
            for index in range(len(row)):
                if index in (1, 3):
                    row[index] += '-' + row[index+1] 
                    row.pop(index+1) # concating two elements into one
        return pd.DataFrame(data=rows, columns=headers)
        
    def high_transaction_csv(self, file_name='نمادهای پرتراکنش'):
        return self.__write_to_csv(self.high_transaction_data(), file_name)

    def all_to_csv(self):
        self.high_transaction_csv()
        self.chosen_stock_index_csv()
        self.stock_effiency_table_csv()
        self.overall_csv()

        
    