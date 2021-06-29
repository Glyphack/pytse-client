import asyncio
import datetime
import functools
import logging
import os
import re
from typing import List, NamedTuple, Optional

import aiohttp
import bs4
import pandas as pd
import requests
from pytse_client import (
    config,
    symbols_data,
    translations,
    tse_settings,
    utils,
)
from pytse_client.download import download, download_ticker_client_types_record
from pytse_client.scraper import tsetmc_scraper
from pytse_client.ticker.api_extractors import Order, get_orders
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL
from pytse_client.utils import async_utils
from tenacity import retry, wait_random
from tenacity.before_sleep import before_sleep_log

logger = logging.getLogger(config.LOGGER_NAME)
logger.addHandler(logging.NullHandler())


class RealtimeTickerInfo(NamedTuple):
    last_price: float
    adj_close: float
    best_demand_vol: int
    best_demand_price: float
    best_supply_vol: int
    best_supply_price: float
    sell_orders: List[Order]
    buy_orders: List[Order]


class Ticker:
    def __init__(self, symbol: str, index: Optional[str] = None):
        self.symbol = symbol
        self.csv_path = f"{config.DATA_BASE_PATH}/{self.symbol}.csv"
        self._index = index or symbols_data.get_ticker_index(self.symbol)
        self._url = tse_settings.TSE_TICKER_ADDRESS.format(self._index)
        self._info_url = tse_settings.TSE_ISNT_INFO_URL.format(self._index)
        self._client_types_url = TSE_CLIENT_TYPE_DATA_URL.format(self._index)
        self._history: pd.DataFrame = pd.DataFrame()

        if os.path.exists(self.csv_path):
            self.from_file()
        else:
            self.from_web()

    def from_web(self):
        self._history = download(self._index)[self._index]

    def from_file(self):
        self._history = pd.read_csv(self.csv_path)
        self._history["date"] = pd.to_datetime(self._history["date"])

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
    def instrument_id(self):
        """
        instrument id of a ticker is unique and used for calling
        some apis from tsetmc
        """
        return re.findall(
            r"InstrumentID='([\w\d]*)|',$", self._ticker_page_response.text
        )[0]

    @property
    def ci_sin(self):
        """
        instrument id of a ticker is like instrument_id and used for calling
        some apis from tsetmc
        """
        return re.findall(
            r"CIsin='([\w\d]*)|',$", self._ticker_page_response.text
        )[0]

    @property
    def title(self) -> str:
        return re.findall(r"Title='(.*?)',", self._ticker_page_response.text
                          )[0].split("-")[0].strip()

    @property
    def group_name(self) -> str:
        return re.findall(
            r"LSecVal='([\D]*)',", self._ticker_page_response.text
        )[0]

    @property
    def p_e_ratio(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have p/e
        """
        adj_close = self.get_ticker_real_time_info_response().adj_close
        eps = self.eps
        if adj_close is None or eps is None or eps == 0:
            return None
        return self.get_ticker_real_time_info_response().adj_close / self.eps

    @property
    def group_p_e_ratio(self) -> Optional[float]:
        """
        Notes on usage: tickers like وملت does not have group P/E (gpe)
        """
        gpe = re.findall(
            r"SectorPE='([\d.]*)',", self._ticker_page_response.text
        )
        if not gpe or not gpe[0]:
            return None
        return float(gpe[0])

    @property
    def eps(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have eps
        """
        eps = re.findall(
            r"EstimatedEPS='([-,\d]*)',", self._ticker_page_response.text
        )[0]
        if eps == "":
            return None
        return float(eps)

    @property
    def total_shares(self) -> float:
        return float(
            re.findall(r"ZTitad=([-,\d]*),",
                       self._ticker_page_response.text)[0]
        )

    @property
    def base_volume(self) -> float:
        return float(
            re.findall(r"BaseVol=([-,\d]*),",
                       self._ticker_page_response.text)[0]
        )

    @property
    def client_types(self):
        return download_ticker_client_types_record(self._index)

    @property
    def trade_dates(self):
        return self._history["date"].to_list()

    @property
    def shareholders(self) -> pd.DataFrame:
        session = utils.requests_retry_session()
        page = session.get(self._shareholders_url, timeout=5)
        session.close()
        soup = bs4.BeautifulSoup(page.content, 'html.parser')
        table: bs4.PageElement = soup.find_all("table")[0]
        shareholders_df = utils.get_shareholders_html_table_as_csv(table)
        shareholders_df = shareholders_df.rename(
            columns=translations.SHAREHOLDERS_FIELD_MAPPINGS
        )
        return shareholders_df

    def get_shareholders_history(
        self,
        from_when=datetime.timedelta(days=90),
        to_when=datetime.datetime.now(),
        only_trade_days=True,
        session=None
    ) -> pd.DataFrame:
        """
            a helper function to use shareholders_history_async
        """
        return asyncio.run(
            self.get_shareholders_history_async(
                from_when,
                to_when,
                only_trade_days,
                session,
            ),
        )

    async def get_shareholders_history_async(
        self,
        from_when=datetime.timedelta(days=90),
        to_when=datetime.datetime.now(),
        only_trade_days=True,
        session=None,
    ) -> pd.DataFrame:
        requested_dates = utils.datetime_range(to_when - from_when, to_when)
        session_created = False
        if not session:
            session_created = True
            conn = aiohttp.TCPConnector(limit=3)
            session = aiohttp.ClientSession(connector=conn)
        tasks = []
        for date in requested_dates:
            if only_trade_days and date.date() not in self.trade_dates:
                continue
            tasks.append(
                self._get_ticker_daily_info_page_response(
                    session, date.strftime(tse_settings.DATE_FORMAT)
                )
            )
        pages = await async_utils.run_tasks_with_wait(tasks, 30, 10)
        if session_created is True:
            await session.close()
        rows = []
        for page in pages:
            page_date = tsetmc_scraper.scrape_daily_info_page_for_date(page)
            shareholders_data = (
                tsetmc_scraper.
                scrape_daily_info_page_for_shareholder_data(page)
            )
            for shareholder_data in shareholders_data:
                rows.append(
                    [
                        datetime.datetime.strptime(
                            page_date,
                            tse_settings.DATE_FORMAT,
                        ),
                        shareholder_data.shares,
                        shareholder_data.percentage,
                        shareholder_data.instrument_id,
                        shareholder_data.name,
                    ]
                )

        return pd.DataFrame(
            data=rows,
            columns=[
                'date',
                'shares',
                'percentage',
                'instrument_id',
                'shareholder',
            ]
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

    def get_ticker_real_time_info_response(self) -> RealtimeTickerInfo:
        """
        notes on usage:
        - Real time data might not be always available
        check for None values before usage
        """
        session = utils.requests_retry_session()
        response = session.get(self._info_url, timeout=5)
        session.close()

        # in some cases last price or adj price is undefined
        try:
            last_price = int(response.text.split()[1].split(",")[1])
        except (ValueError, IndexError):  # When instead of number value is `F`
            last_price = None
        try:
            adj_close = int(response.text.split()[1].split(",")[2])
        except (ValueError, IndexError):
            adj_close = None

        orders_data = response.text.split(";")[2]
        buy_orders, sell_orders = get_orders(orders_data)

        best_demand_vol = (
            buy_orders[0].volume if 0 < len(buy_orders) else None
        )
        best_demand_price = (
            buy_orders[0].price if 0 < len(buy_orders) else None
        )
        best_supply_vol = (
            sell_orders[0].volume if 0 < len(sell_orders) else None
        )
        best_supply_price = (
            sell_orders[0].price if 0 < len(sell_orders) else None
        )

        return RealtimeTickerInfo(
            last_price,
            adj_close,
            best_demand_vol=best_demand_vol,
            best_demand_price=best_demand_price,
            best_supply_vol=best_supply_vol,
            best_supply_price=best_supply_price,
            buy_orders=buy_orders,
            sell_orders=sell_orders,
        )

    @property
    @functools.lru_cache()
    def _ticker_page_response(self):
        return utils.requests_retry_session().get(self._url, timeout=10)

    @functools.lru_cache()
    @retry(
        wait=wait_random(min=3, max=5),
        before_sleep=before_sleep_log(logger, logging.ERROR)
    )
    async def _get_ticker_daily_info_page_response(
        self, session, date
    ) -> requests.Response:
        async with session.get(
            tse_settings.INSTRUMENT_DAY_INFO_URL.format(
                index=self.index, date=date
            ),
        ) as response:
            response.raise_for_status()
            page = await response.text()
            logger.info(f"fetched date {date}")
            return page

    @property
    def _shareholders_url(self) -> str:
        return tse_settings.TSE_SHAREHOLDERS_URL.format(self.ci_sin)
