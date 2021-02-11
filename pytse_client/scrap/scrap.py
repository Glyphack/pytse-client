import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

from requests.api import head


class MainPageInfo:
    def __init__(self, path=None) -> None:
        self._soup = BeautifulSoup(requests.get('http://www.tsetmc.com/').content, 'lxml') 
        self._blue_tables = self._soup.find_all(class_='box1 blue tbl z1_4 h210') # includes overall tables
        self._silver_tables = self._soup.find_all(class_='box1 white tbl z1_4 h210')
        self._white_tables_1 = self._soup.find_all(class_='box1 white tbl z1_4 h210') # includes stock index effiency tables
        self._white_tables_2 = self._soup.find_all(class_='box1 white tbl z3_4 h210') # includes chosen stocks
        self._white_tables_3 = self._soup.find_all(class_='box1 white tbl z4_4 h210') # includes 2 high transactions and 1 optional transaction.
        self._path = path

    @property
    def silver_tables(self):
        return self._silver_tables

    @property
    def blue_tables(self):
        return self._blue_tables

    @property
    def white_tables(self):
        return self._white_tables

    @property
    def white_tables_1(self):
        return self._white_tables_1

    @property
    def white_tables_2(self):
        return self._white_tables_2

    @property
    def white_tables_3(self):
        return self._white_tables_3

    @property
    def path(self):
        if not self._path:
            return 'scrap_files'
        return self._path

    def overrall_data(self):
        info = {}
        for table in self.blue_tables:
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
        """
        Returns a tuple of headers and rows for the table.
        If df = True returns a dataframe object instead.
        """
        stock_index_effiency_tables = [] # Extract stock effiency tables
        for table in self._white_tables_1:
            for header_pointer in table.find_all(class_='header pointer'):
                if header_pointer.text == 'تاثیر در شاخص':
                    stock_index_effiency_tables.append(table)
        stock_index_effiency_headers = [] 
        for table in stock_index_effiency_tables:
            for th in table.thead.tr.find_all('th'):
                if th.text in stock_index_effiency_headers:
                    continue
                stock_index_effiency_headers.append(th.text)
        stock_index_effiency_rows = [] 
        for table in stock_index_effiency_tables:
            data_set = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                data_set.append(td.text)
                if index % 3 == 0:                              # For appending distinct rows to a row list,   
                    stock_index_effiency_rows.append(data_set)  # we use this way based on number of cells in a row.
                    data_set = []
        return stock_index_effiency_headers, stock_index_effiency_rows

    def stock_effiency_table_csv(self):
        rows = self.stock_effiency_table_data()[1]
        headers = self.stock_effiency_table_data()[0]
        df = pd.DataFrame(data=rows, columns=headers)
        current_path = f'{self.path}/تاثیر در شاخص.csv'
        Path(self.path).mkdir(parents=True, exist_ok=True)
        df.to_csv(current_path, index=False)
        return current_path

    def chosen_stock_index_data(self):
        chosen_stock_headers = []
        for table in self._white_tables_2:
            for th in table.thead.tr.find_all('th'):
                chosen_stock_headers.append(th.text)
        chosen_stock_rows = []
        for table in self._white_tables_2:
            data_set = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                data_set.append(td.text)
                if index % 7 == 0:
                    chosen_stock_rows.append(data_set)
                    data_set = []
        return chosen_stock_headers, chosen_stock_rows

    def chosen_stock_index_csv(self):
        rows = self.chosen_stock_index_data()[1]
        headers = self.chosen_stock_index_data()[0]
        df = pd.DataFrame(data=rows, columns=headers)
        current_path = f'{self.path}/شاخص های منتخب.csv'
        Path(self.path).mkdir(parents=True, exist_ok=True)
        df.to_csv(current_path, index=False)
        return current_path

    def high_transaction_data(self):
        high_transaction_tables = []
        for table in self.white_tables_3:
            if table.find(class_='header pointer').text == 'نمادهای پرتراکنش':
                high_transaction_tables.append(table)
        high_transaction_headers = []
        for table in high_transaction_tables:
            for index, header in enumerate(table.thead.find_all('th'), start=1):
                if '\r\n' in header.text or header.text in high_transaction_headers:
                    continue
                high_transaction_headers.append(header.text)
        high_transaction_rows = []
        for table in high_transaction_tables:
            row = []
            for index, td in enumerate(table.tbody.find_all('td'), start=1):
                if '\u200c' in td.text:
                    td.text.replace('\u200c', '')
                row.append(td.text)
                if index % 10 == 0:
                    high_transaction_rows.append(row)
                    row = []
        for row in high_transaction_rows:
            for index in range(len(row)):
                if index in (1, 3):
                    row[index] += '-' + row[index+1] 
                    row.pop(index+1) # concating two elements into one
        return high_transaction_headers, high_transaction_rows
        
    def high_transaction_csv(self):
        rows = self.high_transaction_data()[1]
        headers = self.high_transaction_data()[0]
        df = pd.DataFrame(data=rows, columns=headers)
        current_path = f'{self.path}/نمادهای پرتراکنش.csv'
        Path(self.path).mkdir(parents=True, exist_ok=True)
        df.to_csv(current_path, index=False)
        return current_path

    def all_to_csv(self):
        self.high_transaction_csv()
        self.chosen_stock_index_csv()
        self.stock_effiency_table_csv()
        self.overall_csv()

        
    