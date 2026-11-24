import os
from pathlib import Path

import pandas as pd

from pytse_client import config, symbols_data
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.client_type import parse_client_type_all
from pytse_client.tsetmc_api.market import parse_key_stats, parse_market_watch

KEY_STAT_NAMES = {
    1: "ave_val_trans_last_3_month",
    2: "ave_val_trans_last_12_month",
    3: "rank_val_trans_last_3_month",
    4: "rank_val_trans_last_12_month",
    5: "ave_vol_trans_last_3_month",
    6: "ave_vol_trans_last_12_month",
    7: "rank_vol_trans_last_3_month",
    8: "rank_vol_trans_last_12_month",
    9: "ave_numof_trans_last_3_month",
    10: "ave_numof_trans_last_12_month",
    11: "rank_numof_trans_last_3_month",
    12: "rank_numof_trans_last_12_month",
    13: "w_ave_price_last_day_normal",
    14: "w_ave_price_last_day_base_vol",
    15: "val_trans_last_day",
    16: "vol_trans_last_day",
    17: "numof_trans_last_day",
    18: "numof_neg_days_last_3_month",
    19: "numof_neg_days_last_12_month",
    20: "percent_neg_days_last_3_month",
    21: "percent_neg_days_last_12_month",
    22: "rank_neg_days_last_3_month",
    23: "rank_neg_days_last_12_month",
    24: "numof_notrade_days_last_3_month",
    25: "numof_notrade_days_last_12_month",
    26: "numof_pos_days_last_3_month",
    27: "numof_pos_days_last_12_month",
    28: "percent_pos_days_last_3_month",
    29: "percent_pos_days_last_12_month",
    30: "rank_pos_days_last_3_month",
    31: "rank_pos_days_last_12_month",
    32: "numof_trade_days_last_3_month",
    33: "numof_trade_days_last_12_month",
    34: "rank_trade_days_last_3_month",
    35: "rank_trade_days_last_12_month",
    36: "val_company_last_day",
    37: "rank_val_company_last_day",
    38: "numof_open_days_last_3_month",
    39: "numof_open_days_last_12_month",
    40: "percent_open_days_last_3_month",
    41: "percent_open_days_last_12_month",
    42: "rank_open_days_last_3_month",
    43: "rank_open_days_last_12_month",
    44: "numof_close_days_last_3_month",
    45: "numof_close_days_last_12_month",
    46: "percent_close_days_last_3_month",
    47: "percent_close_days_last_12_month",
    48: "rank_close_days_last_3_month",
    49: "rank_close_days_last_12_month",
    50: "ave_vol_individual_buy_last_3_month",
    51: "ave_vol_individual_buy_last_12_month",
    52: "rank_vol_individual_buy_last_3_month",
    53: "rank_vol_individual_buy_last_12_month",
    54: "ave_vol_corporation_buy_last_3_month",
    55: "ave_vol_corporation_buy_last_12_month",
    56: "rank_vol_corporation_buy_last_3_month",
    57: "rank_vol_corporation_buy_last_12_month",
    58: "ave_numof_individual_buyer_last_3_month",
    59: "ave_numof_individual_buyer_last_12_month",
    60: "rank_numof_individual_buyer_last_3_month",
    61: "rank_numof_individual_buyer_last_12_month",
    62: "ave_numof_corporation_buyer_last_3_month",
    63: "ave_numof_corporation_buyer_last_12_month",
    64: "rank_numof_corporation_buyer_last_3_month",
    65: "rank_numof_corporation_buyer_last_12_month",
    66: "ave_numof_buyer_last_3_month",
    67: "ave_numof_buyer_last_12_month",
    68: "rank_numof_buyer_last_3_month",
    69: "rank_numof_buyer_last_12_month",
    70: "ave_vol_individual_sell_last_3_month",
    71: "ave_vol_individual_sell_last_12_month",
    72: "rank_vol_individual_sell_last_3_month",
    73: "rank_vol_individual_sell_last_12_month",
    74: "ave_vol_corporation_sell_last_3_month",
    75: "ave_vol_corporation_sell_last_12_month",
    76: "rank_vol_corporation_sell_last_3_month",
    77: "rank_vol_corporation_sell_last_12_month",
    78: "ave_numof_individual_seller_last_3_month",
    79: "ave_numof_individual_seller_last_12_month",
    80: "rank_numof_individual_seller_last_3_month",
    81: "rank_numof_individual_seller_last_12_month",
    82: "ave_numof_corporation_seller_last_3_month",
    83: "ave_numof_corporation_seller_last_12_month",
    84: "rank_numof_corporation_seller_last_3_month",
    85: "rank_numof_corporation_seller_last_12_month",
    86: "ave_numof_seller_last_3_month",
    87: "ave_numof_seller_last_12_month",
    88: "rank_numof_seller_last_3_month",
    89: "rank_numof_seller_last_12_month",
}

CLIENT_TYPE_KEYS = [
    "index",
    "numof_individual_buy",
    "numof_corporate_buy",
    "vol_individual_buy",
    "vol_corporate_buy",
    "numof_individual_sell",
    "numof_corporate_sell",
    "vol_individual_sell",
    "vol_corporate_sell",
]

