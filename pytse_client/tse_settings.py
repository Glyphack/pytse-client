TSE_GET_LAST_TRADE_DAY = (
    "https://cdn.tsetmc.com/api/MarketData/GetMarketOverview/1"
)

# The last path part is the number of days, 0 means the whole history.
TSE_TICKER_EXPORT_DATA_ADDRESS = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{}/0"
)

TSE_TICKER_RECENT_DAYS_URL = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{}/12"
)

TSE_FINANCIAL_INDEX_EXPORT_DATA_ADDRESS = (
    "https://cdn.tsetmc.com/api/Index/GetIndexB2History/{}"
)

FINANCIAL_INDEX_EXPORT_INTRADAY_URL = (
    "https://cdn.tsetmc.com/api/Index/GetIndexB1LastDay/{}"
)

FINANCIAL_INDEX_COMPANIES_URL = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetIndexCompany/{}"
)

TSE_TICKER_ADDRESS = "https://www.tsetmc.com/instInfo/{}"

TSE_INSTRUMENT_INFO = (
    "https://cdn.tsetmc.com/api/Instrument/GetInstrumentInfo/{}"
)

TSE_CLOSING_PRICE_INFO_URL = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceInfo/{}"
)

TSE_BEST_LIMITS_URL = "https://cdn.tsetmc.com/api/BestLimits/{}"

TSE_CLIENT_TYPE_URL = (
    "https://cdn.tsetmc.com/api/ClientType/GetClientType/{}/1/0"
)

TSE_ETF_URL = "https://cdn.tsetmc.com/api/Fund/GetETFByInsCode/{}"

# Takes the symbol, not the insCode.
TSE_TICKER_INTRODUCTION_URL = (
    "https://cdn.tsetmc.com/api/Codal/GetCodalPublisherBySymbol/{}"
)

TSE_CLIENT_TYPE_DATA_URL = (
    "https://cdn.tsetmc.com/api/ClientType/GetClientTypeHistory/{}"
)

TSE_SYMBOL_ID_URL = (
    "https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/{}"
)

TSE_TRADE_DETAIL_URL = "https://cdn.tsetmc.com/api/Trade/GetTrade/{}"

TSE_SHAREHOLDERS_URL = (
    "https://cdn.tsetmc.com/api/Shareholder/GetInstrumentShareHolderLast/{}"
)

CLOSING_PRICE_DAILY_ALL_INST_URL = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyAllInst"
)

# The last path part is the flow: 1 for bourse, 2 for fara bourse.
INDICES_LIST_URL = "https://cdn.tsetmc.com/api/Index/GetIndexB1LastAll/All/{}"

SYMBOL_DAY_INFO_SHAREHOLDERS_DATA = (
    "https://cdn.tsetmc.com/api/Shareholder/{index}/{date}"
)

SYMBOL_DAY_INSTRUMENT_INFO_URL = (
    "https://cdn.tsetmc.com/api/Instrument/GetInstrumentHistory/{index}/{date}"
)

KEY_STATS_URL = (
    "https://cdn.tsetmc.com/api/MarketData/GetInstValueAllInstAllParam"
)

MARKET_WATCH_URL = (
    "https://cdn.tsetmc.com/api/ClosingPrice/GetMarketWatch"
    "?market=0&industrialGroup="
    "&paperTypes[0]=1&paperTypes[1]=2&paperTypes[2]=3&paperTypes[3]=4"
    "&paperTypes[4]=5&paperTypes[5]=6&paperTypes[6]=7&paperTypes[7]=8"
    "&paperTypes[8]=9&showTraded=false&withBestLimits=true"
)

TICKER_ORDER_BOOK = "https://cdn.tsetmc.com/api/BestLimits/{index}/{date}"

# With "true" instead of "false" the API returns only part of the trades.
TICKER_TRADE_DETAILS = (
    "https://cdn.tsetmc.com/api/Trade/GetTradeHistory/{index}/{date}/false"
)

CLIENT_TYPES_URL = "https://cdn.tsetmc.com/api/ClientType/GetClientTypeAll"

DATE_FORMAT = "%Y%m%d"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.tsetmc.com",
    "Referer": "https://www.tsetmc.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
}
