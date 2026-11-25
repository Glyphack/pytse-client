"""Calls every public API of pytse_client once against the live TSETMC
servers, with one symbol each, so a full run stays short.

Every test has the e2e marker. Files the APIs write go to a temporary
folder. Run it with `mise run e2e`.
"""

import asyncio
import datetime

import pandas as pd
import pytest

import pytse_client as tse

pytestmark = pytest.mark.e2e

SYMBOL = "فولاد"
# few trades a day, so the intraday history of a day is small
INTRADAY_SYMBOL = "دیران"
FUND_SYMBOL = "کاریس"
INDEX_NAME = "شاخص كل"
INDEX_ID = "32097828799138957"  # شاخص کل
DELETED_SYMBOL_INDEX = "25165947991415904"  # خصدرا, removed from the market

TICKER_PROPERTIES = (
    "title",
    "fulltitle",
    "url",
    "index",
    "instrument_id",
    "ci_sin",
    "group_name",
    "fiscal_year",
    "eps",
    "p_e_ratio",
    "group_p_e_ratio",
    "nav",
    "nav_date",
    "psr",
    "p_s_ratio",
    "base_volume",
    "state",
    "last_price",
    "adj_close",
    "yesterday_price",
    "open_price",
    "high_price",
    "low_price",
    "count",
    "volume",
    "value",
    "last_date",
    "flow",
    "sta_max",
    "sta_min",
    "min_week",
    "max_week",
    "min_year",
    "max_year",
    "month_average_volume",
    "float_shares",
    "best_supply_price",
    "best_supply_vol",
    "best_demand_price",
    "best_demand_vol",
    "total_shares",
    "market_cap",
    "trade_dates",
)

# fields a stock always has, even when the market is closed
REQUIRED_TICKER_PROPERTIES = (
    "title",
    "url",
    "group_name",
    "eps",
    "base_volume",
    "state",
    "last_price",
    "adj_close",
    "yesterday_price",
    "flow",
    "total_shares",
    "market_cap",
)


@pytest.fixture(scope="module", autouse=True)
def output_dir(tmp_path_factory):
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(tmp_path_factory.mktemp("e2e"))
        yield


@pytest.fixture(scope="module")
def ticker(output_dir) -> tse.Ticker:
    return tse.Ticker(SYMBOL)


@pytest.fixture(scope="module")
def intraday_ticker(output_dir) -> tse.Ticker:
    return tse.Ticker(INTRADAY_SYMBOL)


@pytest.fixture(scope="module")
def day(intraday_ticker) -> datetime.date:
    # a finished trading day, so its intraday history is complete
    return intraday_ticker.trade_dates[-2]


def assert_not_empty(df):
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_all_symbols():
    assert SYMBOL in tse.all_symbols()


def test_download():
    result = tse.download(
        symbols=SYMBOL, write_to_csv=True, include_jdate=True
    )
    assert_not_empty(result[SYMBOL])
    assert "jdate" in result[SYMBOL].columns


def test_download_client_types_records():
    result = tse.download_client_types_records(SYMBOL, write_to_csv=True)
    assert_not_empty(result[SYMBOL])


def test_download_financial_indexes():
    result = tse.download_financial_indexes(
        symbols=INDEX_NAME, write_to_csv=True, include_jdate=True
    )
    assert_not_empty(result[INDEX_NAME])
    assert "jdate" in result[INDEX_NAME].columns


def test_financial_index():
    index = tse.FinancialIndex(symbol=INDEX_NAME)
    assert_not_empty(index.history)
    assert_not_empty(index.intraday_price)
    assert index.contributing_symbols
    assert index.last_value is not None
    assert index.last_update is not None
    assert index.high is not None
    assert index.low is not None


def test_financial_index_by_id():
    assert_not_empty(tse.FinancialIndex(symbol="", index=INDEX_ID).history)


def test_get_orderbook(day):
    key = day.strftime("%Y-%m-%d")
    processed = tse.get_orderbook(
        INTRADAY_SYMBOL, start_date=day, end_date=day, to_csv=True
    )
    assert_not_empty(processed[key])
    diff = tse.get_orderbook(
        INTRADAY_SYMBOL,
        start_date=day,
        end_date=day,
        diff_orderbook=True,
        async_requests=False,
    )
    assert_not_empty(diff[key])


def test_get_trade_details(day):
    ticks = tse.get_trade_details(INTRADAY_SYMBOL, day, to_csv=True)
    assert_not_empty(ticks[day])


def test_get_stats():
    assert_not_empty(tse.get_stats(to_csv=True))


def test_get_asks_and_bids():
    assert_not_empty(tse.get_asks_and_bids(to_csv=True))


def test_ticker_properties(ticker):
    values = {name: getattr(ticker, name) for name in TICKER_PROPERTIES}
    for name in REQUIRED_TICKER_PROPERTIES:
        assert values[name] is not None, name
    assert_not_empty(ticker.history)
    assert_not_empty(ticker.client_types)
    assert_not_empty(ticker.shareholders)
    assert isinstance(tse.Ticker.get_last_trade_day(), datetime.date)


def test_ticker_real_time_info(ticker):
    info = ticker.get_ticker_real_time_info_response()
    assert info.last_price is not None
    assert info.buy_orders or info.sell_orders
    for order in (info.buy_orders or []) + (info.sell_orders or []):
        assert order.price is not None
        assert order.volume is not None
        assert order.count is not None
    for summary in (
        info.individual_trade_summary,
        info.corporate_trade_summary,
    ):
        assert summary is not None
        assert summary.buy_count is not None
        assert summary.buy_vol is not None
        assert summary.sell_count is not None
        assert summary.sell_vol is not None


def test_ticker_trade_details(ticker):
    trades = ticker.get_trade_details()
    assert list(trades.columns) == ["date", "volume", "price"]


def test_ticker_trade_details_of_a_day(intraday_ticker, day):
    candles = intraday_ticker.get_trade_details(
        day, day, aggregate=True, timeframe="1m"
    )
    assert_not_empty(candles["aggregate"])


def test_ticker_shareholders_history(ticker):
    history = ticker.get_shareholders_history(
        from_when=datetime.timedelta(days=7)
    )
    assert_not_empty(history)


def test_ticker_async_history(ticker):
    async def fetch():
        return await asyncio.gather(
            ticker.get_shareholders_history_async(
                from_when=datetime.timedelta(days=7)
            ),
            ticker.get_total_shares_history_async(
                from_when=datetime.timedelta(days=7)
            ),
        )

    shareholders, total_shares = asyncio.run(fetch())
    assert_not_empty(shareholders)
    assert_not_empty(total_shares)


def test_adjusted_ticker():
    assert_not_empty(tse.Ticker(SYMBOL, adjust=True).history)


def test_deleted_ticker():
    assert_not_empty(tse.Ticker("", index=DELETED_SYMBOL_INDEX).history)


def test_fund_nav():
    fund = tse.Ticker(FUND_SYMBOL)
    assert fund.nav is not None
    assert fund.nav_date is not None


def test_export(ticker):
    assert_not_empty(tse.export_ticker_history_as_csv(ticker))
    assert len(tse.ticker_real_time_data_to_csv(ticker)) == 1
