import dataclasses

import pandas
from pytse_client.ticker.ticker import Ticker


def ticker_real_time_data_to_csv(ticker: Ticker):
    realtime_info = ticker.get_ticker_real_time_info_response()
    data = dataclasses.asdict(realtime_info)
    _ = data.pop("sell_orders")
    _ = data.pop("buy_orders")
    [flat_dict] = pandas.json_normalize(data, sep=".").to_dict(
        orient="records"
    )

    df = pandas.DataFrame([flat_dict])
    df["symbol"] = ticker.symbol
    df["name"] = ticker.title
    df["group_name"] = ticker.group_name
    df["fiscal_year"] = ticker.fiscal_year
    df["eps"] = ticker.eps
    df["p_e_ratio"] = ticker.p_e_ratio
    df["group_p_e_ratio"] = ticker.group_p_e_ratio
    df["psr"] = ticker.psr
    df["p_s_ratio"] = ticker.p_s_ratio
    df["base_volume"] = ticker.base_volume
    df["flow"] = ticker.flow
    df["sta_max"] = ticker.sta_max
    df["sta_min"] = ticker.sta_min
    df["min_week"] = ticker.min_week
    df["max_week"] = ticker.max_week
    df["min_year"] = ticker.min_year
    df["max_year"] = ticker.max_year
    df["month_average_volume"] = ticker.month_average_volume
    return df


def export_ticker_history_as_csv(ticker: Ticker):
    trade_day_history = ticker.history
    client_types_history = ticker.client_types

    # TODO move to original function if okay
    trade_day_history["date"] = pandas.to_datetime(trade_day_history["date"])
    client_types_history["date"] = pandas.to_datetime(
        client_types_history["date"]
    )

    merged_dataframe = pandas.merge(
        trade_day_history,
        client_types_history,
        on="date",
        how="outer",
    )

    return merged_dataframe
