from pytse_client import FinancialIndex

fIndex = FinancialIndex("شاخص كل")
# شاخص کل
fIndex = FinancialIndex(symbol="",
                        index="32097828799138957")
# فرآوده های نفتی
fIndex = FinancialIndex(symbol="",
                        index="12331083953323969")
fIndex = FinancialIndex(symbol="شاخص قيمت 50 شركت")
fIndex = FinancialIndex(symbol="فني مهندسي")
fIndex = FinancialIndex(symbol="فراورده نفتي",
                        index="12331083953323969")
# اگر باهم استفاده شوند معیار index میشود.

print(fIndex.history)
print(fIndex.intraday_price)
print(fIndex.high)
print(fIndex.low)
print(fIndex.last_update)
print(fIndex.last_value)
print(fIndex.contributing_symbols)
