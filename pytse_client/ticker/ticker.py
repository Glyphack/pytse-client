import asyncio
import contextlib
import datetime
import functools
import logging
import os
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, overload

import jdatetime
import pandas as pd
import requests

from pytse_client import config, symbols_data, tse_settings
from pytse_client.download import download, download_ticker_client_types_record
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api._convert import to_optional_float
from pytse_client.tsetmc_api.best_limits import Order, parse_best_limits
from pytse_client.tsetmc_api.client_type import (
    TradeSummary,
    corporate_trade_summary,
    individual_trade_summary,
    parse_client_type,
)
from pytse_client.tsetmc_api.closing_price import (
    parse_closing_price_daily_list,
    parse_closing_price_info,
)
from pytse_client.tsetmc_api.codal import CodalPublisher, parse_codal_publisher
from pytse_client.tsetmc_api.fund import parse_etf
from pytse_client.tsetmc_api.instrument import (
    InstrumentInfo,
    parse_instrument_history,
    parse_instrument_info,
)
from pytse_client.tsetmc_api.market import parse_market_overview
from pytse_client.tsetmc_api.shareholder import (
    parse_day_shareholders,
    parse_shareholders,
)
from pytse_client.tsetmc_api.trade import (
    parse_trade_history,
    parse_trades,
    unique_trades,
)
from pytse_client.utils.logging_generator import get_logger
from pytse_client.utils.persian import replace_arabic

logger = logging.getLogger(config.LOGGER_NAME)
logger.addHandler(logging.NullHandler())
trade_details_logger = get_logger(
    f"{config.LOGGER_NAME}_trade_details", logging.INFO
)

_CANDLE_LENGTHS = {
    "30s": "30s",
    "1m": "1min",
    "5m": "5min",
    "10m": "10min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
}

_STATE_NAMES = {
    "I ": "ممنوع",
    "A ": "مجاز",
    "AG": "مجاز-مسدود",
    "AS": "مجاز-متوقف",
    "AR": "مجاز-محفوظ",
    "IG": "ممنوع-مسدود",
    "IS": "ممنوع-متوقف",
    "IR": "ممنوع-محفوظ",
}

_FLOW_NAMES = {
    "0": "عمومی - مشترک بین بورس و فرابورس",
    "1": "بورس",
    "2": "فرابورس",
    "3": "آتی",
    "4": "پایه فرابورس",
    "5": "پایه فرابورس (منتشر نمی شود)",
}


def _datetime_range(
    start: datetime.datetime, end: datetime.datetime
) -> Generator[datetime.datetime, None, None]:
    span = end - start
    for i in range(span.days + 1):
        yield start + datetime.timedelta(days=i)


