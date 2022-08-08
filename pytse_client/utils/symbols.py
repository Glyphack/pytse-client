import json

from pytse_client.ticker_statisticals import get_index_to_symbol_map
from pytse_client import config


def map_index_to_symbols():
    symbols_file = f'{config.pytse_dir}/data/symbols_name.json'
    with open(symbols_file, 'r') as json_file:
        symbol_dic = json.load(json_file)
    return get_index_to_symbol_map(symbol_dic)
