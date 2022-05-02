"""
    به صورت درون روزانه به دیتاهای آپدیت شده شاخص ها دسترسی پیدا می‌کنیم.    
"""

from pytse_client import FinancialIndex

fIndex = FinancialIndex("شاخص كل")
fIndex = FinancialIndex(symbol="", index="32097828799138957") # شاخص کل
fIndex = FinancialIndex(symbol="", index="12331083953323969") # فرآوده های نفتی
fIndex = FinancialIndex(symbol="شاخص قيمت 50 شركت")
fIndex = FinancialIndex(symbol="فني مهندسي")
fIndex = FinancialIndex(symbol="فراورده نفتي", index="12331083953323969") # اگر باهم استفاده شوند معیار index میشود.

print(fIndex.history)
print(fIndex.intraday_price)
print(fIndex.high)
print(fIndex.low)
print(fIndex.last_update)
print(fIndex.last_value)
print(fIndex.contributing_symbols)

