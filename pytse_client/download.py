import logging
from concurrent import futures
from pathlib import Path

import jdatetime
import pandas as pd

from pytse_client import config, symbols_data, tse_settings
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.client_type import parse_client_type_history
from pytse_client.tsetmc_api.closing_price import (
    parse_closing_price_daily_list,
)
from pytse_client.tsetmc_api.index import parse_index_history
from pytse_client.utils import persian

logger = logging.getLogger(config.LOGGER_NAME)


def _handle_ticker_index(symbol):
    ticker_index = symbols_data.get_ticker_index(symbol)

    if ticker_index is None:
        market_symbol = symbols_data.get_symbol_info(symbol)
        if market_symbol is not None:
            symbols_data.append_symbol_to_file(market_symbol)
            ticker_index = market_symbol.index
    return ticker_index


def _adjust_data_frame(df, include_jdate):
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    if include_jdate:
        df["jdate"] = df.date.apply(
            lambda gregorian: jdatetime.date.fromgregorian(date=gregorian)
        )


def download(
    symbols: list | set | str,
    write_to_csv: bool = False,
    include_jdate: bool = False,
    base_path: str = config.DATA_BASE_PATH,
    adjust: bool = False,
) -> dict[str, pd.DataFrame]:
    if symbols == "all":
        symbols = symbols_data.all_symbols()
    elif isinstance(symbols, str):
        symbols = [symbols]
    # the symbols json uses Persian letters (ی, ک), accept Arabic ones
    symbols = [persian.replace_arabic(symbol.strip()) for symbol in symbols]

    df_list = {}
    future_to_symbol = {}
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            if (
                symbol.isnumeric()
                and symbols_data.get_ticker_index(symbol) is None
            ):
                ticker_indexes = [symbol]
            else:
                ticker_index = _handle_ticker_index(symbol)
                if ticker_index is None:
                    raise Exception(  # noqa: TRY002
                        f"Cannot find symbol: {symbol}"
                    )
                # deleted symbols have their index in the old list too
                ticker_indexes = list(
                    dict.fromkeys(
                        [ticker_index]
                        + symbols_data.get_ticker_old_index(symbol)
                    )
                )

            for index in ticker_indexes:
                future = executor.submit(download_ticker_daily_record, index)

                future_to_symbol[future] = symbol

        for future in futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                df: pd.DataFrame = future.result()
            except pd.errors.EmptyDataError as ex:
                logger.error(
                    f"Cannot read daily trade records for symbol: {symbol}",
                    extra={"Error": ex},
                )
                continue
            _adjust_data_frame(df, include_jdate)

            if symbol in df_list:
                df_list[symbol] = (
                    pd.concat(
                        [df_list[symbol], df], ignore_index=True, sort=False
                    )
                    .sort_values("date")
                    .reset_index(drop=True)
                )
            else:
                df_list[symbol] = df

            if adjust:
                df_list[symbol] = adjust_price(df_list[symbol])

            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                if adjust:
                    df_list[symbol].to_csv(
                        f"{base_path}/{symbol}-ت.csv", index=False
                    )
                else:
                    df_list[symbol].to_csv(
                        f"{base_path}/{symbol}.csv", index=False
                    )

    if len(df_list) != len(symbols):
        print("Warning, download did not complete, re-run the code")
    return df_list


def adjust_price(df: pd.DataFrame) -> pd.DataFrame:
    """Scale the prices before every day whose yesterday price differs
    from the close of the day before, so the history has no jumps."""
    if df.empty or not isinstance(df.index, pd.RangeIndex):
        return df

    index = df.index
    new_df = df.copy()
    step = index.step
    diff = list(new_df.index[new_df.shift(1).adjClose != new_df.yesterday])
    if len(diff) > 0:
        diff.pop(0)
    ratio = 1
    ratio_list = []
    for i in diff[::-1]:
        ratio *= (
            new_df.loc[i, "yesterday"] / new_df.shift(1).loc[i, "adjClose"]
        )
        ratio_list.insert(0, ratio)
    for i, k in enumerate(diff):
        if i == 0:
            start = index.start
        else:
            start = diff[i - 1]
        end = k - step
        new_df.loc[
            start:end,
            [
                "open",
                "high",
                "low",
                "close",
                "adjClose",
                "yesterday",
            ],
        ] = round(
            new_df.loc[
                start:end,
                [
                    "open",
                    "high",
                    "low",
                    "close",
                    "adjClose",
                    "yesterday",
                ],
            ]
            * ratio_list[i]
        )

    return new_df


def download_ticker_daily_record(ticker_index: str):
    rows = parse_closing_price_daily_list(
        client.api.call_closing_price_daily_list(ticker_index)
    )
    rows = [row for row in rows if row.trade_count > 0]
    if not rows:
        raise pd.errors.EmptyDataError(
            f"No daily trade records for instrument {ticker_index}"
        )
    df = pd.DataFrame(
        {
            "date": [f"{row.date:%Y%m%d}" for row in rows],
            "open": [float(row.first_price) for row in rows],
            "high": [float(row.high_price) for row in rows],
            "low": [float(row.low_price) for row in rows],
            "adjClose": [float(row.closing_price) for row in rows],
            "value": [row.value for row in rows],
            "volume": [row.volume for row in rows],
            "count": [row.trade_count for row in rows],
            "yesterday": [float(row.yesterday_price) for row in rows],
            "close": [float(row.last_price) for row in rows],
        }
    )
    return df.sort_values("date").reset_index(drop=True)


