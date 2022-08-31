TSE_TICKER_EXPORT_DATA_ADDRESS = (
    "http://tsetmc.com/tsev2/data/Export-txt.aspx?t=i&a=1&b=0&i={}"
)

TSE_FINANCIAL_INDEX_EXPORT_DATA_ADDRESS = (
    "http://www.tsetmc.com/tsev2/chart/data/Index.aspx?i={}&t=value"
)

FINANCIAL_INDEX_EXPORT_INTRADAY_URL = (
    "http://www.tsetmc.com/Loader.aspx?ParTree=15131J&i={}"
)


TSE_TICKER_ADDRESS = "http://tsetmc.com/Loader.aspx?ParTree=151311&i={}"

# FIXME: c should be cSecVal (group code of instrument)
# remove e parameter when instrument has not NAV value
TSE_ISNT_INFO_URL = (
    "http://www.tsetmc.com/tsev2/data/instinfofast.aspx?i={}&c=0&e=1"
)
TSE_TICKER_INTRODUCTION_URL = (
    "http://www.tsetmc.com/Loader.aspx?Partree=15131V&s={}"
)
TSE_CLIENT_TYPE_DATA_URL = (
    "http://www.tsetmc.com/tsev2/data/clienttype.aspx?i={}"
)
TSE_SYMBOL_ID_URL = "http://www.tsetmc.com/tsev2/data/search.aspx?skey={}"

TSE_TRADE_DETAIL_URL = "http://www.tsetmc.com/tsev2/data/TradeDetail.aspx?i={}"

# use instrument id as argument
TSE_SHAREHOLDERS_URL = "http://www.tsetmc.com/Loader.aspx?Partree=15131T&c={}"

# returns all the instrument data for a specific date
# date should be formatted like YYYYMMDD
INSTRUMENT_DAY_INFO_URL = (
    "http://cdn.tsetmc.com/Loader.aspx?ParTree=15131P&i={index}&d={date}"
)

# returns list of all symbols
SYMBOLS_LIST_URL = "http://www.tsetmc.com/Loader.aspx?ParTree=111C1417"

# market watch init, has initial data for market watch like symbols name etc.
MARKET_WATCH_INIT_URL = (
    "http://www.tsetmc.com/tsev2/data/MarketWatchInit.aspx?h=0&r=0"
)

# get day share holder data
SYMBOL_DAY_INFO_SHAREHOLDERS_DATA = (
    "http://cdn.tsetmc.com/api/Shareholder/{index}/{date}"
)

SYMBOL_DAY_INSTRUMENT_INFO_URL = (
    "http://cdn.tsetmc.com/api/Instrument/GetInstrumentHistory/{index}/{date}"
)

# get statistical information for all tickers
KEY_STATS_URL = "http://www.tsetmc.com/tsev2/data/InstValue.aspx?t=a"

# get some information about each ticker using دیده بان بازار
MARKET_WATCH_URL = (
    "http://www.tsetmc.com/tsev2/data/MarketWatchInit.aspx?h=0&r=0"
)


CLIENT_TYPES_URL = "http://www.tsetmc.com/tsev2/data/ClientTypeAll.aspx"

DATE_FORMAT = "%Y%m%d"
MIN_DATE = 20010321
