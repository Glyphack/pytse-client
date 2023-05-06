import datetime
import os
import pandas as pd
from pathlib import Path
from pytse_client.ticker import Ticker
from pytse_client.config import ORDER_BOOK_HIST_PATH

# maximum available depth in tsetmc for historical orderbook
MAX_DEPTH = 5
ERROR_MSG = "{date} is not a valid trade day. Make sure it is a trade day."
ORDERBOOK_HEADER = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
}


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

extended_columns = []
for i in range(1, MAX_DEPTH + 1):
    columns = [f"{key}_{i}" for key in base_keys]
    extended_columns.extend(columns)

reversed_keys = {val: key for key, val in api_to_orderbook_mapping.items()}


def _validate_trade_date(ticker: Ticker, date: datetime.date):
    return date in ticker.trade_dates


def validate_dates(
    ticker: Ticker,
    start_date: datetime.date,
    end_date: datetime.date,
    ignore_date_validation: bool,
):
    if not ignore_date_validation:
        if not _validate_trade_date(ticker, start_date):
            raise Exception(ERROR_MSG.format(date=start_date))
        if not _validate_trade_date(ticker, end_date):
            raise Exception(ERROR_MSG.format(date=end_date))


def get_valid_dates(
    ticker: Ticker,
    start_date: datetime.date,
    end_date: datetime.date,
):
    all_valid_dates = []
    for n in range((end_date - start_date).days + 1):
        date = start_date + datetime.timedelta(n)
        if date in ticker.trade_dates:
            all_valid_dates.append(date)
    return all_valid_dates


def write_to_csv(df: pd.DataFrame, base_path: str, date: datetime.date):
    base_path = base_path or ORDER_BOOK_HIST_PATH
    Path(base_path).mkdir(parents=True, exist_ok=True)
    file_name = f'organized_orderbook_{date.strftime("%Y-%m-%d")}.csv'
    path = os.path.join(base_path, file_name)
    df.to_csv(path)


def process_diff_orderbook(df: pd.DataFrame):
    newdf = pd.DataFrame(columns=extended_columns)
    for idx, row in df.iterrows():
        key_vals = {
            f"{key}_{int(row['depth'])}": val for key, val in row.items()
        }
        key_vals.pop(f'depth_{int(row["depth"])}')
        newdf.loc[idx, key_vals.keys()] = tuple(key_vals.values())
    # This will fill the missing values in each row with the last non-null
    # value in the same column.
    return newdf.fillna(method="ffill")


def common_process(df: pd.DataFrame, date: str):
    if len(df) == 0:
        return pd.DataFrame(columns=list(api_to_orderbook_mapping.keys()))
    df.rename(columns=reversed_keys, inplace=True)
    df = df.loc[:, list(api_to_orderbook_mapping.keys())]
    df["datetime"] = pd.to_datetime(
        date + " " + df["datetime"].astype(str), format="%Y%m%d %H%M%S"
    )
    df = df.sort_values(["datetime", "depth"], ascending=[True, True])
    df.set_index("datetime", inplace=True)
    df.drop(columns=["refID"], inplace=True)
    return df
