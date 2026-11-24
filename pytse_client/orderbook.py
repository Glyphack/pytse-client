import asyncio
import datetime
import logging
import multiprocessing
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pytse_client.config import LOGGER_NAME, ORDER_BOOK_HIST_PATH
from pytse_client.ticker.ticker import Ticker
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.best_limits import (
    BestLimitHistory,
    parse_best_limits_history,
)
from pytse_client.utils.logging_generator import get_logger

logger = get_logger(f"{LOGGER_NAME}_orderbook", logging.INFO)

MAX_DEPTH = 5
ERROR_MSG = "{date} is not a valid trade day. Make sure it is a trade day."


api_to_orderbook_mapping = {
    "datetime": "hEven",
    "refID": "refID",
    "depth": "number",
    "bid": "pMeDem",
    "ask": "pMeOf",
    "vol_bid": "qTitMeDem",
    "vol_ask": "qTitMeOf",
    "num_bid": "zOrdMeDem",
    "num_ask": "zOrdMeOf",
}

base_keys = [
    "bid",
    "ask",
    "vol_bid",
    "vol_ask",
    "num_bid",
    "num_ask",
]

extended_columns = [
    f"{key}_{depth}" for depth in range(1, MAX_DEPTH + 1) for key in base_keys
]


def best_limits_history_frame(rows: list[BestLimitHistory]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": [row.time for row in rows],
            "refID": [row.ref_id for row in rows],
            "depth": [row.level for row in rows],
            "bid": [float(row.buy_price) for row in rows],
            "ask": [float(row.sell_price) for row in rows],
            "vol_bid": [row.buy_volume for row in rows],
            "vol_ask": [row.sell_volume for row in rows],
            "num_bid": [row.buy_count for row in rows],
            "num_ask": [row.sell_count for row in rows],
        },
        columns=list(api_to_orderbook_mapping.keys()),
    )


def get_orderbook(
    symbol_name: str,
    start_date: datetime.date,
    end_date: datetime.date | None = None,
    to_csv: bool = False,
    base_path: str | None = None,
    ignore_date_validation: bool = False,
    diff_orderbook: bool = False,  # only the changes, faster
    async_requests: bool = True,
) -> dict[str, pd.DataFrame]:
    end_date = start_date if not end_date else end_date
    ticker = Ticker(symbol_name)

    if not ignore_date_validation:
        trade_dates = ticker.trade_dates
        for date in (start_date, end_date):
            if date not in trade_dates:
                raise Exception(ERROR_MSG.format(date=date))  # noqa: TRY002
    days = ticker.get_valid_dates(start_date, end_date)

    if async_requests:
        days_changes = asyncio.run(_fetch_days_async(ticker.index, days))
    else:
        days_changes = []
        for day in days:
            data = client.api.call_best_limits_history(ticker.index, day)
            logger.info(
                f"successfully download raw orderbook on {day} from tse"
            )
            days_changes.append(
                best_limits_history_frame(parse_best_limits_history(data))
            )

    jobs = [
        _DayOrderBook(changes, day, to_csv, base_path, diff_orderbook)
        for day, changes in zip(days, days_changes)
    ]
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        frames = pool.map(_build_day_orderbook, jobs)
    return {
        day.strftime("%Y-%m-%d"): frame for day, frame in zip(days, frames)
    }


@dataclass
class _DayOrderBook:
    changes: pd.DataFrame
    date: datetime.date
    to_csv: bool
    base_path: str | None
    diff_orderbook: bool


# Module level so the process pool can pickle it.
def _build_day_orderbook(job: _DayOrderBook) -> pd.DataFrame:
    columns = list(api_to_orderbook_mapping.keys())
    if len(job.changes) == 0:
        newdf = pd.DataFrame(columns=columns)
    else:
        newdf = job.changes.loc[:, columns]
        newdf["datetime"] = pd.to_datetime(
            f"{job.date:%Y%m%d} " + newdf["datetime"].astype(str),
            format="%Y%m%d %H:%M:%S",
        )
        newdf = newdf.sort_values(
            ["datetime", "depth"], ascending=[True, True]
        )
        newdf.set_index("datetime", inplace=True)
        newdf.drop(columns=["refID"], inplace=True)
    if not job.diff_orderbook:
        full = pd.DataFrame(columns=extended_columns)
        for idx, row in newdf.iterrows():
            depth = int(row["depth"])
            key_vals = {f"{key}_{depth}": val for key, val in row.items()}
            key_vals.pop(f"depth_{depth}")
            full.loc[idx, key_vals.keys()] = tuple(key_vals.values())
        newdf = full.ffill()
    if job.to_csv:
        base_path = job.base_path or ORDER_BOOK_HIST_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)
        file_name = f"organized_orderbook_{job.date:%Y-%m-%d}.csv"
        newdf.to_csv(os.path.join(base_path, file_name))
    logger.info(f"successfully construct orderbook on {job.date}")
    return newdf


async def _fetch_day_async(
    ins_code: str, day: datetime.date, session
) -> pd.DataFrame:
    data = await client.api.call_best_limits_history_async(
        ins_code, day, session
    )
    logger.info(
        f"successfully async download raw orderbook on {day:%Y%m%d} from tse"
    )
    return best_limits_history_frame(parse_best_limits_history(data))


async def _fetch_days_async(
    ins_code: str, days: list[datetime.date]
) -> list[pd.DataFrame]:
    async with client.open_session(limit=25) as session:
        return await asyncio.gather(
            *(_fetch_day_async(ins_code, day, session) for day in days)
        )
