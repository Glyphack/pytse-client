import datetime
import os
import logging
import pandas as pd
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Optional, Union
from pytse_client.tse_settings import TICKER_TRADE_DETAILS
from pytse_client.utils.trade_dates import get_valid_dates
from pytse_client.ticker.ticker import Ticker
from pytse_client.config import LOGGER_NAME, TRADE_DETAILS_HIST_PATH
from pytse_client.utils.logging_generator import get_logger

logger = get_logger(f"{LOGGER_NAME}_trade_details", logging.INFO)
ERROR_MSG = "{date} is not a valid trade day. Make sure it is a trade day."
TRADE_DETAILS_HEADER = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
}
mapping_api_col = {"pTran": "price", "qTitTran": "volume", "hEven": "datetime"}
valid_time_frames_mapping = {
    "30s": "30S",
    "1m": "1T",
    "5m": "5T",
    "10m": "10T",
    "15m": "15T",
    "30m": "30T",
    "1h": "1H",
}
reversed_keys = {val: key for key, val in mapping_api_col.items()}


def get_trade_details(
    symbol_name: str,
    start_date: datetime.date,
    end_date: Optional[datetime.date] = None,
    to_csv: bool = False,
    base_path: Optional[str] = None,
    timeframe: Optional[str] = None,
    aggregate: bool = False,
) -> Dict[str, pd.DataFrame]:
    if (
        timeframe is not None
        and timeframe not in valid_time_frames_mapping.keys()
    ):
        raise ValueError(
            f"The provided timeframe is not valid. It should be among {valid_time_frames_mapping.keys()}"
        )

    result = {}
    end_date = start_date if not end_date else end_date
    ticker = Ticker(symbol_name)

    all_valid_dates = get_valid_dates(ticker, start_date, end_date)

    date_df_list = []
    date_df_list.extend(get_df_valid_dates(ticker, all_valid_dates))
    for date_df in date_df_list:
        date, df = date_df
        df = common_process(df, date.strftime("%Y%m%d"))
        if df.empty:
            continue
        if timeframe:
            ohlcv_df = df.resample(valid_time_frames_mapping[timeframe]).agg(
                {"price": "ohlc", "volume": "sum"}
            )
            ohlcv_df.columns = ["open", "high", "low", "close", "volume"]
            ohlcv_df = ohlcv_df.dropna()
            result[date] = ohlcv_df
        else:
            result[date] = df

    if aggregate:
        result = {"aggregate": pd.concat(result.values())}
        result["aggregate"] = result["aggregate"].sort_values(
            ["datetime"], ascending=[True]
        )

    if to_csv:
        for date in result:
            write_to_csv(result[date], base_path, date)
    return result


def write_to_csv(
    df: pd.DataFrame,
    base_path: Union[str, None],
    date: Union[datetime.date, str],
):
    base_path = base_path or TRADE_DETAILS_HIST_PATH
    Path(base_path).mkdir(parents=True, exist_ok=True)
    extension = (
        date.strftime("%Y-%m-%d") if type(date) == datetime.date else date
    )
    file_name = f"trade_details_{extension}.csv"
    path = os.path.join(base_path, file_name)
    df.to_csv(path)


def common_process(df: pd.DataFrame, date: str):
    if len(df) == 0:
        return pd.DataFrame(columns=list(mapping_api_col.values()))
    df.rename(columns=mapping_api_col, inplace=True)
    df = df.loc[:, list(mapping_api_col.values())]
    df["datetime"] = pd.to_datetime(
        date + " " + df["datetime"].astype(str), format="%Y%m%d %H%M%S"
    )
    df = df.sort_values(["datetime"], ascending=[True])
    df.set_index("datetime", inplace=True)
    return df


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


async def get_df_valid_dates_async(ticker, valid_dates):
    conn = aiohttp.TCPConnector(limit=25)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = []
        for date in valid_dates:
            tasks.append(_get_trade_details(ticker, date, session))
        results = await asyncio.gather(*tasks)

    return results


async def _get_trade_details(ticker: Ticker, date_obj: datetime.date, session):
    index = ticker.index
    date = date_obj.strftime("%Y%m%d")
    url = TICKER_TRADE_DETAILS.format(index=index, date=date)
    max_retries = 9
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with session.get(
                url, headers=TRADE_DETAILS_HEADER, timeout=100
            ) as response:
                if response.status == 503:
                    logger.info(
                        f"Received 503 Service Unavailable on {date_obj}. Retrying..."
                    )
                    retry_count += 1
                    await asyncio.sleep(1)
                else:
                    response.raise_for_status()
                    data = await response.json()
                    logger.info(
                        f"Successfully fetched trade details on {date_obj} from tse"
                    )
                    return [date_obj, pd.json_normalize(data["tradeHistory"])]
        except (aiohttp.ClientError, asyncio.TimeoutError):
            logger.error(f"Request failed for {date_obj}. Retrying...")
            retry_count += 1
            await asyncio.sleep(1)

    raise Exception(
        f"Failed to fetch trade details for {ticker} on {date_obj} after {max_retries} retries"
    )
