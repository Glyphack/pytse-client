"""
access properties of Ticker for all symbols
"""
import datetime
import logging
import random
import traceback
from collections import defaultdict

from pytse_client import Ticker, all_symbols

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    symbols_errors = defaultdict(list)
    random_symbols = random.sample(list(all_symbols()), 50)
    for index, symbol in enumerate(random_symbols):
        logger.info(f"{symbol} item {index+1}/{len(random_symbols)}")
        try:
            ticker = Ticker(symbol)
            ticker.title
            ticker.url
            ticker.group_name
            ticker.eps
            ticker.p_e_ratio
            ticker.group_p_e_ratio
            ticker.base_volume
            ticker.state
            ticker.last_price
            ticker.adj_close
            ticker.yesterday_price
            ticker.open_price
            ticker.high_price
            ticker.low_price
            ticker.count
            ticker.volume
            ticker.value
            ticker.last_date
            ticker.flow
            ticker.sta_max
            ticker.sta_min
            ticker.min_week
            ticker.max_week
            ticker.min_year
            ticker.max_year
            ticker.month_average_volume
            ticker.float_shares
            ticker.total_shares
            ticker.shareholders
            ticker.get_shareholders_history(
                from_when=datetime.timedelta(days=20)
            )
            ticker.get_ticker_real_time_info_response()
            ticker.get_trade_details()
        except Exception as e:
            logger.exception(f"Exception testing {symbol}")
            symbols_errors[symbol].append(e)
    # if there is some error test will fail with all errors
    if symbols_errors:
        raise Exception(symbols_errors)
