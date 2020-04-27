import os

import pandas as pd

from pytse_client import config, download, symbols_data, tse_settings


class Ticker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.csv_path = f"{config.DATA_BASE_PATH}/{self.symbol}.csv"
        self._index = symbols_data.get_ticker_index(self.symbol)
        self._url = tse_settings.TSE_TICKRER_ADDRESS.format(self._index)
        self._history: pd.DataFrame = pd.DataFrame()

        if os.path.exists(self.csv_path):
            self.from_file()
        else:
            self.from_web()

    @property
    def history(self):
        return self._history

    @property
    def url(self):
        return self._url

    @property
    def index(self):
        return self._index

    def from_web(self):
        self._history = download(self.symbol)[self.symbol]

    def from_file(self):
        self._history = pd.read_csv(self.csv_path)
