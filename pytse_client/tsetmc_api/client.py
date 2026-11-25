import asyncio
import datetime
import json
import logging
import ssl
from typing import Any, Protocol
from urllib.parse import quote

import aiohttp
import certifi
import requests
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random,
)
from tenacity.before_sleep import before_sleep_log
from urllib3 import Retry
from yarl import URL

from pytse_client import config, tse_settings

logger = logging.getLogger(config.LOGGER_NAME)

_REQUESTS_TIMEOUT = (5, 10)
_AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(
    total=60, sock_connect=5, sock_read=10
)
# the system certificate list of some machines rejects the TSETMC certificate
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class TsetmcApi(Protocol):
    def call_market_overview(self) -> Any: ...

    def call_market_watch(self) -> Any: ...

    def call_key_stats(self) -> Any: ...

    def call_closing_price_info(self, ins_code: str) -> Any: ...

    def call_closing_price_daily_list(self, ins_code: str) -> Any: ...

    def call_recent_closing_price_daily_list(self, ins_code: str) -> Any: ...

    def call_closing_price_daily_all_inst(self) -> Any: ...

    def call_best_limits(self, ins_code: str) -> Any: ...

    def call_best_limits_history(
        self, ins_code: str, date: datetime.date
    ) -> Any: ...

    def call_client_type(self, ins_code: str) -> Any: ...

    def call_client_type_all(self) -> Any: ...

    def call_client_type_history(self, ins_code: str) -> Any: ...

    def call_trades(self, ins_code: str) -> Any: ...

    def call_shareholders(self, ins_code: str) -> Any: ...

    def call_instrument_info(self, ins_code: str) -> Any: ...

    def call_instrument_search(self, text: str) -> Any: ...

    def call_index_history(self, ins_code: str) -> Any: ...

    def call_index_intraday(self, ins_code: str) -> Any: ...

    def call_indices(self, flow: int) -> Any: ...

    def call_index_companies(self, ins_code: str) -> Any: ...

    def call_etf(self, ins_code: str) -> Any: ...

    def call_codal_publisher(self, symbol: str) -> Any: ...

    async def call_best_limits_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any: ...

    async def call_trade_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any: ...

    async def call_day_shareholders_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any: ...

    async def call_instrument_info_async(
        self, ins_code: str, session: aiohttp.ClientSession
    ) -> Any: ...

    async def call_instrument_search_async(
        self, text: str, session: aiohttp.ClientSession
    ) -> Any: ...

    async def call_instrument_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any: ...


def _retrying_session(
    retries: int = 5,
    status_forcelist: tuple[int, ...] = (500, 502, 503, 504),
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.3,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.headers.update(tse_settings.HEADERS)
    return session


_retry_error_status = retry(
    retry=retry_if_exception_type(requests.HTTPError),
    wait=wait_random(min=1, max=4),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)


_retry_day_request = retry(
    wait=wait_random(min=3, max=5),
    stop=stop_after_attempt(10),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.ERROR),
)


def open_session(limit: int) -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(limit=limit)
    return aiohttp.ClientSession(connector=connector)


async def _get_async(
    url: str | URL,
    session: aiohttp.ClientSession,
    headers: dict[str, str] = tse_settings.HEADERS,
) -> Any:
    async with session.get(
        url, headers=headers, timeout=_AIOHTTP_TIMEOUT, ssl=_SSL_CONTEXT
    ) as response:
        response.raise_for_status()
        data = json.loads(await response.text())
    logger.debug("fetched %s", url)
    return data


def _day(date: datetime.date) -> str:
    return date.strftime(tse_settings.DATE_FORMAT)


def _instrument_search_url(text: str) -> str:
    return tse_settings.TSE_SYMBOL_ID_URL.format(quote(text.strip(), safe=""))


_ORDER_BOOK_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 "
        "Mobile Safari/537.36"
    ),
}


_TRADE_HISTORY_HEADERS = {
    **_ORDER_BOOK_HEADERS,
    "Accept-Encoding": "gzip, deflate",
}

_TRADE_HISTORY_ATTEMPTS = 9