def download_fIndex_record(fIndex: str):
    url = tse_settings.TSE_FINANCIAL_INDEX_EXPORT_DATA_ADDRESS.format(fIndex)
    rows = parse_index_history(client.api.call_index_history(fIndex))
    if not rows:
        raise ValueError(f"""Invalid response from the url: {url}.
                         \nExpected valid financial index data.""")
    df = pd.DataFrame(
        {
            "date": [f"{row.date:%Y%m%d}" for row in rows],
            "high": [row.high for row in rows],
            "low": [row.low for row in rows],
            "close": [row.close for row in rows],
        }
    )
    return df.sort_values("date").reset_index(drop=True)


def download_financial_indexes(
    symbols: list | set | str,
    write_to_csv: bool = False,
    include_jdate: bool = False,
    base_path: str = config.FINANCIAL_INDEX_BASE_PATH,
) -> dict[str, pd.DataFrame]:
    if symbols == "all":
        symbols = symbols_data.all_financial_index()
    elif isinstance(symbols, str):
        symbols = [symbols]

    df_list = {}
    future_to_symbol = {}
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            symbol = persian.replace_persian(symbol)
            if (
                symbol.isnumeric()
                and symbols_data.get_financial_index(symbol) is None
            ):
                financial_index = symbol
            else:
                financial_index = symbols_data.get_financial_index(symbol)
            if financial_index is None:
                raise Exception(  # noqa: TRY002
                    f"Cannot find financial index: {symbol}"
                )

            future = executor.submit(download_fIndex_record, financial_index)

            future_to_symbol[future] = symbol

        for future in futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                df: pd.DataFrame = future.result()
            except pd.errors.EmptyDataError as ex:
                logger.error(
                    f"Cannot read daily trade records for symbol: {symbol}",
                    extra={"Error": ex},
                )
                continue
            _adjust_data_frame(df, include_jdate)
            df_list[symbol] = df

            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                df_list[symbol].to_csv(
                    f"{base_path}/{symbol}.csv", index=False
                )

    if len(df_list) != len(symbols):
        print("Warning, download did not complete, re-run the code")
    return df_list


def download_client_types_records(
    symbols: list | set | str,
    write_to_csv: bool = False,
    include_jdate: bool = False,
    base_path: str = config.CLIENT_TYPES_DATA_BASE_PATH,
):
    if symbols == "all":
        symbols = symbols_data.all_symbols()
    elif isinstance(symbols, str):
        symbols = [symbols]
    # the symbols json uses Persian letters (ی, ک), accept Arabic ones
    symbols = [persian.replace_arabic(symbol.strip()) for symbol in symbols]

    df_list = {}
    future_to_symbol = {}
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        for symbol in symbols:
            ticker_index = _handle_ticker_index(symbol)
            if ticker_index is None:
                raise Exception(  # noqa: TRY002
                    f"Cannot find symbol: {symbol}"
                )
            future = executor.submit(
                download_ticker_client_types_record, ticker_index
            )
            future_to_symbol[future] = symbol
        for future in futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            df: pd.DataFrame = future.result()
            if df is None:
                continue
            _adjust_data_frame(df, include_jdate)
            df_list[symbol] = df
            if write_to_csv:
                Path(base_path).mkdir(parents=True, exist_ok=True)
                df.to_csv(f"{base_path}/{symbol}.csv")

    if len(df_list) != len(symbols):
        print("""could not download client types for all the symbols make
        sure you have what you need or re-run the function""")
    return df_list


def download_ticker_client_types_record(ticker_index: str):
    data = parse_client_type_history(
        client.api.call_client_type_history(ticker_index)
    )
    if not data:
        logger.warning(
            f"""Cannot create client types data for ticker{ticker_index}
             from data: {data}""",
            extra={"ticker_index": ticker_index},
        )
        return None
    client_types_data_frame = pd.DataFrame(
        {
            "date": [f"{row.date:%Y%m%d}" for row in data],
            "individual_buy_count": [row.individual_buy_count for row in data],
            "corporate_buy_count": [row.corporate_buy_count for row in data],
            "individual_sell_count": [
                row.individual_sell_count for row in data
            ],
            "corporate_sell_count": [row.corporate_sell_count for row in data],
            "individual_buy_vol": [row.individual_buy_volume for row in data],
            "corporate_buy_vol": [row.corporate_buy_volume for row in data],
            "individual_sell_vol": [
                row.individual_sell_volume for row in data
            ],
            "corporate_sell_vol": [row.corporate_sell_volume for row in data],
            "individual_buy_value": [row.individual_buy_value for row in data],
            "corporate_buy_value": [row.corporate_buy_value for row in data],
            "individual_sell_value": [
                row.individual_sell_value for row in data
            ],
            "corporate_sell_value": [row.corporate_sell_value for row in data],
        }
    )
    for i in [
        "individual_buy_",
        "individual_sell_",
        "corporate_buy_",
        "corporate_sell_",
    ]:
        client_types_data_frame[f"{i}mean_price"] = client_types_data_frame[
            f"{i}value"
        ].astype(float) / client_types_data_frame[f"{i}vol"].astype(float)
    client_types_data_frame[
        "individual_ownership_change"
    ] = client_types_data_frame["corporate_sell_vol"].astype(
        float
    ) - client_types_data_frame[
        "corporate_buy_vol"
    ].astype(
        float
    )
    return client_types_data_frame
