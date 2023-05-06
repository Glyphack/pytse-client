import asyncio
import aiohttp
import logging
import datetime
import pandas as pd
from pytse_client.config import LOGGER_NAME
from pytse_client.ticker import Ticker
from pytse_client.tse_settings import TICKER_ORDER_BOOK
from pytse_client.orderbook.common import ORDERBOOK_HEADER
from pytse_client.utils.logging_generator import get_logger

logger = get_logger(f"{LOGGER_NAME}_orderbook_async", logging.INFO)


def get_df_valid_dates(
    ticker: Ticker,
    valid_dates: list,
):
    return asyncio.run(
        get_df_valid_dates_async(
            ticker,
            valid_dates,
        ),
    )


async def get_df_valid_dates_async(
    ticker: Ticker,
    valid_dates: list,
):
    conn = aiohttp.TCPConnector(limit=25)
    session = aiohttp.ClientSession(connector=conn)
    tasks = []
    for date in valid_dates:
        tasks.append(_get_diff_orderbook(ticker, date, session))
    dates_orderbooks = await asyncio.gather(*tasks)
    await session.close()
    return dates_orderbooks


async def _get_diff_orderbook(
    ticker: Ticker, date_obj: datetime.date, session
):
    index = ticker.index
    date = date_obj.strftime("%Y%m%d")
    url = TICKER_ORDER_BOOK.format(index=index, date=date)
    async with session.get(
        url, headers=ORDERBOOK_HEADER, timeout=10
    ) as response:
        logger.info(
            f"successfully async download raw orderbook on {date} from tse"
        )
        data = await response.json()
        return [date_obj, pd.json_normalize(data["bestLimitsHistory"])]
