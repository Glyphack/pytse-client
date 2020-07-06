from concurrent.futures.thread import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from typing import List, Union

import pandas as pd
from requests import HTTPError

from pytse_client import config, symbols_data, tse_settings
from pytse_client.utils import requests_retry_session


def download(
        symbols: Union[List, str],
        write_to_csv: bool = False,
        base_path: str = config.DATA_BASE_PATH):
    if symbols == "all":
        symbols = symbols_data.all_symbols()
    elif isinstance(symbols, str):
        symbols = [symbols]

    df_list = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            ticker_index = symbols_data.get_ticker_index(symbol)
            if ticker_index == None:
                print("Warning, ticker index not found, I'm trying to download it...")
                ticker_index = get_symbol_id(symbol)
                print(ticker_index)
            future = executor.submit(
                download_ticker_daily_record,
                ticker_index
            )
            df: pd.DataFrame = future.result()
            if df.shape[0] == 0:
                continue
            df = df.iloc[::-1]
            df = df.rename(
                columns=FIELD_MAPPINGS
            )
            df = df.drop(columns=["<PER>", "<OPEN>", "<TICKER>"])
            df.date = pd.to_datetime(df.date, format="%Y%m%d")
            df.set_index("date", inplace=True)
            df_list[symbol] = df

            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                df.to_csv(
                    f'{base_path}/{symbol}.csv')

    if len(df_list) != len(symbols):
        print("Warning, download did not complete, re-run the code")
    return df_list


def download_ticker_daily_record(ticker_index: str):
    url = tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS.format(ticker_index)
    response = requests_retry_session().get(url, timeout=10)
    try:
        response.raise_for_status()
    except HTTPError:
        return download_ticker_daily_record(ticker_index)

    data = StringIO(response.text)
    return pd.read_csv(data)


def get_symbol_id(symbol_name: str):
    url = tse_settings.TSE_SYMBOL_ID_URL.format(symbol_name + ' ')
    response = requests_retry_session().get(url, timeout=10)
    try:
        response.raise_for_status()
    except HTTPError:
        raise Exception("Sorry, tse server did not respond")
    
    symbol_id = response.text.split(';')[0].split(',')[2]
    return symbol_id


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
