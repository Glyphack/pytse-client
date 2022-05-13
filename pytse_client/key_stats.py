import json
from pathlib import Path
import os
import re
import pandas as pd
from typing import Dict, List, Tuple
from pytse_client import (
    utils,
    tse_settings,
    config
)

from pytse_client.ticker_statisticals.utils import get_index_to_symbol_map
from pytse_client.ticker_statisticals import (
    filter_key_value,
    filter_value_NONE
)


def _map_index_to_symbols():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    symbols_file = os.path.join(parent_dir, "data/symbols_name.json")
    with open(symbols_file, 'r') as json_file:
        symbol_dic = json.load(json_file)
    return get_index_to_symbol_map(symbol_dic)


def _get_list_of_processed_stats(raw_key_stats: str) \
        -> Tuple[List[str], List[str]]:

    # group 1 is idx, group 2 is key, group 3 is value
    proccessed_key_stats = re.sub(
        r'([0-9]+)\,([0-9]+)\,([0-9\.]+)\;',
        '@\\g<1>@\\g<2>,\\g<3>;', raw_key_stats)
    list_of_key_stats = proccessed_key_stats.split("@")[1:]
    indices = list_of_key_stats[0::2]
    values = list_of_key_stats[1::2]

    return indices, values


def get_aggregated_key_stats(base_path=None, to_csv=False)\
        -> Dict[str, Dict[str, str]]:
    aggregated_key_stats = {}
    index_to_symbol_map = _map_index_to_symbols()
    session = utils.requests_retry_session()
    try:
        response = session.get(tse_settings.KEY_STATS_URL)
    except Exception as e:
        raise Exception(f"Failed to get key stats: {e}")
    finally:
        session.close()

    raw_key_stats = response.text
    indices, values = _get_list_of_processed_stats(raw_key_stats)

    linked_stats = zip(indices, values)
    for idx_stat, val_stat in linked_stats:
        if idx_stat not in index_to_symbol_map:
            continue
        else:
            symbol = index_to_symbol_map[idx_stat]["symbol"]
            name = index_to_symbol_map[idx_stat]["name"]
        filter_key_found = {}
        segmented_val_stat = re.split(r'\;', val_stat)
        segmented_val_stat = list(
            filter(lambda x: x != '', segmented_val_stat))
        for each_segment in segmented_val_stat:
            key, val = each_segment.split(",")
            filter_key_found[filter_key_value[int(key)]] = val
        aggregated_key_stats[idx_stat] = {
            **filter_value_NONE,
            **filter_key_found,
            "symbol": symbol,
            "name": name
        }

    aggregated_key_stats_df = pd.DataFrame.from_dict(aggregated_key_stats).T

    # change type of columns to int
    str_cols = {"symbol", "name"}
    numeric_cols = set(aggregated_key_stats_df.columns) - str_cols
    numeric_cols_ls = list(numeric_cols)
    aggregated_key_stats_df[numeric_cols_ls]\
        = aggregated_key_stats_df[numeric_cols_ls].apply(
            pd.to_numeric,
            errors='coerce'
    )
    aggregated_key_stats_df["index"] = aggregated_key_stats_df.index
    aggregated_key_stats_df.reset_index(drop=True, inplace=True)

    if to_csv:
        base_path = config.KEY_STATS_BASE_PATH if\
            base_path is None else base_path
        Path(base_path).mkdir(parents=True, exist_ok=True)

        path = os.path.join(base_path, "key_stats.csv")
        aggregated_key_stats_df.to_csv(path, index=False)

    return aggregated_key_stats_df
