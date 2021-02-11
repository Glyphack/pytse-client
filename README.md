<div dir="rtl">

# دریافت اطلاعات بازار بورس تهران

![Python application](https://github.com/Glyphack/pytse-client/workflows/Python%20application/badge.svg)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Glyphack/pytse-client.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Glyphack/pytse-client/context:python)
[![Discord Chat](https://img.shields.io/discord/730808323808559106?label=discord)](https://discord.gg/ampPDKHpVv)

با استفاده از pytse client میتونید به دیتای بازار بورس تهران در پایتون دسترسی داشته باشید.
هدف حل مشکلات گرفتن اطلاعات بروز از سایت بازار بورس تهران هست.

## محتویات

- [قابلیت ها](#قابلیت-ها)
- [نصب](#نصب)
- [نحوه استفاده](#نحوه-استفاده)
  - [دانلود سابقه سهم‌ها](#دانلود-سابقه-سهم‌ها)
  - [دانلود سابقه معاملات حقیقی و حقوقی](#دانلود-سابقه-معاملات-حقیقی-و-حقوقی-به-صورت-مجزا)
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

### دانلود سابقه سهم‌ها

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

برای دانلود سابقه یک یا چند سهم کافی هست اسم اون ها به تابع داده بشه:

<div dir="rtl">

همچنین با گذاشتن
`write_to_csv=True`
سابقه سهم توی فایلی با اسم سهم نوشته میشه

سابقه سهم در قالب `Dataframe` است

درصورتی که می خواهید تاریخ شمسی به خروجی اضافه شود می توانید با گذاشتن
`include_jdate=True`
این امکان را فراهم کنید

</div>

<div dir="ltr">

```python
import pytse_client as tse
tse.download(symbols="وبملت", write_to_csv=True)
tse.download(symbols="وبملت", write_to_csv=True, include_jdate=True)
tse.download(symbols=["وبملت", "ولملت"], write_to_csv=True)
```

</div>

### دانلود سابقه معاملات حقیقی و حقوقی به صورت مجزا

برای دانلود سابقه معاملات حقیقی و حقوقی برای تمامی نمادها میتوان از تابع زیر استفاده کرد

<div dir="ltr">

```python
from pytse_client import download_client_types_records

if __name__ == '__main__':

  records_dict = download_client_types_records("all")
  print(records_dict["فولاد"])
  #Output
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

مشابه تابع قبلی میتوان نتایج را ذخیره کرد

<div dir="ltr">

```python
from pytse_client import download_client_types_records
if __name__ == '__main__':

  #Records are saved as a .csv file with the same name of ticer's
  records = download_client_types_records("فولاد", write_to_csv=True)
```

</div>

### ماژول Ticker

این ماژول برای کار با دیتای یک سهم خاص هست و با گرفتن نماد اطلاعات موجود رو میده

برای مثال:

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
print(ticker.best_supply_price)  # قیمت بهترین تقاضا
26700
print(ticker.best_supply_vol)  # حجم بهترین تقاضا
357062
print(ticker.best_demand_price)  # قیمت بهترین عرضه
26700
print(ticker.best_demand_vol)  # حجم بهترین عرضه
576608
print(ticker.shareholders)  # اطلاعات سهام داران عمده
```

</div>

برای استفاده لازم نیست حتما تابع دانلود صدا زده بشه.
اگر این کد رو بدون دانلود کردن سهم استفاده کنید خودش اطلاعات سهم رو از سایت میگیره،
اما اگر قبل از اون از دانلود استفاده کرده باشید
به جای گرفتن از اینترنت اطلاعات رو از روی فایل میخونه که سریع تر هست

##### ۱نکته

طبق تجربه‌ ای که داشتم چون گاهی اوقات سایت بورس مدت زیادی طول میکشه تا اطلاعات رو بفرسته یا بعضی مواقع نمیفرسته بهتر هست که اول تابع دانلود رو استفاده کنید برای سهم‌هایی که لازم هست و بعد با دیتای اون ها کار کنید.

##### نکته۲

بعضی از ویژگی‌ها برای همه‌ی سهم ها در دسترس نیست. برای مثال بعضی از سهم ها دارای آخرین قیمت یا پی به ای یا ای پی اس نیستند. مقدار این ویژگی‌ها در صورت نبودن برابر با `None` خواهد بود. پس باید در برنامه خود اینکه این مقادیر وجود دارند را بررسی کنید.

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

سهام داران عمده اطلاعات داخل این [صفحه](http://tsetmc.com/Loader.aspx?Partree=15131T&c=IRO1BMLT0007) هست.
این اطلاعات رو میشه با `shareholders` گرفت که یک DataFrame هست.


<div dir="ltr">

```
ticker = Ticker("وبملت")
print(ticker.shareholders) # اطلاعات سهام داران عمده

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

##### شناور سهم
برای مثال میشه با استفاده از سهامداران عمده شناور سهم رو حساب کرد:

<div dir="ltr">

```
ticker.shareholders.percentage.sum() # جمع سهام داران
53.63

100 - ticker.shareholders.percentage.sum() # شناور سهم 
46.37
```
</div>


<div id="qa" />

#### کامیونیتی

اگر درباره پکیج یا استفاده از اون سوالی دارید میتونید توی سرور دیسکورد بپرسید.

https://discord.gg/ampPDKHpVv

<div id="required-packages" />

#### پکیج های مورد نیاز:

- [Pandas](https://github.com/pydata/pandas)
- [Requests](http://docs.python-requests.org/en/master/)
- [jdatetime](https://github.com/slashmili/python-jalali)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4)

<div id="credits" />

#### الهام گرفته از:

- [tehran_stocks](https://github.com/ghodsizadeh/tehran-stocks)
- [yfinance](https://github.com/ranaroussi/yfinance)

</div>
