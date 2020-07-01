<div dir="rtl">

# (pyTSEClient (python tse client

&rlm;
با استفاده از این پکیج میتونید به دیتای بازار بورس تهران در پایتون دسترسی داشته باشید.
&rlm;
&rlm;
هدف حل مشکلات گرفتن اطلاعات بروز از سایت بازار بورس تهران هست.
&rlm;

## محتویات

- [قابلیت ها](#قابلیت-ها)
- [نصب](#نصب)
- [نحوه استفاده](#نحوه-استفاده)
  - [دانلود سابقه سهم ها](#دانلود-سابقه-سهم-ها)
  - [ماژول Ticker](#ماژول-Ticker)
  - [اطلاعات حقیقی و حقوقی](#اطلاعات-حقیقی-و-حقوقی)
  - [پکیج های مورد نیاز](#required-packages)
- [الهام گرفته از](#credits)

## قابلیت ها

- دریافت اطلاعات روز های معاملاتی هر سهم و قابلیت ذخیره سازی
- قابلیت گرفتن اطلاعات یک سهام مانند گروه سهام و اطلاعات معاملات حقیقی و حقوقی
- دریافت اطلاعات فاندامنتال یک نماد شامل(eps, p/e ,حجم مبنا)

## نصب

<div dir="ltr">

```bash
pip install pytse-client
```

</div>

## نحوه استفاده

### دانلود سابقه سهم ها

با استفاده از این تابع میتوان سابقه سهام هارو دریافت کرد و هم اون رو ذخیره و هم توی کد استفاده کرد

<div dir="ltr">

```python
import pytse_client as tse
tickers = tse.download(symbols="all", write_to_csv=True)
tickers["ولملت"] # history

            date     open     high  ...     volume  count    close
0     2009-02-18   1050.0   1050.0  ...  330851245    800   1050.0
1     2009-02-21   1051.0   1076.0  ...  335334212   6457   1057.0
2     2009-02-22   1065.0   1074.0  ...    8435464    603   1055.0
3     2009-02-23   1066.0   1067.0  ...    8570222    937   1060.0
4     2009-02-25   1061.0   1064.0  ...    7434309    616   1060.0
...          ...      ...      ...  ...        ...    ...      ...
2323  2020-04-14   9322.0   9551.0  ...  105551315  13536   9400.0
2324  2020-04-15   9410.0   9815.0  ...  201457026  11322   9815.0
2325  2020-04-18  10283.0  10283.0  ...  142377245   8929  10283.0
2326  2020-04-19  10797.0  10797.0  ...  292985635  22208  10380.0
2327  2020-04-20  10600.0  11268.0  ...  295590437  16313  11268.0
```

</div>

سابقه سهم توی فایلی با اسم سهم نوشته میشه `write_to_csv=True` همچنین با گذاشتن

است `Dataframe` سابقه سهم در قالب

برای دانلود سابقه یک یا چند سهم کافی هست اسم اون ها به تابع داده بشه:

<div dir="ltr">

```python
import pytse_client as tse
tse.download(symbols="وبملت", write_to_csv=True)
tse.download(symbols=["وبملت", "ولملت"], write_to_csv=True)
```

</div>

### ماژول Ticker

&rlm;
این ماژول برای کار با دیتای یک سهم خاص هست و با گرفتن نماد اطلاعات موجود رو میده

برای مثال:
&rlm;

<div dir="ltr">

```python
import pytse_client as tse

tse.download(symbols="وبملت", write_to_csv=True)  # optional
ticker = tse.Ticker("وبملت")
print(ticker.history)  # سابقه قیمت سهم
print(ticker.client_types)  # حقیقی حقوقی
print(ticker.title)  # نام شرکت
بانك ملت (وبملت)
print(ticker.url)  # آدرس صفحه سهم
http://tsetmc.com/Loader.aspx?ParTree=151311&i=778253364357513
print(ticker.group_name)  # نام گروه
بانكها و موسسات اعتباري
print(ticker.eps)  # eps
2725.0
print(ticker.p_e_ratio)  # P/E
6.1478899082568805
print(ticker.group_p_e_ratio)  # group P/E
18.0
print(ticker.base_volume)  # حجم مبنا
7322431.0
print(ticker.last_price)  # آخرین معامله
17316
print(ticker.adj_close)  # قیمت پایانی
16753
```

</div>

برای استفاده لازم نیست حتما تابع دانلود صدا زده بشه.
اگر این کد رو بدون دانلود کردن سهم استفاده کنید خودش اطلاعات سهم رو از سایت میگیره،
اما اگر قبل از اون از دانلود استفاده کرده باشید
به جای گرفتن از اینترنت اطلاعات رو از روی فایل میخونه که سریع تر هست

##### نکته

&rlm;
طبق تجربه‌ ای که داشتم چون گاهی اوقات سایت بورس مدت زیادی طول میکشه تا اطلاعات رو بفرسته یا بعضی مواقع نمیفرسته بهتر هست که اول تابع دانلود رو استفاده کنید برای سهم هایی که لازم هست و بعد با دیتای اون ها کار کنید.
&rlm;

#### اطلاعات حقیقی و حقوقی

اطلاعات خرید و فروش حقیقی و حقوقی سهام رو میشه از طریق `ticker.client_types` گرفت این اطلاعات یه DataFrame شامل اطلاعات موجود در تب حقیقی حقوقی(تب بنفشی که در این [صفحه](http://www.tsetmc.com/Loader.aspx?ParTree=151311&i=778253364357513) هست) سهم هست:

<div dir="ltr">

```
date : تاریخ
individual_buy_count : تعداد معاملات خرید حقیقی
corporate_buy_count : تعداد معلاملات خرید حقوقی
individual_sell_count : تعداد معاملات فروش حقیقی
corporate_sell_count : تعداد معلاملات فروش حقوقی
individual_buy_vol : حجم خرید حقیقی
corporate_buy_vol : حجم خرید حقوقی
individual_sell_vol : حجم فروش حقیقی
corporate_sell_value : حجم فروش حقوقی
individual_buy_mean_price : قیمت میانگین خرید حقیقی
individual_sell_mean_price : قیمت میانگین فروش حقیقی
corporate_buy_mean_price : قیمت میانگین خرید حقوقی
corporate_sell_mean_price : قیمت میانگین فروش حقوقی
individual_ownership_change : تغییر مالکیت حقوقی به حقیقی
```

</div>

<div id="required-packages" />

#### &rlm; پکیج های مورد نیاز: &rlm;

- [Pandas](https://github.com/pydata/pandas)
- [Requests](http://docs.python-requests.org/en/master/)

<div id="credits" />

#### &rlm; الهام گرفته از: &rlm;

- [tehran_stocks](https://github.com/ghodsizadeh/tehran-stocks)
- [yfinance](https://github.com/ranaroussi/yfinance)

</div>
