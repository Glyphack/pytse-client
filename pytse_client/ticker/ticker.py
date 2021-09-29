import asyncio
import datetime
import functools
import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional

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
from pytse_client.proxy.dto import ShareholderData
from pytse_client.proxy.tsetmc import get_day_shareholders_history
from pytse_client.ticker.api_extractors import (
    Order,
    TradeSummary,
    get_corporate_trade_summary,
    get_individual_trade_summary,
    get_orders,
)
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL
from tenacity import retry, wait_random
from tenacity.before_sleep import before_sleep_log

logger = logging.getLogger(config.LOGGER_NAME)
logger.addHandler(logging.NullHandler())


@dataclass
class RealtimeTickerInfo:
    last_price: Optional[float]
    adj_close: Optional[float]
    best_demand_vol: Optional[int]
    best_demand_price: Optional[float]
    best_supply_vol: Optional[int]
    best_supply_price: Optional[float]
    sell_orders: Optional[List[Order]]
    buy_orders: Optional[List[Order]]
    individual_trade_summary: Optional[TradeSummary]
    corporate_trade_summary: Optional[TradeSummary]


class Ticker:
    def __init__(
        self,
        symbol: str,
        index: Optional[str] = None,
        adjust: bool = False,
    ):
        self._index = index or symbols_data.get_ticker_index(symbol)
        self.symbol = symbol if index is None else self._index
        self.adjust = adjust
        self.daily_records_csv_path = (
            f"{config.DATA_BASE_PATH}/{self.symbol}.csv"
        )
        self.adjusted_daily_records_csv_path = (
            f"{config.DATA_BASE_PATH}/{self.symbol}-ت.csv"
        )
        self._url = tse_settings.TSE_TICKER_ADDRESS.format(self._index)
        self._info_url = tse_settings.TSE_ISNT_INFO_URL.format(self._index)
        self._client_types_url = TSE_CLIENT_TYPE_DATA_URL.format(self._index)
        self._history: pd.DataFrame = pd.DataFrame()

        if self.adjust:
            if os.path.exists(self.adjusted_daily_records_csv_path):
                self.from_file()
            else:
                self.from_web()
        else:
            if os.path.exists(self.daily_records_csv_path):
                self.from_file()
            else:
                self.from_web()

    def from_web(self):
        self._history = download(
            symbols=self.symbol,
            adjust=self.adjust,
        )[self.symbol]

    def from_file(self):
        if self.adjust:
            self._history = pd.read_csv(self.adjusted_daily_records_csv_path)
        else:
            self._history = pd.read_csv(self.daily_records_csv_path)
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
            conn = aiohttp.TCPConnector(limit=25)
            session = aiohttp.ClientSession(connector=conn)
        tasks = []
        filtered_dates = list(
            filter(
                lambda date: not only_trade_days or
                (only_trade_days and date.date() in self.trade_dates),
                requested_dates,
            )
        )
        for date in filtered_dates:
            tasks.append(
                get_day_shareholders_history(self._index, date, session)
            )
        all_tickers_shareholders: List[List[ShareholderData]
                                       ] = await asyncio.gather(*tasks)
        if session_created is True:
            await session.close()

        rows = []
        for ticker_shareholders, info_date in zip(
            all_tickers_shareholders, filtered_dates
        ):
            for shareholder_data in ticker_shareholders:
                rows.append(
                    [
                        info_date,
                        shareholder_data.id,
                        shareholder_data.shares,
                        shareholder_data.percentage,
                        shareholder_data.instrument_id,
                        shareholder_data.name,
                        shareholder_data.change,
                    ]
                )
        return pd.DataFrame(
            data=rows,
            columns=[
                'date',
                'shareholder_id',
                'shareholder_shares',
                'shareholder_percentage',
                'shareholder_instrument_id',
                'shareholder_name',
                'change',
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
        # when instead of number value is `F`
        except (ValueError, IndexError):
            last_price = None
        try:
            adj_close = int(response.text.split()[1].split(",")[2])
        except (ValueError, IndexError):
            adj_close = None

        response_sections_list = response.text.split(";")

        try:
            orders_section = response_sections_list[2]
            buy_orders, sell_orders = get_orders(orders_section)
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
        except (IndexError):
            buy_orders = []
            sell_orders = []
            logger.warning(
                f"""not enough sections in response to demand
                and supply information resp: {response_sections_list}"""
            )
            best_demand_vol = None
            best_demand_price = None
            best_supply_vol = None
            best_supply_price = None
            buy_orders = None
            sell_orders = None

        if len(response_sections_list) >= 4:
            trade_summary_section = response_sections_list[4]
            individual_trade_summary = get_individual_trade_summary(
                trade_summary_section
            )
            corporate_trade_summary = get_corporate_trade_summary(
                trade_summary_section
            )
        else:
            logger.warning(
                f"""not enough sections in response to extract trade summaries
                resp: {response_sections_list}"""
            )
            individual_trade_summary = None
            corporate_trade_summary = None

        return RealtimeTickerInfo(
            last_price,
            adj_close,
            best_demand_vol=best_demand_vol,
            best_demand_price=best_demand_price,
            best_supply_vol=best_supply_vol,
            best_supply_price=best_supply_price,
            buy_orders=buy_orders,
            sell_orders=sell_orders,
            individual_trade_summary=individual_trade_summary,
            corporate_trade_summary=corporate_trade_summary,
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
