import os
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from pytse_client import config, tse_settings, utils
from pytse_client.ticker_statisticals import (
    filter_key_value,
    filter_value_NONE,
)
from pytse_client.ticker_statisticals.utils import (
    get_keys_of_client_types,
    get_keys_of_market_watch,
)
from pytse_client.utils import map_index_to_symbols


def _get_list_of_processed_stats(
    raw_key_stats: str,
) -> Tuple[List[str], List[str]]:

    # group 1 is idx, group 2 is key, group 3 is value
    proccessed_key_stats = re.sub(
        r"([0-9]+)\,([0-9]+)\,([0-9\.]+)\;",
        "@\\g<1>@\\g<2>,\\g<3>;",
        raw_key_stats,
    )
    list_of_key_stats = proccessed_key_stats.split("@")[1:]
    indices = list_of_key_stats[0::2]
    values = list_of_key_stats[1::2]

    return indices, values


def _get_dict_of_client_types(raw_client_types: str):
    """
    output: Dictionary of client types with the following keys:
        "index", "numof_individual_buy", "numof_corporate_buy",
        "vol_individual_buy", "vol_corporate_buy",
        "numof_individual_sell", "numof_corporate_sell",
        "vol_individual_sell", "vol_corporate_sell"
    """
    client_types_keys = get_keys_of_client_types()
    final_client_types = {}
    for each_client_type in raw_client_types.split(";"):
        key_val = list(zip(client_types_keys, each_client_type.split(",")))
        key_val_dict = dict(key_val)
        final_client_types[key_val_dict["index"]] = key_val_dict
    return final_client_types


def _get_dict_of_market_watch(raw_market_watch: str):
    """
    output: Dictionary of market watch with the following keys:
        "index", "code", "symbol", "name", "last_changed", "open_price",
        "adj_closing_price", "last_price", "number_of_trans",
        "volume_of_trans", "value_of_trans", "min_price", "max_year",
        "yesterday_price", "EPS", "base_volume", "NOT_VALID_KEY",
        "NOT_VALID_KEY", "group_number", "max_price_allowed",
        "min_price_allowed", "number_of_stocks", "NOT_VALID_KEY"
    """
    try:
        _market_watch = raw_market_watch.split("@")[2]
    except IndexError:
        print("Failed to get market watch stats")
        return {}

    market_watch_keys = get_keys_of_market_watch()
    final_market_watch = {}
    for each_market_watch in _market_watch.split(";"):
        key_val = list(zip(market_watch_keys, each_market_watch.split(",")))
        key_val_dict = dict(key_val)
        del key_val_dict["NOT_VALID_KEY"]
        final_market_watch[key_val_dict["index"]] = key_val_dict
    return final_market_watch


def get_stats(base_path=None, to_csv=False) -> pd.DataFrame:
    aggregated_key_stats = {}
    index_to_symbol_map = map_index_to_symbols()
    session = utils.requests_retry_session()

    raw_key_stats = _get_key_stats(session).text
    indices, values = _get_list_of_processed_stats(raw_key_stats)

    raw_client_types = _get_client_types(session).text
    client_types_dict = _get_dict_of_client_types(raw_client_types)

    raw_market_watch = _get_market_watch(session).text
    market_watch_dict = _get_dict_of_market_watch(raw_market_watch)

    linked_stats = zip(indices, values)
    for idx_stat, val_stat in linked_stats:
        if idx_stat not in index_to_symbol_map:
            continue
        else:
            symbol = index_to_symbol_map[idx_stat]["symbol"]
            name = index_to_symbol_map[idx_stat]["name"]
        filter_key_found = {}
        segmented_val_stat = re.split(r"\;", val_stat)
        segmented_val_stat = list(
            filter(lambda x: x != "", segmented_val_stat)
        )

        for each_segment in segmented_val_stat:
            key, val = each_segment.split(",")
            filter_key_found[filter_key_value[int(key)]] = val

        client_types = client_types_dict.get(
            idx_stat, {key: None for key in get_keys_of_client_types()}
        )

        market_watch = market_watch_dict.get(
            idx_stat,
            {
                key: None
                for key in get_keys_of_market_watch()
                if key != "NOT_VALID_KEY"
            },
        )

        aggregated_key_stats[idx_stat] = {
            **filter_value_NONE,
            **filter_key_found,
            **client_types,
            **market_watch,
            "symbol": symbol,
            "name": name,
        }

    aggregated_key_stats_df = pd.DataFrame.from_dict(aggregated_key_stats).T

    # change type of columns to int
    str_cols = {"symbol", "name"}
    numeric_cols = set(aggregated_key_stats_df.columns) - str_cols
    numeric_cols_ls = list(numeric_cols)
    aggregated_key_stats_df[numeric_cols_ls] = aggregated_key_stats_df[
        numeric_cols_ls
    ].apply(pd.to_numeric, errors="coerce")
    aggregated_key_stats_df["index"] = aggregated_key_stats_df.index
    aggregated_key_stats_df.reset_index(drop=True, inplace=True)

    if to_csv:
        base_path = config.STATS_BASE_PATH if base_path is None else base_path
        Path(base_path).mkdir(parents=True, exist_ok=True)
        path = os.path.join(base_path, "key_stats.csv")
        print(path)
        aggregated_key_stats_df.to_csv(path, index=False)

    return aggregated_key_stats_df


def _get_key_stats(session):
    try:
        response = session.get(tse_settings.KEY_STATS_URL)
    except Exception as e:
        raise Exception(f"Failed to get key stats: {e}")
    finally:
        session.close()
    return response


def _get_client_types(session):
    try:
        response = session.get(tse_settings.CLIENT_TYPES_URL)
    except Exception as e:
        raise Exception(f"Failed to get client types: {e}")
    finally:
        session.close()
    return response


def _get_market_watch(session):
    try:
        response = session.get(tse_settings.MARKET_WATCH_URL)
    except Exception as e:
        raise Exception(f"Failed to get market watch: {e}")
    finally:
        session.close()
    return response