def _catch(*exception_args):
    def wrapper(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except exception_args:
                return None

        return inner

    return wrapper


@dataclass
class RealtimeTickerInfo:
    date_time: datetime.datetime
    state: str | None
    last_price: float | None
    adj_close: float | None
    yesterday_price: float | None
    open_price: float | None
    high_price: float | None
    low_price: float | None
    count: int | None
    volume: int | None
    value: int | None
    last_date: datetime.datetime | None
    best_demand_vol: int | None
    best_demand_price: float | None
    best_supply_vol: int | None
    best_supply_price: float | None
    sell_orders: list[Order] | None
    buy_orders: list[Order] | None
    individual_trade_summary: TradeSummary | None
    corporate_trade_summary: TradeSummary | None
    nav: int | None
    nav_date: str | None
    market_cap: int | None


class Ticker:
    def __init__(
        self,
        symbol: str,
        index: str | None = None,
        adjust: bool = False,
    ):
        symbol = replace_arabic(symbol.strip())
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

    @functools.cached_property
    def history(self) -> pd.DataFrame:
        """Read from the ticker's csv file when it is up to date, otherwise
        downloaded and written to that file."""
        csv_path = (
            self.adjusted_daily_records_csv_path
            if self.adjust
            else self.daily_records_csv_path
        )
        if os.path.exists(csv_path):
            history = self.from_file()
            if not history.empty:
                last_saved = history["date"].iloc[-1].date()
                recent_days = parse_closing_price_daily_list(
                    client.api.call_recent_closing_price_daily_list(
                        self._index
                    )
                )
                # Days without a trade are not saved.
                missing_day = any(
                    day.date > last_saved and day.trade_count > 0
                    for day in recent_days
                )
                # A saved history older than the recent days has a gap.
                has_gap = bool(recent_days) and (
                    min(day.date for day in recent_days) > last_saved
                )
                if not missing_day and not has_gap:
                    return history
        return download(
            symbols=self.symbol,
            adjust=self.adjust,
            write_to_csv=True,
        )[self.symbol]

    def from_file(self) -> pd.DataFrame:
        if self.adjust:
            history = pd.read_csv(self.adjusted_daily_records_csv_path)
        else:
            history = pd.read_csv(self.daily_records_csv_path)
        history["date"] = pd.to_datetime(history["date"])
        return history

    @property
    def url(self):
        return self._url

    @property
    def index(self):
        return self._index

    @property
    def instrument_id(self):
        """ISIN of the instrument."""
        return self._instrument_info.isin

    @property
    def ci_sin(self):
        """ISIN of the company."""
        return self._instrument_info.company_isin

    @property
    def title(self) -> str:
        return replace_arabic(self._instrument_info.name.split("-")[0])

    @property
    def fulltitle(self) -> str:
        return replace_arabic(self._instrument_info.name)

    @property
    def group_name(self) -> str | None:
        return self._instrument_info.sector.name

    @property
    def p_e_ratio(self) -> float | None:
        adj_close = self._realtime_info(prices=True).adj_close
        eps = self.eps
        if adj_close is None or eps is None or eps == 0:
            return None
        return adj_close / eps

    @property
    def group_p_e_ratio(self) -> float | None:
        # The API sends 0 when there is no value.
        return self._instrument_info.eps.sector_pe or None

    @property
    def eps(self) -> float | None:
        return self._instrument_info.eps.estimated_eps

    @property
    def p_s_ratio(self) -> float | None:
        adj_close = self._realtime_info(prices=True).adj_close
        psr = self.psr
        if adj_close is None or psr is None or psr == 0:
            return None
        return adj_close / psr

    @property
    def psr(self) -> float | None:
        # The API sends 0 when there is no value.
        return self._instrument_info.eps.psr or None

    @property
    def total_shares(self) -> float:
        total_shares = self._instrument_info.total_shares
        return float(total_shares)  # ty: ignore[invalid-argument-type]

    @property
    def base_volume(self) -> float:
        base_volume = self._instrument_info.base_volume
        return float(base_volume)  # ty: ignore[invalid-argument-type]

    @property
    def fiscal_year(self) -> str | None:
        """End of the fiscal year as month/day, e.g. "12/29"."""
        publisher = self._codal_publisher
        if publisher is None:
            return None
        return publisher.financial_year or None

    @property
    def flow(self) -> str:
        return _FLOW_NAMES.get(str(self._instrument_info.flow), "")

    @property
    @_catch(TypeError, ValueError)
    def sta_max(self) -> float | None:
        threshold = self._instrument_info.static_threshold
        return to_optional_float(threshold.max_price) if threshold else None

    @property
    @_catch(TypeError, ValueError)
    def sta_min(self) -> float | None:
        threshold = self._instrument_info.static_threshold
        return to_optional_float(threshold.min_price) if threshold else None

    @property
    @_catch(TypeError, ValueError)
    def min_week(self) -> float | None:
        return to_optional_float(self._instrument_info.min_week)

    @property
    @_catch(TypeError, ValueError)
    def max_week(self) -> float | None:
        return to_optional_float(self._instrument_info.max_week)

    @property
    @_catch(TypeError, ValueError)
    def min_year(self) -> float | None:
        return to_optional_float(self._instrument_info.min_year)

    @property
    @_catch(TypeError, ValueError)
    def max_year(self) -> float | None:
        return to_optional_float(self._instrument_info.max_year)

    @property
    def month_average_volume(self) -> str:
        volume = self._instrument_info.month_average_volume
        return str(int(volume))  # ty: ignore[invalid-argument-type]

    @property
    @_catch(TypeError, ValueError)
    def float_shares(self) -> float | None:
        return to_optional_float(self._instrument_info.free_float)

    @property
    def client_types(self):
        client_types = download_ticker_client_types_record(self._index)
        if client_types is None:
            raise RuntimeError("cannot download client types data try again")
        return client_types

    @property
    def trade_dates(self) -> list[datetime.date]:
        trade_dates = (
            datetime_val.date()
            for datetime_val in pd.to_datetime(self.history["date"])
        )
        return list(trade_dates)

    def get_valid_dates(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> list[datetime.date]:
        """Trading days from start_date to end_date, both included."""
        trade_dates = set(self.trade_dates)
        days = (
            start_date + datetime.timedelta(n)
            for n in range((end_date - start_date).days + 1)
        )
        return [day for day in days if day in trade_dates]

    @property
    def shareholders(self) -> pd.DataFrame:
        """Columns: id, shareholder, shares, percentage, change."""
        rows = parse_shareholders(client.api.call_shareholders(self._index))
        return pd.DataFrame(
            [
                [
                    row.share_id,
                    row.name,
                    float(row.shares),
                    row.percentage,
                    float(row.change_amount),
                ]
                for row in rows
            ],
            columns=["id", "shareholder", "shares", "percentage", "change"],
        )

    def get_shareholders_history(
        self,
        from_when=datetime.timedelta(days=90),
        to_when: datetime.datetime | None = None,
        only_trade_days=True,
        session=None,
    ) -> pd.DataFrame:
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
        to_when: datetime.datetime | None = None,
        only_trade_days=True,
        session=None,
    ) -> pd.DataFrame:
        if to_when is None:
            to_when = datetime.datetime.now()
        requested_dates = _datetime_range(to_when - from_when, to_when)
        filtered_dates = list(
            filter(
                lambda date: not only_trade_days
                or (only_trade_days and date.date() in self.trade_dates),
                requested_dates,
            )
        )
        days_shareholders = await self._call_for_days(
            client.api.call_day_shareholders_async, filtered_dates, session
        )

        rows = []
        for day_shareholders, info_date in zip(
            days_shareholders, filtered_dates
        ):
            for shareholder in parse_day_shareholders(day_shareholders):
                # The API also sends rows of the next trading day.
                if (
                    shareholder.date is not None
                    and shareholder.date > info_date.date()
                ):
                    continue
                rows.append(
                    [
                        info_date,
                        shareholder.share_id,
                        float(shareholder.shares),
                        shareholder.percentage,
                        shareholder.company_isin,
                        shareholder.name,
                        shareholder.change,
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
        to_when: datetime.datetime | None = None,
        only_open_days=True,
        session=None,
    ) -> pd.DataFrame:
        if to_when is None:
            to_when = datetime.datetime.now()
        requested_dates = (
            datetime_val.date()
            for datetime_val in _datetime_range(to_when - from_when, to_when)
        )
        filtered_dates = list(
            filter(
                lambda date: not only_open_days
                or (only_open_days and date in self.trade_dates),
                requested_dates,
            )
        )
        days_instrument_history = await self._call_for_days(
            client.api.call_instrument_history_async, filtered_dates, session
        )

        rows = []
        for day_instrument_history, date in zip(
            days_instrument_history, filtered_dates
        ):
            instrument_day_data = parse_instrument_history(
                day_instrument_history
            )
            rows.append(
                [
                    date,
                    float(instrument_day_data.total_shares),
                ]
            )
        return pd.DataFrame(
            data=rows,
            columns=["date", "total_shares"],
        )

    async def _call_for_days(self, call, dates, session) -> list:
        if session is None:
            async with client.open_session(limit=25) as own_session:
                return await self._call_for_days(call, dates, own_session)
        return await asyncio.gather(
            *(call(self._index, date, session) for date in dates)
        )

    @property
    def state(self):
        return self._realtime_info(prices=True).state

    @property
    def last_price(self):
        return self._realtime_info(prices=True).last_price

    @property
    def adj_close(self):
        return self._realtime_info(prices=True).adj_close

    @property
    def yesterday_price(self):
        return self._realtime_info(prices=True).yesterday_price

    @property
    def open_price(self):
        return self._realtime_info(prices=True).open_price

    @property
    def high_price(self):
        return self._realtime_info(prices=True).high_price

    @property
    def low_price(self):
        return self._realtime_info(prices=True).low_price

    @property
    def count(self):
        return self._realtime_info(prices=True).count

    @property
    def volume(self):
        return self._realtime_info(prices=True).volume

    @property
    def value(self):
        return self._realtime_info(prices=True).value

    @property
    def last_date(self):
        return self._realtime_info(prices=True).last_date

    @property
    def best_demand_vol(self):
        return self._realtime_info(orders=True).best_demand_vol

    @property
    def best_demand_price(self):
        return self._realtime_info(orders=True).best_demand_price

    @property
    def best_supply_vol(self):
        return self._realtime_info(orders=True).best_supply_vol

    @property
    def best_supply_price(self):
        return self._realtime_info(orders=True).best_supply_price

    @property
    def nav(self):
        return self._realtime_info(nav=True).nav

    @property
    def market_cap(self):
        return self._realtime_info(prices=True).market_cap

    @property
    def nav_date(self):
        return self._realtime_info(nav=True).nav_date

    @classmethod
    def get_last_trade_day(cls) -> datetime.date:
        return parse_market_overview(
            client.api.call_market_overview()
        ).last_trade_date

    def get_ticker_real_time_info_response(self) -> RealtimeTickerInfo:
        """Fields are None when real time data is not available."""
        return self._realtime_info(
            prices=True, orders=True, client_types=True, nav=True
        )

    def _realtime_info(
        self,
        prices: bool = False,
        orders: bool = False,
        client_types: bool = False,
        nav: bool = False,
    ) -> RealtimeTickerInfo:
        if not self.__is_active():
            raise RuntimeError(
                f"Cannot get realtime data from inactive ticker {self.symbol}"
            )
        closing_price = best_limits = client_type = None
        if prices:
            closing_price = parse_closing_price_info(
                client.api.call_closing_price_info(self._index)
            )
        if orders:
            best_limits = parse_best_limits(
                client.api.call_best_limits(self._index)
            )
        if client_types:
            client_type = parse_client_type(
                client.api.call_client_type(self._index)
            )
        etf = None
        # The API answers 500 for instruments that are not funds.
        if nav and (self._instrument_info.isin or "").startswith("IRT"):
            with contextlib.suppress(requests.RequestException, ValueError):
                etf = parse_etf(client.api.call_etf(self._index))
        nav_value = nav_date = None
        if etf is not None and etf.redemption_nav is not None:
            nav_value = etf.redemption_nav
            if etf.date and etf.time:
                jalali = jdatetime.date.fromgregorian(date=etf.date)
                nav_date = (
                    f"{jalali.year}/{jalali.month}/{jalali.day} "
                    f"{etf.time:%H:%M:%S}"
                )

        price_fields: dict[str, Any] = dict.fromkeys(
            (
                "state",
                "last_price",
                "adj_close",
                "yesterday_price",
                "open_price",
                "high_price",
                "low_price",
                "count",
                "volume",
                "value",
                "last_date",
                "market_cap",
            )
        )
        if closing_price is not None:
            instrument_state = closing_price.instrument_state
            state = None
            if instrument_state and instrument_state.code:
                state = (
                    _STATE_NAMES.get(instrument_state.code)
                    or instrument_state.title
                )
            last_date = None
            if closing_price.date and closing_price.time:
                last_date = datetime.datetime.combine(
                    closing_price.date, closing_price.time
                )
            adj_close = closing_price.closing_price
            price_fields = {
                "state": state,
                "last_price": closing_price.last_price,
                "adj_close": adj_close,
                "yesterday_price": closing_price.yesterday_price,
                "open_price": closing_price.first_price,
                "high_price": closing_price.high_price,
                "low_price": closing_price.low_price,
                "count": closing_price.trade_count,
                "volume": closing_price.volume,
                "value": closing_price.value,
                "last_date": last_date,
                "market_cap": (
                    adj_close * self.total_shares
                    if adj_close is not None
                    else None
                ),
            }

        buy_orders = sell_orders = None
        if best_limits is not None:
            levels = sorted(best_limits, key=lambda row: row.level)
            buy_orders = [
                Order(
                    count=row.buy_count,
                    volume=row.buy_volume,
                    price=row.buy_price,
                )
                for row in levels
            ]
            sell_orders = [
                Order(
                    count=row.sell_count,
                    volume=row.sell_volume,
                    price=row.sell_price,
                )
                for row in levels
            ]
        return RealtimeTickerInfo(
            datetime.datetime.now(),
            **price_fields,
            best_demand_vol=buy_orders[0].volume if buy_orders else None,
            best_demand_price=buy_orders[0].price if buy_orders else None,
            best_supply_vol=sell_orders[0].volume if sell_orders else None,
            best_supply_price=sell_orders[0].price if sell_orders else None,
            buy_orders=buy_orders,
            sell_orders=sell_orders,
            individual_trade_summary=(
                individual_trade_summary(client_type) if client_types else None
            ),
            corporate_trade_summary=(
                corporate_trade_summary(client_type) if client_types else None
            ),
            nav=nav_value,
            nav_date=nav_date,
        )

    @functools.cached_property
    def _instrument_info(self) -> InstrumentInfo:
        return parse_instrument_info(
            client.api.call_instrument_info(self._index)
        )

    @functools.cached_property
    def _codal_publisher(self) -> CodalPublisher | None:
        try:
            return parse_codal_publisher(
                client.api.call_codal_publisher(self._instrument_info.symbol)
            )
        except (requests.RequestException, ValueError):
            return None

    @overload
    def get_trade_details(
        self,
        start_date: None = None,
        end_date: datetime.date | None = None,
        to_csv: bool = False,
        base_path: str | None = None,
        timeframe: str | None = None,
        aggregate: bool = False,
    ) -> pd.DataFrame: ...

    @overload
    def get_trade_details(
        self,
        start_date: datetime.date,
        end_date: datetime.date | None = None,
        to_csv: bool = False,
        base_path: str | None = None,
        timeframe: str | None = None,
        aggregate: bool = False,
    ) -> dict[datetime.date | str, pd.DataFrame]: ...

    def get_trade_details(
        self,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        to_csv: bool = False,
        base_path: str | None = None,
        timeframe: str | None = None,
        aggregate: bool = False,
    ) -> pd.DataFrame | dict[datetime.date | str, pd.DataFrame]:
        """Trades of the ticker, canceled trades left out.

        Without start_date: the trades of the current day with the columns
        date (time of the trade), volume and price. The other arguments
        are not used.

        With start_date: a dict of day -> DataFrame of the trades of every
        traded day from start_date to end_date (start_date only when
        end_date is None), indexed by datetime, with the columns price and
        volume. timeframe ("30s", "1m", "5m", "10m", "15m", "30m" or "1h")
        gives candles with the columns open, high, low, close and volume
        instead. aggregate puts all days under the key "aggregate".
        """
        if start_date is None:
            trades = sorted(
                unique_trades(
                    parse_trades(client.api.call_trades(self.index))
                ),
                key=lambda trade: trade.number,
            )
            rows = [
                [trade.time, trade.volume, float(trade.price)]
                for trade in trades
            ]
            return pd.DataFrame(rows, columns=["date", "volume", "price"])

        if timeframe is not None and timeframe not in _CANDLE_LENGTHS:
            raise ValueError(
                "The provided timeframe is not valid. It should be among "
                f"{_CANDLE_LENGTHS.keys()}"
            )
        days = self.get_valid_dates(start_date, end_date or start_date)
        days_trades = asyncio.run(
            self._call_for_days(
                client.api.call_trade_history_async, days, session=None
            )
        )

        result: dict[datetime.date | str, pd.DataFrame] = {}
        for day, day_trades in zip(days, days_trades):
            trade_details_logger.info(
                f"Successfully fetched trade details on {day} from tse"
            )
            trades = unique_trades(parse_trade_history(day_trades))
            if not trades:
                continue
            frame = pd.DataFrame(
                {
                    "price": [float(trade.price) for trade in trades],
                    "volume": [trade.volume for trade in trades],
                    "datetime": [trade.time for trade in trades],
                }
            )
            frame["datetime"] = pd.to_datetime(
                f"{day:%Y%m%d} " + frame["datetime"].astype(str),
                format="%Y%m%d %H:%M:%S",
            )
            frame = frame.sort_values(
                ["datetime"], ascending=[True]
            ).set_index("datetime")
            if timeframe:
                frame = frame.resample(_CANDLE_LENGTHS[timeframe]).agg(
                    {"price": "ohlc", "volume": "sum"}
                )
                frame.columns = ["open", "high", "low", "close", "volume"]
                frame = frame.dropna()
            result[day] = frame

        if aggregate:
            result = {
                "aggregate": pd.concat(result.values()).sort_values(
                    ["datetime"], ascending=[True]
                )
            }
        if to_csv:
            base_path = base_path or config.TRADE_DETAILS_HIST_PATH
            Path(base_path).mkdir(parents=True, exist_ok=True)
            for name, frame in result.items():
                if isinstance(name, datetime.date):
                    name = name.strftime("%Y-%m-%d")
                frame.to_csv(
                    os.path.join(base_path, f"trade_details_{name}.csv")
                )
        return result

    def __is_active(self):
        most_recent_index = symbols_data.get_ticker_index(self.symbol)
        if most_recent_index is None:
            return not any(
                self._index in symbol_info.get("old", [])
                for symbol_info in symbols_data.symbols_information().values()
            )
        old_indexes = symbols_data.get_ticker_old_index(self.symbol)
        return most_recent_index not in old_indexes


def get_trade_details(
    symbol_name: str,
    start_date: datetime.date,
    end_date: datetime.date | None = None,
    to_csv: bool = False,
    base_path: str | None = None,
    timeframe: str | None = None,
    aggregate: bool = False,
) -> dict[datetime.date | str, pd.DataFrame]:
    return Ticker(symbol_name).get_trade_details(
        start_date, end_date, to_csv, base_path, timeframe, aggregate
    )
