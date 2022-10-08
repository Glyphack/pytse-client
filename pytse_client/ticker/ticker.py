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
from pytse_client.proxy.dto import InstrumentHistoryResponse, ShareholderData
from pytse_client.proxy.tsetmc import (
    get_day_shareholders_history,
    get_day_ticker_info_history,
)
from pytse_client.ticker.api_extractors import (
    Order,
    TradeSummary,
    get_corporate_trade_summary,
    get_individual_trade_summary,
    get_orders,
)
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL
from pytse_client.utils.decorators import catch
from pytse_client.utils.persian import replace_arabic, replace_persian
from tenacity import retry
from tenacity.before_sleep import before_sleep_log
from tenacity.wait import wait_random

logger = logging.getLogger(config.LOGGER_NAME)
logger.addHandler(logging.NullHandler())


@dataclass
class RealtimeTickerInfo:
    date_time: datetime.datetime
    state: Optional[str]
    last_price: Optional[float]
    adj_close: Optional[float]
    yesterday_price: Optional[float]
    open_price: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    count: Optional[int]
    volume: Optional[int]
    value: Optional[int]
    last_date: Optional[datetime.datetime]
    best_demand_vol: Optional[int]
    best_demand_price: Optional[float]
    best_supply_vol: Optional[int]
    best_supply_price: Optional[float]
    sell_orders: Optional[List[Order]]
    buy_orders: Optional[List[Order]]
    individual_trade_summary: Optional[TradeSummary]
    corporate_trade_summary: Optional[TradeSummary]
    nav: Optional[int]
    nav_date: Optional[str]
    # ارزش بازار
    market_cap: Optional[int]


