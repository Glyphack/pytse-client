import os
from pathlib import Path
import json
import pandas as pd
import datetime
import logging

from pytse_client.config import ORDER_BOOK_HIST_PATH
from pytse_client.tse_settings import TICKER_ORDER_BOOK
from pytse_client.utils.request_session import requests_retry_session
from pytse_client.symbols_data import get_ticker_index
from pytse_client.ticker import Ticker

MAX_DEPTH = 5
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
error_msg = "{date} is not a valid date object. Make sure it was a trade day."

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
}


keys = {
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

secondly_keys = [
    "bid",
    "ask",
    "vol_bid",
    "vol_ask",
    "num_bid",
    "num_ask",
]


reversed_keys = {val: key for key, val in keys.items()}
valid_keys = [key for key in keys]


def get_orderbook(
    symbol_name,
    start_date: datetime.date,
    end_date=None,
    to_csv=False,
    base_path=None,
    ignore_date_validation=False,
    diff_orderbook=False,  # faster to process but only stores the difference
):
    ticker = Ticker(symbol_name)
    end_date = start_date if not end_date else end_date
    if not ignore_date_validation:
        if not _validate_trade_date(ticker, start_date):
            raise Exception(error_msg.format(date=start_date))
        if not _validate_trade_date(ticker, end_date):
            raise Exception(error_msg.format(date=end_date))
    all_valid_dates = []
    for n in range((end_date - start_date).days + 1):
        date = start_date + datetime.timedelta(n)
        if date in ticker.trade_dates:
            all_valid_dates.append(date)
    result = {}
    for valid_date in all_valid_dates:
        try:
            df = _get_orderbook(
                symbol_name, valid_date, to_csv, base_path, diff_orderbook
            )
        except Exception as e:
            logging.error(e)
            logging.info("returning the results until now ...")
            return result

        result[valid_date.strftime("%Y-%m-%d")] = df
        logging.info(f"successfully construct orderbook on {valid_date}")
    return result


def _validate_trade_date(ticker: Ticker, date: datetime.date):
    return date in ticker.trade_dates


def _get_orderbook(
    symbol_name,
    date: datetime.date,
    to_csv=False,
    base_path=None,
    diff_orderbook=False,
):
    df = _get_diff_orderbook(symbol_name, date)
    if not diff_orderbook:
        df.drop(columns=["refID"], inplace=True)
        new_columns = []
        for i in range(1, MAX_DEPTH + 1):
            columns = [f"{key}_{i}" for key in secondly_keys]
            new_columns.extend(columns)
        newdf = pd.DataFrame(columns=new_columns)
        for idx, row in df.iterrows():
            keys = {f"{key}_{int(row['depth'])}": val for key, val in row.items()}
            for key, val in keys.items():
                if "depth" in key:
                    continue
                newdf.at[idx, key] = val

        for idx, row in newdf.iterrows():
            if idx == 0:
                last_idx = idx
                continue
            for key, val in row.items():
                if pd.isna(newdf.at[idx, key]):
                    newdf.at[idx, key] = newdf.at[last_idx, key]
            last_idx = idx
    else:
        newdf = df

    if to_csv:
        base_path = base_path or ORDER_BOOK_HIST_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)
        file_name = f'organized_orderbook_{date.strftime("%Y-%m-%d")}.csv'
        path = os.path.join(base_path, file_name)
        newdf.to_csv(path, index=False)

    return newdf


def _get_diff_orderbook(symbol_name, date_obj: datetime.date):
    index = get_ticker_index(symbol_name)
    date = date_obj.strftime("%Y%m%d")
    session = requests_retry_session(retries=10, backoff_factor=0.2)
    url = TICKER_ORDER_BOOK.format(index=index, date=date)

    response = session.get(url, headers=headers, timeout=10)
    logging.info(f"successfully download raw orderbook on {date_obj} from tse")
    data = json.loads(response.content)
    session.close()

    df = pd.json_normalize(data["bestLimitsHistory"])
    if len(df) == 0:
        return pd.DataFrame(columns=valid_keys)
    df.rename(columns=reversed_keys, inplace=True)
    df = df.loc[:, valid_keys]
    df["datetime"] = pd.to_datetime(
        date + " " + df["datetime"].astype(str), format="%Y%m%d %H%M%S"
    )
    df = df.sort_values(["datetime", "depth"], ascending=[True, True])
    df.set_index("datetime", inplace=True)

    return df
