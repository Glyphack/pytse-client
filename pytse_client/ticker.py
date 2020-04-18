import re

import pandas as pd
from requests import HTTPError

from pytse_client import config, download
from pytse_client.utils import requests_retry_session

NAME_REGEX = r"LVal18AFC='([\D]*)',"


class Ticker:
    def __init__(self, index: str):
        self._history: pd.DataFrame = pd.DataFrame()
        self._index = index

    def from_web(self):
        self._history = download(self._index)[self._index]

    def from_file(self, name: str = None, base_path: str = config.BASE_PATH):
        if name is None:
            name = self._index
        self._history = pd.read_csv(f"{base_path}/{name}.csv")

    @property
    def history(self):
        return self._history

    @property
    def symbol(self):
        return re.findall(NAME_REGEX, self.home_response().text)[0]

    def home_url(self):
        return config.TSE_TICKER_ADDRESS.format(self._index)

    def home_response(self):
        try:
            response = requests_retry_session().get(
                self.home_url(), timeout=10
            )
            response.raise_for_status()
        except HTTPError:
            return self.home_response()