class Ticker:
    def __init__(
        self,
        symbol: str,
        index: Optional[str] = None,
        adjust: bool = False,
    ):
        determined_symbol_index = index or symbols_data.get_ticker_index(
            symbol
        )
        if determined_symbol_index is None:
            raise ValueError(
                f"""Symbol {symbol} not found, if you are trying to use
                             a symbol which is removed from the tse website
                             provide it's index manually:
                             ticker = tse.Ticker("", index="25165947991415904")
                             """
            )
        self._index = determined_symbol_index
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
        # TODO: if symbol equals instrument id, it cannot fetch introduction
        # page. it occurs when Ticker called with index id not symbol
        self._introduction_url = (
            tse_settings.TSE_TICKER_INTRODUCTION_URL.format(
                replace_persian(self.symbol)
            )
        )
        self._history: pd.DataFrame = pd.DataFrame()

        if self.adjust:
            if os.path.exists(self.adjusted_daily_records_csv_path):
                self._history = self.from_file()
            else:
                self._history = download(
                    symbols=self.symbol,
                    adjust=self.adjust,
                )[self.symbol]
        else:
            if os.path.exists(self.daily_records_csv_path):
                self._history = self.from_file()
            else:
                self._history = download(
                    symbols=self.symbol,
                    adjust=self.adjust,
                )[self.symbol]

    def from_file(self) -> pd.DataFrame:
        if self.adjust:
            history = pd.read_csv(self.adjusted_daily_records_csv_path)
        else:
            history = pd.read_csv(self.daily_records_csv_path)
        history["date"] = pd.to_datetime(history["date"])
        return history

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
        """
        Symbol title in persian
        """
        return replace_arabic(
            re.findall(r"Title='(.*?)',", self._ticker_page_response.text)[
                0
            ].split("-")[0]
        )

    @property
    def fulltitle(self) -> str:
        """
        Symbol title with it's market in persian
        """
        return replace_arabic(
            re.findall(r"Title='(.*?)',", self._ticker_page_response.text)[0]
        )

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
        return adj_close / eps

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
    def p_s_ratio(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have p/s
        """
        adj_close = self.get_ticker_real_time_info_response().adj_close
        psr = self.psr
        if adj_close is None or psr is None or psr == 0:
            return None
        return adj_close / psr

    @property
    def psr(self) -> Optional[float]:
        """
        Notes on usage: tickers like آسام does not have psr
        """
        psr = re.findall(
            r"PSR='([+-]?[\.\d]*)'", self._ticker_page_response.text
        )
        if not psr or psr[0] == "":
            return None
        return float(psr[0])

    @property
    def total_shares(self) -> float:
        return float(
            re.findall(r"ZTitad=([-,\d]*),", self._ticker_page_response.text)[
                0
            ]
        )

    @property
    def base_volume(self) -> float:
        return float(
            re.findall(r"BaseVol=([-,\d]*),", self._ticker_page_response.text)[
                0
            ]
        )

    @property
    def fiscal_year(self) -> Optional[str]:
        fiscal_year = re.findall(
            r"سال مالی :<\/td>.*?>(.*?)<",
            self._ticker_introduction_page_response.text,
            re.DOTALL,
        )
        return fiscal_year[0] if fiscal_year else None

    @property
    def flow(self) -> str:
        """
        عنوان بازار
        """
        flow_code = re.findall(
            r"Flow='(.*?)'", self._ticker_page_response.text
        )[0]
        return self._flow_name(flow_code)

    @property
    @catch(IndexError, ValueError)
    def sta_max(self) -> float:
        """
        حداکثر قیمت مجاز
        """
        return float(
            re.findall(
                r"PSGelStaMax='(.*?)'", self._ticker_page_response.text
            )[0]
        )

    @property
    @catch(IndexError, ValueError)
    def sta_min(self) -> float:
        """
        حداقل قیمت مجاز
        """
        return float(
            re.findall(
                r"PSGelStaMin='(.*?)'", self._ticker_page_response.text
            )[0]
        )

    @property
    @catch(IndexError, ValueError)
    def min_week(self) -> float:
        """
        حداقل قیمت هفته اخیر
        """
        return float(
            re.findall(r"MinWeek='(.*?)'", self._ticker_page_response.text)[0]
        )

    @property
    @catch(IndexError, ValueError)
    def max_week(self) -> float:
        """
        حداکثر قیمت هفته اخیر
        """
        return float(
            re.findall(r"MaxWeek='(.*?)'", self._ticker_page_response.text)[0]
        )

    @property
    @catch(IndexError, ValueError)
    def min_year(self) -> float:
        """
        حداقل قیمت بازه سال
        """
        return float(
            re.findall(r"MinYear='(.*?)'", self._ticker_page_response.text)[0]
        )

    @property
    @catch(IndexError, ValueError)
    def max_year(self) -> float:
        """
        حداکثر قیمت بازه سال
        """
        return float(
            re.findall(r"MaxYear='(.*?)'", self._ticker_page_response.text)[0]
        )

    @property
    def month_average_volume(self) -> str:
        """
        میانگین حجم ماه
        """
        return re.findall(
            r"QTotTran5JAvg='(.*?)'", self._ticker_page_response.text
        )[0]

    @property
    @catch(IndexError, ValueError)
    def float_shares(self) -> float:
        """
        درصد سهام شناور
        """
        return float(
            re.findall(
                r"KAjCapValCpsIdx='(.*?)'", self._ticker_page_response.text
            )[0]
        )

    @property
    def client_types(self):
        client_types = download_ticker_client_types_record(self._index)
        if client_types is None:
            raise RuntimeError("cannot download client types data try again")
        return client_types

    @property
    def trade_dates(self) -> List[datetime.date]:
        trade_dates = map(
            lambda datetime_val: datetime_val.date(),
            pd.to_datetime(self._history["date"]),
        )
        return list(trade_dates)

    @property
    def shareholders(self) -> pd.DataFrame:
        session = utils.requests_retry_session()
        page = session.get(self._shareholders_url, timeout=5)
        session.close()
        soup = bs4.BeautifulSoup(page.content, "html.parser")
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
        session=None,
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
                lambda date: not only_trade_days
                or (only_trade_days and date.date() in self.trade_dates),
                requested_dates,
            )
        )
        for date in filtered_dates:
            tasks.append(
                get_day_shareholders_history(self._index, date, session)
            )
        all_tickers_shareholders: List[
            List[ShareholderData]
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
                "date",
                "shareholder_id",
                "shareholder_shares",
                "shareholder_percentage",
                "shareholder_instrument_id",
                "shareholder_name",
                "change",
            ],
        )

    async def get_total_shares_history_async(
        self,
        from_when=datetime.timedelta(days=60),
        to_when=datetime.datetime.now(),
        only_open_days=True,
        session=None,
    ) -> pd.DataFrame:
        requested_dates = map(
            lambda datetime_val: datetime_val.date(),
            utils.datetime_range(to_when - from_when, to_when),
        )
        session_created = False
        if not session:
            session_created = True
            conn = aiohttp.TCPConnector(limit=25)
            session = aiohttp.ClientSession(connector=conn)
        tasks = []
        filtered_dates = list(
            filter(
                lambda date: not only_open_days
                or (only_open_days and date in self.trade_dates),
                requested_dates,
            )
        )
        for date in filtered_dates:
            tasks.append(
                get_day_ticker_info_history(self._index, date, session)
            )
        instrument_history: List[
            InstrumentHistoryResponse
        ] = await asyncio.gather(*tasks)
        if session_created is True:
            await session.close()

        rows = []
        for instrument_day_data, date in zip(
            instrument_history, filtered_dates
        ):
            rows.append(
                [
                    date,
                    instrument_day_data.total_shares,
                ]
            )
        return pd.DataFrame(
            data=rows,
            columns=["date", "total_shares"],
        )

    @property
    def state(self):
        return self.get_ticker_real_time_info_response().state

    @property
    def last_price(self):
        return self.get_ticker_real_time_info_response().last_price

    @property
    def adj_close(self):
        return self.get_ticker_real_time_info_response().adj_close

    @property
    def yesterday_price(self):
        return self.get_ticker_real_time_info_response().yesterday_price

    @property
    def open_price(self):
        return self.get_ticker_real_time_info_response().open_price

    @property
    def high_price(self):
        return self.get_ticker_real_time_info_response().high_price

    @property
    def low_price(self):
        return self.get_ticker_real_time_info_response().low_price

    @property
    def count(self):
        return self.get_ticker_real_time_info_response().count

    @property
    def volume(self):
        return self.get_ticker_real_time_info_response().volume

    @property
    def value(self):
        return self.get_ticker_real_time_info_response().value

    @property
    def last_date(self):
        return self.get_ticker_real_time_info_response().last_date

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
    def nav(self):
        return self.get_ticker_real_time_info_response().nav

    @property
    def market_cap(self):
        return self.get_ticker_real_time_info_response().market_cap

    @property
    def nav_date(self):
        return self.get_ticker_real_time_info_response().nav_date

    def get_ticker_real_time_info_response(self) -> RealtimeTickerInfo:
        """
        notes on usage:
        - Real time data might not be always available
        check for None values before usage
        """
        if not self.__is_active():
            raise RuntimeError(
                f"Cannot get realtime data from inactive ticker {self.symbol}"
            )
        session = utils.requests_retry_session()
        response = session.get(self._info_url, timeout=5)
        session.close()

        response_sections_list = response.text.split(";")

        if len(response_sections_list) >= 1:
            price_section = response_sections_list[0].split(",")
            try:
                state = self._instrument_state(price_section[1])
                yesterday_price = int(price_section[5])
                open_price = int(price_section[4])
                high_price = int(price_section[6])
                low_price = int(price_section[7])
                count = int(price_section[8])
                volume = int(price_section[9])
                value = int(price_section[10])
                last_date = datetime.datetime.strptime(
                    price_section[12] + price_section[13], "%Y%m%d%H%M%S"
                )
            except (ValueError, IndexError):
                state = None
                yesterday_price = None
                open_price = None
                high_price = None
                low_price = None
                count = None
                volume = None
                value = None
                last_date = None

            # in some cases last price or adj price is undefined
            try:
                last_price = int(price_section[2])
            # when instead of number value is `F`
            except (ValueError, IndexError):
                last_price = None
            try:
                adj_close = int(price_section[3])
            except (ValueError, IndexError):
                adj_close = None
            try:
                market_cap = adj_close * self.total_shares
            except ValueError:
                market_cap = None

        try:
            info_section = response_sections_list[0].split(",")
            nav = int(info_section[15])
            nav_date = str(info_section[14])
        except (ValueError, IndexError):
            nav = None
            nav_date = None

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
            datetime.datetime.now(),
            state,
            last_price,
            adj_close,
            yesterday_price,
            open_price,
            high_price,
            low_price,
            count,
            volume,
            value,
            last_date,
            best_demand_vol=best_demand_vol,
            best_demand_price=best_demand_price,
            best_supply_vol=best_supply_vol,
            best_supply_price=best_supply_price,
            buy_orders=buy_orders,
            sell_orders=sell_orders,
            individual_trade_summary=individual_trade_summary,
            corporate_trade_summary=corporate_trade_summary,
            nav=nav,
            market_cap=market_cap,
            nav_date=nav_date,
        )

    @property
    @functools.lru_cache()
    def _ticker_page_response(self):
        return utils.requests_retry_session().get(self._url, timeout=10)

    @functools.cached_property
    def _ticker_introduction_page_response(self):
        return utils.requests_retry_session().get(
            self._introduction_url, timeout=10
        )

    @functools.lru_cache()
    @retry(
        wait=wait_random(min=3, max=5),
        before_sleep=before_sleep_log(logger, logging.ERROR),
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

    def _instrument_state(self, state_code) -> str:
        states = {
            "I ": "ممنوع",
            "A ": "مجاز",
            "AG": "مجاز-مسدود",
            "AS": "مجاز-متوقف",
            "AR": "مجاز-محفوظ",
            "IG": "ممنوع-مسدود",
            "IS": "ممنوع-متوقف",
            "IR": "ممنوع-محفوظ",
        }
        return states.get(state_code, "")

    def _flow_name(self, flow_code) -> str:
        flows = {
            "0": "عمومی - مشترک بین بورس و فرابورس",
            "1": "بورس",
            "2": "فرابورس",
            "3": "آتی",
            "4": "پایه فرابورس",
            "5": "پایه فرابورس (منتشر نمی شود)",
        }
        return flows.get(flow_code, "")

    def get_trade_details(self):
        session = utils.requests_retry_session()
        page = session.get(
            tse_settings.TSE_TRADE_DETAIL_URL.format(self.index), timeout=5
        )
        session.close()
        soup = bs4.BeautifulSoup(page.content, "lxml")
        xml_rows = soup.find_all("row")
        rows = []
        for xml_row in xml_rows:
            cells = xml_row.find_all("cell")
            row = [
                datetime.time.fromisoformat(cells[1].text),
                int(cells[2].text),
                float(cells[3].text),
            ]
            rows.append(row)
        return pd.DataFrame(rows, columns=["date", "volume", "price"])

    def __is_active(self):
        """
        Check if ticker is in active state so new data comes in.
        Deactivated symbols have message
        نماد قدیمی حذف شده
        in their name.
        Returns: True if the symbol is in active state
        """
        most_recent_index = symbols_data.get_ticker_index(self.symbol)
        old_indexes = symbols_data.get_ticker_old_index(self.symbol)
        return most_recent_index not in old_indexes
