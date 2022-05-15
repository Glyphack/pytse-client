import os
import json


from pytse_client.ticker_statisticals import get_index_to_symbol_map

def map_index_to_symbols():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    symbols_file = os.path.join(parent_dir, "../data/symbols_name.json")
    with open(symbols_file, 'r') as json_file:
        symbol_dic = json.load(json_file)
    return get_index_to_symbol_map(symbol_dic)