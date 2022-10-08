"""
This example is about getting data for a ticker.
use this example if you want to get data for one ticker
"""

import pandas as pd
from pytse_client import Ticker, download

# to be able to see whole DataFrame columns
pd.set_option("display.max_columns", 20)

download(symbols="نوری", write_to_csv=True)  # optional
ticker = Ticker("نوری")
print(ticker.history)  # سابقه قیمت سهم
print(ticker.client_types)  # حقیقی حقوقی
print(ticker.title)  # نام شرکت
print(ticker.url)  # آدرس صفحه سهم
print(ticker.group_name)  # نام گروه
print(ticker.fiscal_year)  # سال مالی
print(ticker.eps)  # eps
print(ticker.p_e_ratio)  # P/E
print(ticker.group_p_e_ratio)  # group P/E
print(ticker.nav)  # NAV خالص ارزش دارایی‌ها ویژه صندوق‌ها می‌باشد
print(ticker.nav_date)  # last date of NAV ویژه صندوق‌ها می‌باشد
print(ticker.psr)  # PSR این نسبت ویژه شرکت‌های تولیدی است
print(ticker.p_s_ratio)  # P/S این نسبت ویژه شرکت‌های تولیدی است
print(ticker.base_volume)  # حجم مبنا
print(ticker.state)  # وضعیت نماد
print(ticker.last_price)  # قیمت آخرین معامله
print(ticker.adj_close)  # قیمت پایانی
print(ticker.market_cap)  # ارزش بازار شرکت
print(ticker.yesterday_price)  # قیمت دیروز
print(ticker.open_price)  # قیمت اولین معامله
print(ticker.high_price)  # قیمت حداکثر
print(ticker.low_price)  # قیمت حداقل
print(ticker.count)  # تعداد معاملات
print(ticker.volume)  # حجم معاملات
print(ticker.value)  # ارزش معاملات
print(ticker.last_date)  # آخرین اطلاعات قیمت ناشی از تغییرات شرکتی و معاملات
print(ticker.flow)  # عنوان بازار
print(ticker.sta_max)  # حداکثر قیمت مجاز
print(ticker.sta_min)  # حداقل قیمت مجاز
print(ticker.min_week)  # حداقل قیمت هفته اخیر
print(ticker.max_week)  # حداکثر قیمت هفته اخیر
print(ticker.min_year)  # حداقل قیمت بازه سال
print(ticker.max_year)  # حداکثر قیمت بازه سال
print(ticker.month_average_volume)  # میانگین حجم ماه
print(ticker.float_shares)  # درصد سهام شناور
print(ticker.total_shares)  # تعداد سهام
print(ticker.shareholders)  # اطلاعات سهام داران عمده
print(ticker.shareholders.percentage.sum())  # جمع سهام داران
print(ticker.get_trade_details())  # ریز معاملات روز جاری

real_time_data = ticker.get_ticker_real_time_info_response()
print(real_time_data.individual_trade_summary.buy_count)
print(real_time_data.individual_trade_summary.buy_vol)
print(real_time_data.individual_trade_summary.sell_count)
print(real_time_data.individual_trade_summary.sell_vol)
print(real_time_data.corporate_trade_summary.buy_count)
print(real_time_data.corporate_trade_summary.buy_vol)
print(real_time_data.corporate_trade_summary.sell_count)
print(real_time_data.corporate_trade_summary.sell_vol)