class HttpTsetmcApi:
    def __init__(self) -> None:
        self._session = _retrying_session()
        # the API answers 500 when it has no NAV for a fund
        self._etf_session = _retrying_session(retries=2, status_forcelist=())
        self._codal_session = _retrying_session(retries=2)

    def _get(
        self,
        url: str,
        session: requests.Session | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = (session or self._session).get(
            url, headers=headers, timeout=_REQUESTS_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def call_market_overview(self) -> Any:
        return self._get(tse_settings.TSE_GET_LAST_TRADE_DAY)

    def call_market_watch(self) -> Any:
        return self._get(tse_settings.MARKET_WATCH_URL)

    def call_key_stats(self) -> Any:
        return self._get(tse_settings.KEY_STATS_URL)

    def call_closing_price_info(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_CLOSING_PRICE_INFO_URL.format(ins_code)
        )

    @_retry_error_status
    def call_closing_price_daily_list(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS.format(ins_code)
        )

    def call_recent_closing_price_daily_list(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_TICKER_RECENT_DAYS_URL.format(ins_code)
        )

    def call_closing_price_daily_all_inst(self) -> Any:
        return self._get(tse_settings.CLOSING_PRICE_DAILY_ALL_INST_URL)

    def call_best_limits(self, ins_code: str) -> Any:
        return self._get(tse_settings.TSE_BEST_LIMITS_URL.format(ins_code))

    def call_best_limits_history(
        self, ins_code: str, date: datetime.date
    ) -> Any:
        return self._get(
            tse_settings.TICKER_ORDER_BOOK.format(
                index=ins_code, date=_day(date)
            ),
            headers=_ORDER_BOOK_HEADERS,
        )

    def call_client_type(self, ins_code: str) -> Any:
        return self._get(tse_settings.TSE_CLIENT_TYPE_URL.format(ins_code))

    def call_client_type_all(self) -> Any:
        return self._get(tse_settings.CLIENT_TYPES_URL)

    @_retry_error_status
    def call_client_type_history(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_CLIENT_TYPE_DATA_URL.format(ins_code)
        )

    def call_trades(self, ins_code: str) -> Any:
        return self._get(tse_settings.TSE_TRADE_DETAIL_URL.format(ins_code))

    def call_shareholders(self, ins_code: str) -> Any:
        return self._get(tse_settings.TSE_SHAREHOLDERS_URL.format(ins_code))

    def call_instrument_info(self, ins_code: str) -> Any:
        return self._get(tse_settings.TSE_INSTRUMENT_INFO.format(ins_code))

    def call_instrument_search(self, text: str) -> Any:
        return self._get(_instrument_search_url(text))

    @_retry_error_status
    def call_index_history(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_FINANCIAL_INDEX_EXPORT_DATA_ADDRESS.format(
                ins_code
            )
        )

    def call_index_intraday(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.FINANCIAL_INDEX_EXPORT_INTRADAY_URL.format(ins_code)
        )

    def call_indices(self, flow: int) -> Any:
        return self._get(tse_settings.INDICES_LIST_URL.format(flow))

    def call_index_companies(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.FINANCIAL_INDEX_COMPANIES_URL.format(ins_code)
        )

    def call_etf(self, ins_code: str) -> Any:
        return self._get(
            tse_settings.TSE_ETF_URL.format(ins_code),
            session=self._etf_session,
        )

    def call_codal_publisher(self, symbol: str) -> Any:
        return self._get(
            tse_settings.TSE_TICKER_INTRODUCTION_URL.format(symbol),
            session=self._codal_session,
        )

    @_retry_day_request
    async def call_best_limits_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return await _get_async(
            tse_settings.TICKER_ORDER_BOOK.format(
                index=ins_code, date=_day(date)
            ),
            session,
            headers=_ORDER_BOOK_HEADERS,
        )

    async def call_trade_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        url = tse_settings.TICKER_TRADE_DETAILS.format(
            index=ins_code, date=_day(date)
        )
        for _ in range(_TRADE_HISTORY_ATTEMPTS):
            try:
                return await _get_async(
                    url,
                    session,
                    headers=_TRADE_HISTORY_HEADERS,
                )
            except (
                TimeoutError,
                aiohttp.ClientError,
                json.JSONDecodeError,
            ) as error:
                logger.warning(
                    "Request for the trades of %s on %s failed (%r). "
                    "Retrying...",
                    ins_code,
                    date,
                    error,
                )
                await asyncio.sleep(1)
        raise Exception(  # noqa: TRY002
            f"Failed to fetch trade details for {ins_code} on {date} "
            f"after {_TRADE_HISTORY_ATTEMPTS} retries"
        )

    @_retry_day_request
    async def call_day_shareholders_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return await _get_async(
            tse_settings.SYMBOL_DAY_INFO_SHAREHOLDERS_DATA.format(
                index=ins_code, date=_day(date)
            ),
            session,
        )

    async def call_instrument_info_async(
        self, ins_code: str, session: aiohttp.ClientSession
    ) -> Any:
        return await _get_async(
            tse_settings.TSE_INSTRUMENT_INFO.format(ins_code),
            session,
        )

    async def call_instrument_search_async(
        self, text: str, session: aiohttp.ClientSession
    ) -> Any:
        return await _get_async(
            URL(_instrument_search_url(text), encoded=True),
            session,
        )

    @_retry_day_request
    async def call_instrument_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        day = _day(date)
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.5",
            "Connection": "keep-alive",
            "Referer": f"https://www.tsetmc.com/History/{ins_code}/{day}",
            "Sec-GPC": "1",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 9) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.5112.102"
                "Safari/537.36"
            ),
        }
        return await _get_async(
            tse_settings.SYMBOL_DAY_INSTRUMENT_INFO_URL.format(
                index=ins_code, date=day
            ),
            session,
            headers=headers,
        )


api: TsetmcApi = HttpTsetmcApi()
