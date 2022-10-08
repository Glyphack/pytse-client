<div dir="rtl"  markdown="1">

# دریافت اطلاعات بازار بورس تهران

[![Test](https://github.com/Glyphack/pytse-client/actions/workflows/unit_test.yml/badge.svg)](https://github.com/Glyphack/pytse-client/actions/workflows/unit_test.yml)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Glyphack/pytse-client.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Glyphack/pytse-client/context:python)
[![Discord Chat](https://img.shields.io/discord/730808323808559106?label=discord)](https://discord.gg/ampPDKHpVv)

با استفاده از pytse client میتونید به دیتای بازار بورس تهران در پایتون دسترسی داشته باشید.
هدف حل مشکلات گرفتن اطلاعات بروز از سایت بازار بورس تهران هست.

## میخواید مشارکت کنید؟

لطفا [این صفحه](https://github.com/Glyphack/pytse-client/blob/master/CONTRIBUTING.md) رو مطالعه کنید

- [دریافت اطلاعات بازار بورس تهران](#دریافت-اطلاعات-بازار-بورس-تهران)
  - [میخواید مشارکت کنید؟](#میخواید-مشارکت-کنید)
  - [قابلیت‌ها](#قابلیتها)
  - [نصب](#نصب)
  - [نصب آخرین نسخه در حال توسعه](#نصب-آخرین-نسخه-در-حال-توسعه)
  - [نحوه استفاده](#نحوه-استفاده)
    - [دانلود سابقه سهم ها](#دانلود-سابقه-سهم-ها)
    - [دانلود سابقه شاخص های مالی](#دانلود-سابقه-شاخص-های-مالی)
    - [دانلود سابقه معاملات حقیقی و حقوقی به صورت مجزا](#دانلود-سابقه-معاملات-حقیقی-و-حقوقی-به-صورت-مجزا)
    - [ماژول Ticker](#ماژول-ticker)
        - [نکته ۱](#نکته-۱)
        - [نکته ۲](#نکته-۲)
      - [اطلاعات نماد‌های حذف شده](#اطلاعات-نمادهای-حذف-شده)
      - [اطلاعات حقیقی و حقوقی](#اطلاعات-حقیقی-و-حقوقی)
      - [سهامداران عمده](#سهامداران-عمده)
      - [تاریخچه‌ی سهام‌داران عمده](#تاریخچهی-سهامداران-عمده)
      - [تاریخچه‌ تعداد سهام](#تاریخچه-تعداد-سهام)
      - [شناور سهم](#شناور-سهم)
      - [اطلاعات لحظه‌ای سهام](#اطلاعات-لحظهای-سهام)
      - [ریز معاملات سهام](#ریز-معاملات-سهام)
    - [تمامی اطلاعات موجود برای فیلترنویسی](#تمامی-اطلاعات-موجود-برای-فیلترنویسی)
    - [گرفتن تمام اطلاعات تاریخی یا لحظه‌ای نماد به صورت CSV](#گرفتن-تمام-اطلاعات-تاریخی-یا-لحظهای-نماد-به-صورت-csv)
  - [کامیونیتی](#کامیونیتی)
  - [منابع آموزشی](#منابع-آموزشی)
  - [الهام گرفته از:](#الهام-گرفته-از)

## قابلیت‌ها

- دریافت اطلاعات تاریخی به صورت تعدیل‌شده و تعدیل نشده برای نمادها
- دریافت اطلاعات لحظه نمادها
- دریافت اطلاعات تاریخی شاخص‌های مالی
- قابلیت گرفتن اطلاعات یک سهم مانند گروه سهم و اطلاعات معاملات حقیقی و حقوقی
- دریافت اطلاعات فاندامنتال یک نماد شامل (EPS ,P/E و حجم مبنا)
- دریافت اطلاعات سهامداران عمده
- دریافت آمارهای کلیدی مربوط به فیلترنویسی برای نمادها
- دریافت ریزمعاملاتی آخرین روز معاملاتی نمادها

## نصب

<div dir="ltr">

```bash
pip install pytse-client
```

</div>

## نصب آخرین نسخه در حال توسعه

این نسخه‌ی در حال توسعه است که بر روی گیت‌هاب قرار دارد، همه‌ی قابلیت‌های گفته شده در این صفحه را دارد اما ممکن است بعضی قابلیت‌های جدید تست شده نباشند. در صورتی که نسخه‌ی بالا کاری که میخواهید را انجام نمیدهد این را نصب کنید.

<div dir="ltr">

```bash
pip install git+https://github.com/Glyphack/pytse-client.git
```

</div>

## نحوه استفاده

### دانلود سابقه سهم ها

با استفاده از این تابع می‌توان سابقه سهام رو دریافت کرد و هم اون رو ذخیره و هم توی کد استفاده کرد

<div dir="ltr">

```python
import pytse_client as tse

tickers = tse.download(symbols="all", write_to_csv=True)
print(tickers["ولملت"])  # history

# Output
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

برای دانلود سابقه یک یا چند سهم کافیست اسم اون‌ها به تابع داده بشه:

<div dir="rtl">

همچنین با گذاشتن
`write_to_csv=True`
سابقه سهم توی فایلی با نماد سهم نوشته میشه

سابقه سهم در قالب `Dataframe` است

در صورتی که می‌خواهید تاریخ شمسی به خروجی اضافه شود می‌توانید با گذاشتن
`include_jdate=True`
این امکان را فراهم کنید

برای دریافت قیمت‌های تعدیل شده از
`adjust=True`
استفاده کنید

</div>

<div dir="ltr">

```python
import pytse_client as tse

tse.download(symbols="وبملت", write_to_csv=True)
tse.download(symbols="وبملت", write_to_csv=True, include_jdate=True)
tse.download(symbols=["وبملت", "ولملت"], write_to_csv=True)
```

</div>

### دانلود سابقه شاخص های مالی

<div style="line-height:80px;">
برای دانلود سابقه شاخص های منتخب بازار که از طریق این <a href="http://www.tsetmc.com/Loader.aspx?Partree=151315&Flow=1">  لینک </a>
می توانید لیست نام آن ها را ملاحظه کنید کافی است اسم شاخص یا شاخص های مورد نظر خود را به صورت
<strong> دقیقا مشابه با لینک ارائه شده در بالا </strong>

در بخش ‍‍
`symbols`
وارد کنید.

همینطور در صورتی که علاقه داشته باشید دیتای مربوط به همه شاخص ها را دریافت کنید کافی است که در برابر کلید `symbols`
رشته
`"all"`
وارد کنید.

چند نمونه از دریافت داده‌های شاخصی را می‌توانید در پایین مشاهده کنید.

</div>
<div dir="ltr">

```python
from pytse_client.download import download_financial_indexes

download_financial_indexes(symbols="all", write_to_csv=True, base_path="hello")


download_financial_indexes(symbols=["شاخص قيمت 50 شركت", "فني مهندسي"], write_to_csv=True, include_jdate=True)
```

</div>
<div>
<i>
به این موضوع توجه داشته باشید که دیتای دریافتی تنها حاوی مقدار شاخص مورد نظر در پایان روز معاملاتی است و اطلاعاتی از `OHLCV`
شاخص در اختیار شما قرار نمی‌دهد.
</i>
</div>

### دانلود سابقه معاملات حقیقی و حقوقی به صورت مجزا

برای دانلود سابقه معاملات حقیقی و حقوقی برای تمامی نمادها می‌توان از تابع زیر استفاده کرد

<div dir="ltr">

```python
from pytse_client import download_client_types_records

if __name__ == '__main__':
    records_dict = download_client_types_records("all")
    print(records_dict["فولاد"])

# Output
date         individual_buy_count  ... individual_ownership_change

2020-09-01                36298  ...                   -691857.0
2020-08-31                58185  ...                  83789408.0
2020-08-26                  461  ...                  21647730.0
2020-08-25                 1248  ...                  14716846.0
2020-08-24                38291  ...                -238454702.0
...                         ...  ...                         ...
2008-12-02                    7  ...                    -10000.0
2008-12-01                    8  ...                         0.0
2008-11-30                   10  ...                    -12781.0
2008-11-29                  116  ...                   4596856.0
2008-11-26                   14  ...                    -20000.0

[2518 rows x 17 columns]

```

</div>

مشابه تابع قبلی می‌توان نتایج را ذخیره کرد

<div dir="ltr">

```python
from pytse_client import download_client_types_records

if __name__ == '__main__':
    # Records are saved as a .csv file with the same name of ticer's
    records = download_client_types_records("فولاد", write_to_csv=True)
```

</div>

### ماژول Ticker

این ماژول برای کار با دیتای یک سهم خاص هست و با گرفتن نماد اطلاعات موجود رو میده

برای مثال:

<div dir="ltr">

```python
import pytse_client as tse

tse.download(symbols="نوری", write_to_csv=True)  # optional
ticker = tse.Ticker("نوری")

print(ticker.history)  # سابقه قیمت سهم
print(ticker.client_types)  # حقیقی حقوقی
print(ticker.title)  # نام شرکت
پتروشيمي نوري (نوري)
print(ticker.url)  # آدرس صفحه سهم
http://tsetmc.com/Loader.aspx?ParTree=151311&i=19040514831923530
print(ticker.group_name)  # نام گروه
محصولات شيميايي
print(ticker.fiscal_year)  # سال مالی
12/29
print(ticker.eps)  # EPS
16442.0
print(ticker.p_e_ratio)  # P/E
6.705388638851721
print(ticker.group_p_e_ratio)  # group P/E
8.24
print(ticker.nav)  # NAV خالص ارزش دارایی‌ها ویژه صندوق‌ها می‌باشد
112,881
print(ticker.nav_date)  # last date of NAV تاریخ بروزرسانی خالص ارزش دارایی‌ها ویژه صندوق‌ها می‌باشد
1400/7/25 13:58:00
print(ticker.psr)  # PSR این نسبت ویژه شرکت‌های تولیدی است
71483.0238888889
print(ticker.p_s_ratio)  # P/S این نسبت ویژه شرکت‌های تولیدی است
1.5423242331125966
print(ticker.base_volume)  # حجم مبنا
918780.0
print(ticker.state)  # وضعیت نماد
مجاز
print(ticker.last_price)  # آخرین معامله
109940
print(ticker.adj_close)  # قیمت پایانی
110250
print(ticker.yesterday_price)  # قیمت دیروز
106800
print(ticker.open_price)  # قیمت اولین معامله
108200
print(ticker.high_price)  # قیمت حداکثر
111830
print(ticker.low_price)  # قیمت حداقل
108200
print(ticker.count)  # تعداد معاملات
3934
print(ticker.volume)  # حجم معاملات
2602437
print(ticker.value)  # ارزش معاملات
286919407590
print(ticker.last_date)  # تاریخ آخرین اطلاعات قیمت پایانی ناشی از تغییرات شرکتی و معاملات
2021-11-01 12:29:54
print(ticker.flow)  # عنوان بازار
بورس
print(ticker.sta_max)  # حداکثر قیمت مجاز
115760.0
print(ticker.sta_min)  # حداقل قیمت مجاز
104740.0
print(ticker.min_week)  # حداقل قیمت هفته اخیر
104500.0
print(ticker.max_week)  # حداکثر قیمت هفته اخیر
111830.0
print(ticker.min_year)  # حداقل قیمت بازه سال
48320.0
print(ticker.max_year)  # حداکثر قیمت بازه سال
197000.0
print(ticker.month_average_volume)  # میانگین حجم ماه
3865804
print(ticker.float_shares)  # درصد سهام شناور
10.0
print(ticker.best_supply_price)  # قیمت بهترین تقاضا
109960
print(ticker.best_supply_vol)  # حجم بهترین تقاضا
8296
print(ticker.best_demand_price)  # قیمت بهترین عرضه
109920
print(ticker.best_demand_vol)  # حجم بهترین عرضه
3620
print(ticker.total_shares)  # تعداد سهام
print(ticker.market_cap) # ارزش بازار شرکت
print(ticker.shareholders)  # اطلاعات سهام‌داران عمده
print(ticker.get_shareholders_history())) # تاریخچه‌ی سهام‌داران عمده
print(ticker.get_trade_details())  # ریز معاملات روز جاری
print(ticker.get_ticker_real_time_info_response()) # اطلاعات لحظه‌ای مانند قیمت و پیشنهادات خرید و فروش
```

</div>
برای دریافت قیمت‌های تعدیل شده هم میشه از این کد استفاده کرد

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker(symbol="بركت", adjust=True)
```

</div>

برای استفاده لازم نیست حتما تابع دانلود صدا زده بشه.
اگر این کد رو بدون دانلود کردن سهم استفاده کنید خودش اطلاعات سهم رو از سایت میگیره،
اما اگر قبل از اون از دانلود استفاده کرده باشید
به جای گرفتن از اینترنت اطلاعات رو از روی فایل میخونه که سریع تر هست

##### نکته ۱

طبق تجربه‌ ای که داشتم چون گاهی اوقات سایت بورس مدت زیادی طول میکشه تا اطلاعات رو بفرسته یا بعضی مواقع نمی‌فرسته بهتر هست که اول تابع دانلود رو استفاده کنید برای سهم‌هایی که لازم هست و بعد با دیتای اون‌ها کار کنید.

در صورت نیاز به اطلاعات لحظه‌ای نماد بهتر است کل [اطلاعات لحظه‌ای سهام](#اطلاعات-لحظهای-سهام) را یکجا دریافت کنید تا هم دیتای دریافتی مربوط به یک زمان باشند و هم از ارسال درخواست‌های مکرر به سایت بورس جلوگیری شود.

##### نکته ۲

بعضی از ویژگی‌ها برای همه‌ی سهم‌ها در دسترس نیست. برای مثال بعضی از سهم‌ها دارای آخرین قیمت یا پی به ای یا ای پی اس نیستند. مقدار این ویژگی‌ها در صورت نبودن برابر با `None` خواهد بود. پس باید در برنامه خود اینکه این مقادیر وجود دارند را بررسی کنید.

#### اطلاعات نماد‌های حذف شده

تعدادی از نماد‌ها توی سایت به شکل حذف شده هستند. برای گرفتن دیتای این نماد‌ها از ماژول تیکر استفاده کنید.
برای مثال جهت دسترسی به دیتای نماد حذف شده خصدرا، اندیس آن را از آدرس نماد در سایت بورس بگیرید
http://www.tsetmc.com/Loader.aspx?ParTree=151311&i=25165947991415904

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("", index="25165947991415904")
```

</div>

مقدار ‍`index` را با مقدار جلوی `i=` جایگزین میکنیم.

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

#### سهامداران عمده

سهام‌داران عمده اطلاعات داخل این [صفحه](http://tsetmc.com/Loader.aspx?Partree=15131T&c=IRO1BMLT0007) هست.
این اطلاعات رو میشه با `shareholders` گرفت که یک DataFrame هست.

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("وبملت")
print(ticker.shareholders)  # اطلاعات سهام‌داران عمده

# Output
 change   percentage       share                                 shareholder
0   دولت جمهوري اسلامي ايران                    23,114,768,760  11.160     0
1   صندوق تامين آتيه كاركنان بانك ملت           13,353,035,330  6.440      0
2   صندوق سرمايه گذاري واسطه گري مالي يكم       11,748,764,647  5.670      0
3   شركت پتروشيمي فن آوران-سهامي عام-           9,253,327,080   4.460      0
4   شركت گروه مالي ملت-سهام عام-                8,933,698,834   4.310      0
5   صندوق سرمايه گذاري.ا.بازارگرداني ملت     8,395,500,914   4.050      0
6   شركت سرمايه گذاري صباتامين-سهامي عام-       7,659,597,269   3.690      0
7   شركت تعاوني معين آتيه خواهان                4,561,801,327   2.200      0
8   شركت س اتهران س.خ-م ك م ف ع-                4,278,903,677   2.060      0
9   شركت گروه توسعه مالي مهرآيندگان-سهامي عام-  4,161,561,525   2.000      0
10  شركت س اخراسان رضوي س.خ-م ك م ف ع-          3,442,236,423   1.660      0
11  شركت س افارس س.خ-م ك م ف ع-                 2,593,956,288   1.250      0
12  شركت س اخوزستان س.خ-م ك م ف ع-              2,526,080,803   1.220      0
13  شركت شيرين عسل-سهامي خاص-                   2,496,936,881   1.200      0
14  شركت سرمايه گذاري ملي ايران-سهامي عام-      2,423,674,676   1.170      0
15  شركت س ااصفهان س.خ-م ك م ف ع-               2,274,221,331   1.090      0
```

</div>

#### تاریخچه‌ی سهام‌داران عمده

با استفاده از تابع get_shareholders_history میشه تاریخچه اطلاعات سهام‌داران عمده رو گرفت:

**رفع خطای asyncio.run() cannot be called from a running event loop**
در صورتی که این خطا رو گرفتید به این معنی هست که تابع `get_shareholders_history` در یک تابع `async` داره اجرا میشه.
برای رفع اون کافیه که تابع `get_shareholders_history_async` رو استفاده کنید مطابق مثال پایین تکه کد دوم.

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("وبملت")
ticker.get_shareholders_history(
    from_when=datetime.timedelta(days=90),  # تعداد روز‌های گذشته که مقدار پیشفرض ۹۰ روز است
    to_when=datetime.datetime.now(),  # تا چه تاریخی اطلاعات گرفته شود که پیشفرض امروز است
    only_trade_days=True,  # فقط روز‌های معاملاتی که پیشفرض بله است
)

# در صورتی که میخواهید تابع
# async
# رو استفاده کنید
await ticker.get_shareholders_history(
    from_when=datetime.timedelta(days=90),  # تعداد روز‌های گذشته که مقدار پیشفرض ۹۰ روز است
    to_when=datetime.datetime.now(),  # تا چه تاریخی اطلاعات گرفته شود که پیشفرض امروز است
    only_trade_days=True,  # فقط روز‌های معاملاتی که پیشفرض بله است
)

```

</div>
خروجی این تابع یک دیتا فریم حاوی دیتای زیر است:
<div dir="ltr">

```
,date,shareholder_id,shareholder_shares,shareholder_percentage,shareholder_instrument_id,shareholder_name,change
0,2021-08-30 17:01:23.037957,273,2910355428.0,32.19,IRO1RSAP0000,شركت ايراني توليداتومبيل-سايپا-,1
1,2021-08-30 17:01:23.037957,406,975144471.0,10.78,IRO1RSAP0000,شركت سايپا,1
2,2021-08-30 17:01:23.037957,50264,454000000.0,5.02,IRO1RSAP0000,شركت ايراني توليداتومبيل سايپا-سهامي عام-,1
3,2021-08-30 17:01:23.037957,42636,409843922.0,4.53,IRO1RSAP0000,شركت سرمايه گذاري وتوسعه صنعتي نيوان ابتكارس.ع,1
4,2021-08-30 17:01:23.037957,46966,116002189.0,1.28,IRO1RSAP0000,BFMصندوق.س.ا.بازارگرداني سهم آشنايكم,1
5,2021-08-31 17:01:23.037957,273,2910355428.0,32.19,IRO1RSAP0000,شركت ايراني توليداتومبيل-سايپا-,1
6,2021-08-31 17:01:23.037957,406,975144471.0,10.78,IRO1RSAP0000,شركت سايپا,1
7,2021-08-31 17:01:23.037957,50264,454000000.0,5.02,IRO1RSAP0000,شركت ايراني توليداتومبيل سايپا-سهامي عام-,1
8,2021-08-31 17:01:23.037957,42636,409843922.0,4.53,IRO1RSAP0000,شركت سرمايه گذاري وتوسعه صنعتي نيوان ابتكارس.ع,1
9,2021-08-31 17:01:23.037957,46966,116002189.0,1.28,IRO1RSAP0000,BFMصندوق.س.ا.بازارگرداني سهم آشنايكم,1
10,2021-09-01 17:01:23.037957,273,2910355428.0,32.19,IRO1RSAP0000,شركت ايراني توليداتومبيل-سايپا-,1
11,2021-09-01 17:01:23.037957,406,975144471.0,10.78,IRO1RSAP0000,شركت سايپا,1
12,2021-09-01 17:01:23.037957,50264,454000000.0,5.02,IRO1RSAP0000,شركت ايراني توليداتومبيل سايپا-سهامي عام-,1
13,2021-09-01 17:01:23.037957,42636,409843922.0,4.53,IRO1RSAP0000,شركت سرمايه گذاري وتوسعه صنعتي نيوان ابتكارس.ع,1
14,2021-09-01 17:01:23.037957,46966,116002189.0,1.28,IRO1RSAP0000,BFMصندوق.س.ا.بازارگرداني سهم آشنايكم,1

```

</div>

<div id="qa" />
گرفتن این دیتا کار زمان بری هست (با توجه به تعداد روزی که لازم دارید) و سریع کردن کار با کد به راحتی امکان پذیر نیست. سعی نکنید با همزمان اجرا کردن این تابع برای سهم‌های مختلف روند رو سریع‌تر کنید چون سایت ip رو بلاک میکنه.
اگر موقع اجرای کد پیغام زیر را به تعداد زیاد گرفتید (مثلا هر ثانیه این پیغام اومد) یعنی آیپی شما توسط سایت بورس بلاک شده و چند دقیقه صبر کنید و دوباره ادامه بدید.
<div dir="ltr">

```
Retrying pytse_client.ticker.ticker.Ticker._get_ticker_daily_info_page_response in 1.3127419515957892 seconds as it raised ClientResponseError: 500, message='Internal Server Error', url=URL('http://cdn.tsetmc.com/Loader.aspx?ParTree=15131P&i=56574323121551263&d=20210220').
```

</div>

#### تاریخچه‌ تعداد سهام
برای گرفتن این اطلاعات از تابع `get_total_shares_history_async`
استفاده کنید.

خروجی این تابع یک دیتافریم با دو ستون 
date, total_shares
است.

توجه داشته باشید که اجرا کردن این تابع به علت `async` بودن متفاوت از بقیه دستورات است.
برای اطلاعات بیشتر درباره‌ی این نوع توابع [این ویدیو](https://www.youtube.com/watch?v=EHHxGAfcZWw) را ببینید

در صورتی که در کد خود تابع async ندارید:

<div dir="ltr">

```python
import asyncio
import pytse_client as tse
ticker = tse.Ticker("وبملت")

result = asyncio.run(ticker.get_total_shares_history_async(
    from_when=datetime.timedelta(days=90),  # تعداد روز‌های گذشته که مقدار پیشفرض ۶۰ روز است
    to_when=datetime.datetime.now(),  # تا چه تاریخی اطلاعات گرفته شود که پیشفرض امروز است
    only_trade_days=True,  # فقط روز‌های معاملاتی که پیشفرض بله است
)
```

</div>
اگر در برنامه‌ی خود کد async دارید:
این تابع را به این شکل اجرا کنید

<div dir="ltr">

```python
import pytse_client as tse
ticker = tse.Ticker("وبملت")

result = await ticker.get_total_shares_history_async(
    from_when=datetime.timedelta(days=90),  # تعداد روز‌های گذشته که مقدار پیشفرض ۶۰ روز است
    to_when=datetime.datetime.now(),  # تا چه تاریخی اطلاعات گرفته شود که پیشفرض امروز است
    only_trade_days=True,  # فقط روز‌های معاملاتی که پیشفرض بله است
)
```

</div>

#### شناور سهم

برای مثال میشه با استفاده از دیتای سهامداران عمده، شناوری سهم رو حساب کرد:

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("وبملت")

print(ticker.shareholders.percentage.sum())  # جمع درصد سهام‌داران عمده
53.63

print(100 - ticker.shareholders.percentage.sum())  # درصد سهام شناور
46.37
```

</div>

#### اطلاعات لحظه‌ای سهام

از طریق تابع `get_ticker_real_time_info_response` میشه اطلاعات لحظه‌ای سهام رو گرفت.
در صورتی که هنگام گرفتن اطلاعات لحظه‌ای وضعیت سهام در حالت ممنوع متوقف باشد یا نماد قدیمی باشد اطلاعات لحظه‌ای موجود نیست و با ارور مواجه خواهید شد که باید به درستی هندل شود.

برای گرفتن اطلاعات لحظه‌ای به صورت فایل csv می‌توانید از تابع زیر استفاده کنید:

<div dir="ltr">

```python
df = ticker_real_time_data_to_csv(ticker)
df.to_csv("test.csv") # برای ذخیره کردن در فایل
```
</div>
نمونه‌ی استفاده

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("وبملت")
try:
    real_time_data = ticker.get_ticker_real_time_info_response()
except RuntimeError: # هندل کردن ارور در صورت وجود نداشتن اطلاعات لحظه‌ای
    print("cannot get realtime data")

print(real_time_data.buy_orders) # پیشنهادات خرید
print(real_time_data.sell_orders) # پیشنهادات فروش
print(real_time_data.best_supply_price)  # قیمت بهترین تقاضا
print(real_time_data.best_supply_vol)  # حجم بهترین تقاضا
print(real_time_data.best_demand_price)  # قیمت بهترین عرضه
print(real_time_data.best_demand_vol)  # حجم بهترین عرضه
print(real_time_data.state)  # وضعیت نماد
print(real_time_data.last_price)  # قیمت آخرین معامله
print(real_time_data.adj_close)  # قیمت پایانی
print(real_time_data.yesterday_price)  # قیمت دیروز
print(real_time_data.open_price)  # قیمت اولین معامله
print(real_time_data.high_price)  # قیمت حداکثر
print(real_time_data.low_price)  # قیمت حداقل
print(real_time_data.count)  # تعداد معاملات
print(real_time_data.volume)  # حجم معاملات
print(real_time_data.value)  # ارزش معاملات
print(real_time_data.last_date)  # آخرین اطلاعات قیمت ناشی از تغییرات شرکتی و معاملات

# پیشنهادات فروش
for sell_order in real_time_data.sell_orders:
    print(sell_order.volume, sell_order.count, sell_order.price)

# پیشنهادات خرید
for buy_order in real_time_data.buy_orders:
    print(buy_order.volume, buy_order.count, buy_order.price)

# اطلاعات خرید و فروش حقیقی و حقوقی
print(real_time_data.individual_trade_summary.buy_count)
print(real_time_data.individual_trade_summary.buy_vol)
print(real_time_data.individual_trade_summary.sell_count)
print(real_time_data.individual_trade_summary.sell_vol)
print(real_time_data.corporate_trade_summary.buy_count)
print(real_time_data.corporate_trade_summary.buy_vol)
print(real_time_data.corporate_trade_summary.sell_count)
print(real_time_data.corporate_trade_summary.sell_vol)
```

</div>

#### ریز معاملات سهام

از طریق تابع `get_trade_details` می‌توان ریز معاملات آخرین روز معاملاتی سهام را گرفت:

<div dir="ltr">

```python
import pytse_client as tse

ticker = tse.Ticker("نوری")
trade_details = ticker.get_trade_details()
print(trade_details)

# Output
          date  volume     price
0     09:00:20   10000  111900.0
1     09:00:20    4480  111900.0
2     09:00:20    3171  111900.0
3     09:00:20    1647  111900.0
4     09:00:20    1101  111900.0
       ...     ...       ...
6478  12:29:57    1163  116000.0
6479  12:29:57    2159  116000.0
6480  12:29:57     795  116000.0
6481  12:29:58     257  116000.0
6482  12:29:59     601  116000.0
```

</div>


### تمامی اطلاعات موجود برای فیلترنویسی

در بخش دیده‌بان بازار امکان فیلترنویسی به زبان جاوااسکریپت وجود دارد. یکی از اطلاعات مهمی که معامله‌گران معمولا با اسفاده از آن فیلترنویسی می‌کنند آمارهای کلیدی سهام است که شامل تمامی موارد ذکر شده در 
[آمارهای کلیدی](./pytse_client/ticker_statisticals/README.md)
است.

همچنین تمامی اطلاعات ارائه شده در مورد اطلاعات حقیقی حقوقی های سهام هم که در ادامه آمده است میتوانید دریافت کنید.

```
"numof_individual_buy", "numof_corporate_buy",
"vol_individual_buy", "vol_corporate_buy",
"numof_individual_sell", "numof_corporate_sell",
"vol_individual_sell", "vol_corporate_sell"

```
نام کلیدهای ارائه شده در بالا به صورت کامل تر پایین آمده است:

```
        [
            '5054819322815158', # id
            '406', # num_of_individual_buyers (daily)
            '5', # num_of_corporate_buyers (daily)
            '4979247', # volume_of_individual_buyers (daily)
            '528270', # volume_of_corporate_buyers (daily)
            '554', # num_of_individual_sellers (daily)
            '2', # num_of_corporate_sellers (daily)
            '5302517', # volume_of_individual_sellers (daily)
            '205000' # volume_of_corporate_sellers (daily)
        ]
    
```


همچنین همه اطلاعات ارائه شده توسط دیده بان بازار را هم می توانید برای تمامی سهام دریافت کنید. در ادامه مشاهده میکنید.

```
"index", "code", "symbol", "name", "last_changed", "open_price",
"adj_closing_price", "last_price", "number_of_trans",
"volume_of_trans", "value_of_trans", "min_price", "max_year",
"yesterday_price", "EPS", "base_volume", "group_number", "max_price_allowed", "min_price_allowed", "number_of_stocks"
```


در واقع از دیده بان بازار دیتاهای زیر قابل دریافت بود که به عنوان نمونه قرار میدهم ولی برخی از دیتاها برای توسعه دهندگان پکیج قابل فهم نبود(آنهایی که با `?` در زیر مشخص شده اند) که در صورت علاقه مندی میتوانید با اطلاع رسانی کاربرد آن ها به ما در توسعه پکیج کمک کنید.

```
        [
            '71957984642204570', # id
            'IRO7APTP0001', # code
            'شپترو', # symbol
            'پتروشيمي آبادان', # name
            '122931', # last changed (time 12:29:31)
            '2470', # open price
            '2438', # adj_closing price
            '2436', # last price
            '861', # number of trans (daily)
            '29225934', # volume of trans (daily)
            '71250969784', # value of trans (daily)
            '2436', # min price (daily)
            '2500', # max price (daily)
            '2511', # yesterday price
            '-43', # EPS
            '4000000', # base voulume
            '3423', # ?
            '4', # ?
            '44', # group number
            '2586.00', # max allowed (daily)
            '2436.00', # min allowed (daily)
            '10000000000', # number of stocks
            '309' # ?
        ]
```


ممکن است گاهی برخی از این اطلاعات موجود نباشند که باید در برنامه از وجود آن برای سهام مورد نظر اطمینان پیدا کنید.
البته باید دقت داشت اگر برخی از این اطلاعات گاهی برای برخی نمادها موجود نبود در خود دیده‌بان بازار هم موجود نبوده است.

در حال حاضر امکان دریافت کل اطلاعات بروز شده و لحظه‌ای مربوط به فیلترنویسی با استفاده از تکه کد زیر موجود است.


<div dir="ltr">

```python
from pytse_client import get_stats

key_stats = get_stats(base_path="hello", to_csv=True)

# Output

   ave_numof_buyer_last_12_month  ave_numof_buyer_last_3_month  ave_numof_corporation_buyer_last_12_month  ...  symbol                          name            index
0                          610.0                         345.0                                        1.0  ...   وسپهر  سرمایه گذاری مالی سپهرصادرات  114312662654155
1                          816.0                         381.0                                        1.0  ...    شصدف                صنعتی دوده فام  204092872752957
2                           92.0                          76.0                                        0.0  ...     فسا                  پتروشیمی فسا  318005355896147
3                          298.0                         246.0                                        2.0  ...   فرآور          فرآوریموادمعدنیایران  408934423224097
4                          407.0                         332.0                                        1.0  ...   سبزوا              سیمان لار سبزوار  611986653700161

```

همانطور که در مثال(ناقص به دلیل کمبود جا) بالا می بینید خروجی این دستور یک pandas dataframe است که **آمارهای کلیدی به علاوه اطلاعات حقیقی و حقوقی و همچنین اطلاعات دیده بان بازار** تمامی نمادهایی که در پکیج معتبر هستند و دیده‌بان در اختیار کاربران قرار می‌دهد را در خود دارد.

به صورت همزمان اطلاعات در ‍‍`hello/key_stats.csv` ذخیره می‌شود.
در صورتی که نمی‌خواهید خروجی csv ساخته شود کافی است که `to_csv=False` قرار دهید.
همینطور در صورت خالی گذاشتن `base_path` به جای آن `stats_data/stats.csv` استفاده می‌شود.


</div>

### گرفتن تمام اطلاعات تاریخی یا لحظه‌ای نماد به صورت CSV

برای استفاده راحت‌تر از اطلاعات لحظه‌ای یا تاریخی و یا درست کردن فایل برای نرم افزارهای دیگه توابعی وجود داره که تمام اطلاعات نماد رو در یک فایل برمیگردونه.

اطلاعات تاریخی برگشته شامل اطلاعات خرید و فروش حقیقی و حقوقی و تاریخچه سهم هست که در هر سطر با ذکر تاریخ وجود دارند
اطلاعات لحظه‌ای تنها یک سطر هست و شامل اطلاعات تابلو هست.

توجه کنید این اطلاعات چیزی بیشتر از توابع موجود در پکیج ندارند و صرفا برای راحتی کار کاربران توسعه داده شده‌اند.
<div dir="ltr">

```python
ticker = Ticker("وبملت")
historical_data = export_ticker_history_as_csv(ticker)
real_time_data = ticker_real_time_data_to_csv(ticker)

# برای نوشتن این اطلاعات به شکل فایل csv

historical_data.to_csv("history.csv")
real_time_data.to_csv("realtime.csv")

```

</div>



## کامیونیتی

اگر درباره پکیج یا استفاده از اون سوالی دارید میتونید توی سرور دیسکورد بپرسید.

https://discord.gg/ampPDKHpVv

<div id="education" />

## منابع آموزشی
لیست زیر پست و یا دوره‌های آموزشی است که به شما کمک می‌کند استفاده از پایتون و پکیج pytse را بیاموزید

- https://virgool.io/@sh.hooshyari/%D8%AF%D8%B1%DB%8C%D8%A7%D9%81%D8%AA-%D8%A7%D8%B7%D9%84%D8%A7%D8%B9%D8%A7%D8%AA-%D8%A8%D9%88%D8%B1%D8%B3-%D8%AA%D9%87%D8%B1%D8%A7%D9%86-%D8%A8%D8%A7-%D9%BE%D8%A7%DB%8C%D8%AA%D9%88%D9%86-mgaev4iytip6
- https://github.com/sfmqrb/Eco-Finance-Course

<div id="credits" />

## الهام گرفته از:

- [tehran_stocks](https://github.com/ghodsizadeh/tehran-stocks)
- [yfinance](https://github.com/ranaroussi/yfinance)

</div>
