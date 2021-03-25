"""
access properties of Ticker for all symbols
"""
from collections import defaultdict

from pytse_client import Ticker, all_symbols

if __name__ == '__main__':
    symbols_errors = defaultdict(list)
    for index, symbol in enumerate(all_symbols()):
        print(f"{symbol} item {index}/{len(all_symbols())}")
        try:
            ticker = Ticker(symbol)
            ticker.history
            ticker.client_types
            ticker.title
            ticker.url
            ticker.group_name
            ticker.eps
            ticker.p_e_ratio
            ticker.group_p_e_ratio
            ticker.base_volume
            ticker.last_price
            ticker.adj_close
            ticker.shareholders
            ticker.shareholders.percentage.sum()
            ticker.total_shares
        except Exception as e:
            print(f"error {e}")
            symbols_errors[symbol].append(e)
    # if there is some error test will fail with all erros
    if symbols_errors:
        raise Exception(symbols_errors)
