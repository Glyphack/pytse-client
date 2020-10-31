from concurrent.futures.thread import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from typing import List, Union

import pandas as pd
from requests import HTTPError
import jdatetime

from pytse_client import config, symbols_data, tse_settings
from pytse_client.utils import requests_retry_session
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL


def download(
        symbols: Union[List, str],
        write_to_csv: bool = False,
        include_jdate: bool = False,
        base_path: str = config.DATA_BASE_PATH):
    if symbols == "all":
        symbols = symbols_data.all_symbols()
    elif isinstance(symbols, str):
        symbols = [symbols]

    df_list = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            ticker_index = symbols_data.get_ticker_index(symbol)
            _handle_ticker_index(symbol, ticker_index)
            future = executor.submit(
                download_ticker_daily_record,
                ticker_index
            )
            df: pd.DataFrame = future.result()
            df = df.iloc[::-1]
            df = df.rename(
                columns=FIELD_MAPPINGS
            )
            df = df.drop(columns=["<PER>", "<OPEN>", "<TICKER>"])
            _adjust_data_frame(df, include_jdate)
            df_list[symbol] = df
            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                df.to_csv(
                    f'{base_path}/{symbol}.csv')

    if len(df_list) != len(symbols):
        print("Warning, download did not complete, re-run the code")
    return df_list


def _adjust_data_frame(df, include_jdate):
    df.date = pd.to_datetime(df.date, format="%Y%m%d")
    if include_jdate:
        df['jdate'] = ""
        df.jdate = df.date.apply(
            lambda gregorian:
            jdatetime.date.fromgregorian(date=gregorian))
    df.set_index("date", inplace=True)


def download_ticker_daily_record(ticker_index: str):
    url = tse_settings.TSE_TICKER_EXPORT_DATA_ADDRESS.format(ticker_index)
    response = requests_retry_session().get(url, timeout=10)
    try:
        response.raise_for_status()
    except HTTPError:
        return download_ticker_daily_record(ticker_index)

    data = StringIO(response.text)
    return pd.read_csv(data)


def download_client_types_records(
        symbols: Union[List, str],
        write_to_csv: bool = False,
        include_jdate: bool = False,
        base_path: str = config.CLIENT_TYPES_DATA_BASE_PATH
):
    if symbols == "all":
        symbols = symbols_data.all_symbols()
    elif isinstance(symbols, str):
        symbols = [symbols]

    df_list = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            ticker_index = symbols_data.get_ticker_index(symbol)
            _handle_ticker_index(symbol, ticker_index)
            future = executor.submit(
                download_ticker_client_types_record,
                ticker_index
            )
            df: pd.DataFrame = future.result()
            _adjust_data_frame(df, include_jdate)
            df_list[symbol] = df
            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                df.to_csv(f'{base_path}/{symbol}.csv')
    return df_list


def _handle_ticker_index(symbol, ticker_index):
    if ticker_index is None:
        ticker_index = get_symbol_id(symbol)
        if ticker_index is None:
            raise Exception("Can not found ticker name")
        else:
            symbols_data.append_symbol_to_file(ticker_index, symbol)


def download_ticker_client_types_record(ticker_index: str):
    data = _extract_ticker_client_types_data(ticker_index)
    client_types_data_frame = pd.DataFrame(data, columns=[
        "date",
        "individual_buy_count", "corporate_buy_count",
        "individual_sell_count", "corporate_sell_count",
        "individual_buy_vol", "corporate_buy_vol",
        "individual_sell_vol", "corporate_sell_vol",
        "individual_buy_value", "corporate_buy_value",
        "individual_sell_value", "corporate_sell_value"
    ])
    for i in [
        "individual_buy_", "individual_sell_",
        "corporate_buy_", "corporate_sell_"
    ]:
        client_types_data_frame[f"{i}mean_price"] = (
                client_types_data_frame[f"{i}value"].astype(float) /
                client_types_data_frame[f"{i}vol"].astype(float)
        )
    client_types_data_frame["individual_ownership_change"] = (
            client_types_data_frame["corporate_sell_vol"].astype(float) -
            client_types_data_frame["corporate_buy_vol"].astype(float)
    )
    return client_types_data_frame


def _extract_ticker_client_types_data(ticker_index: str) -> List:
    url = TSE_CLIENT_TYPE_DATA_URL.format(ticker_index)
    response = requests_retry_session().get(url, timeout=5)
    data = response.text.split(";")
    data = [row.split(",") for row in data]
    return data


def to_arabic(string: str):
    return string.replace('ک', 'ك').replace('ی', 'ي').strip()


def get_symbol_id(symbol_name: str):
    url = tse_settings.TSE_SYMBOL_ID_URL.format(symbol_name.strip())
    response = requests_retry_session().get(url, timeout=10)
    try:
        response.raise_for_status()
    except HTTPError:
        raise Exception("Sorry, tse server did not respond")

    symbol_full_info = response.text.split(';')[0].split(',')
    if (to_arabic(symbol_name) == symbol_full_info[0].strip()):
        return symbol_full_info[2]  # symbol id
    return None


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
