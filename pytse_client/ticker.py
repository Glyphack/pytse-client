import os

import pandas as pd

import tse_settings
from pytse_client import config, download, symbols_data


class Ticker:
    def __init__(self, symbol: str):
        self._history: pd.DataFrame = pd.DataFrame()
        self._symbol = symbol
        self._index = symbols_data.get_ticker_index(self._symbol)
        if os.path.exists(self.csv_path):
            self.from_file()
        else:
            self.from_web()

    @property
    def history(self):
        return self._history

    @property
    def csv_path(self):
        return f"{config.DATA_BASE_PATH}/{self._symbol}.csv"

    @property
    def url(self):
        return tse_settings.TSE_TICKER_ADDRESS.format(self._index)

    def from_web(self):
        self._history = download(self._symbol)[self._symbol]

    def from_file(self):
        self._history = pd.read_csv(self.csv_path)
