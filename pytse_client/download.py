from concurrent.futures.thread import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from typing import List, Union

import pandas as pd
from requests import HTTPError

from pytse_client import config
from pytse_client.data import symbols_info
from pytse_client.utils import requests_retry_session


def download(
        tickers: Union[List, str],
        write_to_csv: bool = False,
        path: str = None):
    if tickers == "all":
        tickers = symbols_info.symbols_index
    elif isinstance(tickers, list):
        tickers = list(set(tickers))
    elif isinstance(tickers, str):
        tickers = [tickers]

    df_list = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            future = executor.submit(
                download_ticker_daily_record,
                ticker
            )
            df: pd.DataFrame = future.result()
            df = df.iloc[::-1]
            df = df.rename(
                columns=FIELD_MAPPINGS
            )
            df = df.drop(columns=["<PER>", "<OPEN>", "<TICKER>"])
            df.Date = pd.to_datetime(df.Date, format="%Y%m%d")
            df.set_index("Date")
            if write_to_csv:
                Path(path).mkdir(parents=True, exist_ok=True)
                df.to_csv(
                    f'{path}/{ticker}.csv')

            df_list[ticker] = df
    if not len(df_list) == len(tickers):
        print("Warning, download did not complete, re-run the code")
    return df_list


def download_ticker_daily_record(ticker_index: str):
    url = config.TSE_TICKER_ADDRESS.format(ticker_index)
    try:
        response = requests_retry_session().get(url, timeout=10)
        response.raise_for_status()
    except HTTPError:
        download_ticker_daily_record(ticker_index)

    data = StringIO(response.text)
    df = pd.read_csv(data)
    return df


FIELD_MAPPINGS = {
    "<DTYYYYMMDD>": "date",
    "<FIRST>": "open",
    "<HIGH>": "high",
    "<LOW>": "low",
    "<LAST>": "close",
    "<VOL>": "volume",
    "<CLOSE>": "adjClose",
    "<OPENINT>": "count",
    "<VALUE>": "value"
}
