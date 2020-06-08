"""
This example is about getting data for a ticker.
use this example if you want to get data for one ticker
"""

from pytse_client import Ticker, download
import pandas as pd

# to be able to see whole DataFrame columns
pd.set_option('display.max_columns', 20)

download(symbols="وبملت", write_to_csv=True)  # optional
ticker = Ticker("وبملت")
print(ticker.history)  # سابقه قیمت سهم
print(ticker.client_types)  # حقیقی حقوقی
print(ticker.title)  # نام شرکت
print(ticker.url)  # آدرس صفحه سهم
print(ticker.group_name)  # نام گروه
print(ticker.eps)  # eps
print(ticker.p_e_ratio)  # P/E
print(ticker.group_p_e_ratio)  # group P/E
print(ticker.base_volume)  # حجم مبنا
print(ticker.last_price)  # آخرین معامله
print(ticker.adj_close)  # قیمت پایانی
