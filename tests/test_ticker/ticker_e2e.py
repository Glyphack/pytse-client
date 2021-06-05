"""
access properties of Ticker for all symbols
"""
import datetime
import random
from collections import defaultdict

from pytse_client import Ticker, all_symbols

if __name__ == '__main__':
    symbols_errors = defaultdict(list)
    random_symbols = random.sample(all_symbols(), 2)
    for index, symbol in enumerate(random_symbols):
        print(f"{symbol} item {index}/{len(random_symbols)}")
        try:
            ticker = Ticker(symbol)
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
            ticker.total_shares
            ticker.get_shareholders_history(
                from_when=datetime.timedelta(days=20)
            )
            ticker.get_ticker_real_time_info_response()
        except Exception as e:
            print(f"error {e}")
            symbols_errors[symbol].append(e)
    # if there is some error test will fail with all erros
    if symbols_errors:
        raise Exception(symbols_errors)
