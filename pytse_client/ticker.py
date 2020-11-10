import collections
import functools
import os
import re
from typing import Optional

import pandas as pd

from pytse_client import config, download, symbols_data, tse_settings, utils
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL
from pytse_client.download import download_ticker_client_types_record

RealtimeTickerInfo = collections.namedtuple(
    'RealtimeTickerInfo',
    ['last_price',
     'adj_close',
     'best_demand_vol',
     'best_demand_price',
     'best_supply_vol',
     'best_supply_price']
)


class Ticker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.csv_path = f"{config.DATA_BASE_PATH}/{self.symbol}.csv"
        self._index = symbols_data.get_ticker_index(self.symbol)
        self._url = tse_settings.TSE_TICKER_ADDRESS.format(self._index)
        self._info_url = tse_settings.TSE_ISNT_INFO_URL.format(self._index)
        self._client_types_url = TSE_CLIENT_TYPE_DATA_URL.format(self._index)
        self._history: pd.DataFrame = pd.DataFrame()

        if os.path.exists(self.csv_path):
            self.from_file()
        else:
            self.from_web()

    def from_web(self):
        self._history = download(self.symbol)[self.symbol]

    def from_file(self):
        self._history = pd.read_csv(self.csv_path)

    @property
    def history(self):
        return self._history

    @property
    def url(self):
        return self._url

    @property
    def index(self):
        return self._index

    @property
    def title(self) -> str:
        return re.findall(
            r"Title='(.*?)',", self.ticker_page_response.text
        )[0].split("-")[0].strip()

    @property
    def group_name(self) -> str:
        return re.findall(
            r"LSecVal='([\D]*)',", self.ticker_page_response.text
        )[0]

    @property
    def p_e_ratio(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have p/e
        """
        adj_close = self.get_ticker_real_time_info_response().adj_close
        eps = self.eps
        if adj_close is None or eps is None:
            return None
        return self.get_ticker_real_time_info_response().adj_close / self.eps

    @property
    def group_p_e_ratio(self) -> Optional[float]:
        """
        Notes on usage: tickers like وملت does not have group P/E (gpe)
        """
        gpe = re.findall(
            r"SectorPE='([\d.]*)',", self.ticker_page_response.text
        )[0]
        if gpe == "":
            return None
        return float(gpe)

    @property
    def eps(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have eps
        """
        eps = re.findall(
            r"EstimatedEPS='([-,\d]*)',", self.ticker_page_response.text
        )[0]
        if eps == "":
            return None
        return float(eps)

    @property
    def base_volume(self):
        return float(
            re.findall(r"BaseVol=([-,\d]*),",
                       self.ticker_page_response.text)[0]
        )

    @property
    def last_price(self):
        return self.get_ticker_real_time_info_response().last_price

    @property
    def adj_close(self):
        return self.get_ticker_real_time_info_response().adj_close

    @property
    def best_demand_vol(self):
        return self.get_ticker_real_time_info_response().best_demand_vol

    @property
    def best_demand_price(self):
        return self.get_ticker_real_time_info_response().best_demand_price

    @property
    def best_supply_vol(self):
        return self.get_ticker_real_time_info_response().best_supply_vol

    @property
    def best_supply_price(self):
        return self.get_ticker_real_time_info_response().best_supply_price

    @property
    @functools.lru_cache()
    def ticker_page_response(self):
        return utils.requests_retry_session().get(self._url, timeout=10)

    def get_ticker_real_time_info_response(self) -> RealtimeTickerInfo:
        """
        notes on usage:
        - Real time data might not be always available
        check for None values before usage
        """
        response = utils.requests_retry_session().get(
            self._info_url, timeout=5
        )
        # check supply and demand data exists
        if response.text.split(";")[2] != "":
            best_demand_vol = int(response.text.split(";")[2].split("@")[1])
            best_demand_price = int(response.text.split(";")[2].split("@")[2])
            best_supply_vol = int(response.text.split(";")[2].split("@")[4])
            best_supply_price = int(response.text.split(";")[2].split("@")[3])
        else:
            best_demand_vol = None
            best_demand_price = None
            best_supply_vol = None
            best_supply_price = None

        # in some cases last price or adj price is undefined
        try:
            last_price = int(response.text.split()[1].split(",")[1])
        except (ValueError, IndexError):  # When instead of number value is `F`
            last_price = None
        try:
            adj_close = int(response.text.split()[1].split(",")[2])
        except (ValueError, IndexError):
            adj_close = None
        return RealtimeTickerInfo(
            last_price,
            adj_close,
            best_demand_vol=best_demand_vol,
            best_demand_price=best_demand_price,
            best_supply_vol=best_supply_vol,
            best_supply_price=best_supply_price,
        )

    @property
    def client_types(self):
        return download_ticker_client_types_record(self._index)
