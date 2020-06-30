import collections
import functools
import os
import re

import pandas as pd

from pytse_client import config, download, symbols_data, tse_settings, utils
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL

RealtimeTickerInfo = collections.namedtuple(
    'RealtimeTickerInfo',
    ['last_price', 'adj_close']
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
            r"Title='([\D]*)',", self.ticker_page_response.text
        )[0].split("-")[0].strip()

    @property
    def group_name(self) -> str:
        return re.findall(
            r"LSecVal='([\D]*)',", self.ticker_page_response.text
        )[0]

    @property
    def p_e_ratio(self) -> float:
        return self.get_ticker_real_time_info_response().adj_close / self.eps

    @property
    def group_p_e_ratio(self):
        return float(
            re.findall(
                r"SectorPE='([\d.]*)',", self.ticker_page_response.text
            )[0]
        )

    @property
    def eps(self) -> float:
        return float(
            re.findall(
                r"EstimatedEPS='([\d]*)',", self.ticker_page_response.text
            )[0]
        )

    @property
    def base_volume(self):
        return float(
            re.findall(
                r"BaseVol=([\d]*),", self.ticker_page_response.text
            )[0]
        )

    @property
    def last_price(self):
        return self.get_ticker_real_time_info_response().last_price

    @property
    def adj_close(self):
        return self.get_ticker_real_time_info_response().adj_close

    @property
    @functools.lru_cache()
    def ticker_page_response(self):
        return utils.requests_retry_session().get(self._url, timeout=10)

    def get_ticker_real_time_info_response(self) -> RealtimeTickerInfo:
        response = utils.requests_retry_session().get(
          self._info_url, timeout=5
        )
        return RealtimeTickerInfo(
            int(response.text.split()[1].split(",")[1]),
            int(response.text.split()[1].split(",")[2])
        )

    @property
    def client_types(self):
        response = utils.requests_retry_session().get(
            self._client_types_url, timeout=10
        )
        data = response.text.split(";")
        data = [row.split(",") for row in data]
        client_types_data_frame = pd.DataFrame(data, columns=[
            "date",
            "individual_buy_count", "corporate_buy_count",
            "individual_sell_count", "corporate_sell_count",
            "individual_buy_vol", "corporate_buy_vol",
            "individual_sell_vol", "corporate_sell_vol",
            "individual_buy_value", "corporate_buy_value",
            "individual_sell_value", "corporate_sell_value"
        ])
        for i in [
            "individual_buy_", "individual_sell_",
            "corporate_buy_", "corporate_sell_"
        ]:
            client_types_data_frame[f"{i}mean_price"] = (
                    client_types_data_frame[f"{i}value"].astype(float) /
                    client_types_data_frame[f"{i}vol"].astype(float)
            )
        client_types_data_frame["individual_ownership_change"] = (
                client_types_data_frame["corporate_sell_vol"].astype(float) -
                client_types_data_frame["corporate_buy_vol"].astype(float)
        )

        return client_types_data_frame