MARKET_WATCH_KEYS = [
    "index",
    "code",
    "symbol",
    "name",
    "last_changed",
    "open_price",
    "adj_closing_price",
    "last_price",
    "number_of_trans",
    "volume_of_trans",
    "value_of_trans",
    "min_price",
    "max_price",
    "yesterday_price",
    "EPS",
    "base_volume",
    "visit_count",
    "flow",
    "group_number",
    "max_price_allowed",
    "min_price_allowed",
    "number_of_stocks",
    "yval",
]


def _strip(text):
    return text.strip() if isinstance(text, str) else text


def get_stats(base_path=None, to_csv=False) -> pd.DataFrame:
    aggregated_key_stats = {}
    no_key_stats = dict.fromkeys(sorted(KEY_STAT_NAMES.values()))
    index_to_symbol_map = symbols_data.map_index_to_symbols()
    try:
        key_stats_rows = parse_key_stats(client.api.call_key_stats())
    except Exception as e:  # noqa: BLE001
        raise Exception(f"Failed to get key stats: {e}")  # noqa: TRY002
    key_stats_dict: dict[str, dict] = {}
    for row in key_stats_rows:
        key_name = KEY_STAT_NAMES.get(row.stat_id)
        if key_name is None:
            continue
        key_stats_dict.setdefault(row.ins_code, {})[key_name] = row.value

    try:
        client_type_rows = parse_client_type_all(
            client.api.call_client_type_all()
        )
    except Exception as e:  # noqa: BLE001
        raise Exception(f"Failed to get client types: {e}")  # noqa: TRY002
    client_types_dict = {
        row.ins_code: {
            "index": row.ins_code,
            "numof_individual_buy": row.individual_buy_count,
            "numof_corporate_buy": row.corporate_buy_count,
            "vol_individual_buy": float(row.individual_buy_volume),
            "vol_corporate_buy": float(row.corporate_buy_volume),
            "numof_individual_sell": row.individual_sell_count,
            "numof_corporate_sell": row.corporate_sell_count,
            "vol_individual_sell": float(row.individual_sell_volume),
            "vol_corporate_sell": float(row.corporate_sell_volume),
        }
        for row in client_type_rows
    }

    try:
        market_watch_rows = parse_market_watch(client.api.call_market_watch())
    except Exception as e:  # noqa: BLE001
        raise Exception(f"Failed to get market watch: {e}")  # noqa: TRY002
    market_watch_dict = {
        row.ins_code: {
            "index": row.ins_code,
            "code": _strip(row.isin),
            "symbol": _strip(row.symbol),
            "name": _strip(row.name),
            "last_changed": (
                row.time.hour * 10000 + row.time.minute * 100 + row.time.second
            ),
            "open_price": float(row.first_price),
            "adj_closing_price": float(row.closing_price),
            "last_price": float(row.last_price),
            "number_of_trans": float(row.trade_count),
            "volume_of_trans": float(row.volume),
            "value_of_trans": float(row.value),
            "min_price": float(row.low_price),
            "max_price": float(row.high_price),
            "yesterday_price": float(row.yesterday_price),
            "EPS": row.eps,
            "base_volume": float(row.base_volume),
            "visit_count": row.visit_count,
            "flow": row.flow,
            "group_number": _strip(row.sector_code),
            "max_price_allowed": float(row.max_allowed_price),
            "min_price_allowed": row.min_allowed_price,
            "number_of_stocks": float(row.total_shares),
            "yval": row.instrument_type,
        }
        for row in market_watch_rows
    }

    for idx_stat, filter_key_found in key_stats_dict.items():
        if idx_stat not in index_to_symbol_map:
            continue
        else:
            symbol = index_to_symbol_map[idx_stat]["symbol"]
            name = index_to_symbol_map[idx_stat]["name"]

        client_types = client_types_dict.get(
            idx_stat, {key: None for key in CLIENT_TYPE_KEYS}
        )

        market_watch = market_watch_dict.get(
            idx_stat, {key: None for key in MARKET_WATCH_KEYS}
        )

        aggregated_key_stats[idx_stat] = {
            **no_key_stats,
            **filter_key_found,
            **client_types,
            **market_watch,
            "symbol": symbol,
            "name": name,
        }

    aggregated_key_stats_df = pd.DataFrame.from_dict(aggregated_key_stats).T

    str_cols = {"symbol", "name"}
    numeric_cols = set(aggregated_key_stats_df.columns) - str_cols
    numeric_cols_ls = list(numeric_cols)
    aggregated_key_stats_df[numeric_cols_ls] = aggregated_key_stats_df[
        numeric_cols_ls
    ].apply(pd.to_numeric, errors="coerce")
    aggregated_key_stats_df["index"] = aggregated_key_stats_df.index
    aggregated_key_stats_df = aggregated_key_stats_df.reset_index(drop=True)

    if to_csv:
        base_path = config.STATS_BASE_PATH if base_path is None else base_path
        Path(base_path).mkdir(parents=True, exist_ok=True)
        path = os.path.join(base_path, "key_stats.csv")
        print(path)
        aggregated_key_stats_df.to_csv(path, index=False)

    return aggregated_key_stats_df
