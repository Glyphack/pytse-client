import json
from pathlib import Path
import os
import re
from typing import Dict, List, Tuple
from pytse_client import (
    utils,
    tse_settings,
    config
)
from pytse_client.data.utils import get_index_to_symbol_map

from .filter_data import filter_key_value


def _map_index_to_symbols():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    symbols_file = os.path.join(parent_dir, "symbols_name.json")
    with open(symbols_file, 'r') as json_file:
        symbol_dic = json.load(json_file)
    return get_index_to_symbol_map(symbol_dic)


def _request_key_stats() -> str:
    session = utils.requests_retry_session()
    try:
        response = session.get(tse_settings.KEY_STATS_URL)
    except Exception as e:
        print('--- Could not retrieve key stats ---')
        print(e)
        return ""
    finally:
        session.close()

    try:
        raw_key_stats = response.text
    except AttributeError as e:
        print(f"--- Not a valid response --- \n\n{response}\n\n")
        print(e)
        return ""

    return raw_key_stats


def _get_list_of_processed_stats(raw_key_stats: str) \
        -> Tuple[List[str], List[str]]:

    # group 1 is idx, group 2 is key, group 3 is value
    proccessed_key_stats = re.sub(
        r'([0-9]+)\,([0-9]+)\,([0-9\.]+)\;',
        '@\\g<1>@\\g<2>,\\g<3>;', raw_key_stats)
    list_of_key_stats = proccessed_key_stats.split("@")[1:]
    idxs = list_of_key_stats[0::2]
    values = list_of_key_stats[1::2]

    return idxs, values


def get_aggregated_key_stats(to_json=False)\
        -> Dict[str, Dict[str, str]]:
    aggregated_key_stats = {}
    index_to_symbol_map = _map_index_to_symbols()
    raw_key_stats = _request_key_stats()
    idxs, values = _get_list_of_processed_stats(raw_key_stats)

    linked_stats = zip(idxs, values)
    for idx_stat, val_stat in linked_stats:
        if idx_stat not in index_to_symbol_map:
            continue
        else:
            symbol = index_to_symbol_map[idx_stat]["symbol"]
            name = index_to_symbol_map[idx_stat]["name"]
        tmp_key_stat = {}
        segmented_val_stat = re.split(r'\;', val_stat)
        segmented_val_stat = list(
            filter(lambda x: x != '', segmented_val_stat))
        for each_segment in segmented_val_stat:
            key, val = each_segment.split(",")
            tmp_key_stat[filter_key_value[int(key)]] = val
        aggregated_key_stats[idx_stat] = {
            **tmp_key_stat, "symbol": symbol, "name": name}

    if to_json:
        base_path = config.KEY_STATS_BASE_PATH
        Path(base_path).mkdir(parents=True, exist_ok=True)
        path = os.path.join(base_path, "key_stats.json")
        with open(path, 'w', encoding="utf8") as json_file:
            json.dump(aggregated_key_stats, json_file,
                      indent=4, ensure_ascii=False)
    return aggregated_key_stats
