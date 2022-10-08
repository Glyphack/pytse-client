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
    return df
