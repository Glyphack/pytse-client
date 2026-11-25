"""Tests of pytse_client.ticker: Ticker, get_trade_details and the two
export functions, on the saved responses of the symbol دیران."""

import asyncio
import datetime
import json
import math
from pathlib import Path

import pandas as pd
import pytest
import requests

import pytse_client as tse
from pytse_client.ticker.ticker import RealtimeTickerInfo
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.best_limits import Order
from pytse_client.tsetmc_api.client_type import TradeSummary

SYMBOL = "دیران"
DIRAN = "69090868458637360"
# the day of the saved trades, order book and shareholders of a past day
DAY = datetime.date(2026, 11, 22)
# the newest day of the saved daily history
LAST_DAY = datetime.date(2026, 11, 23)

HISTORY_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "adjClose",
    "value",
    "volume",
    "count",
    "yesterday",
    "close",
]


@pytest.fixture
def ticker() -> tse.Ticker:
    return tse.Ticker(SYMBOL)


# ---------------------------------------------------------------------------
# creating a ticker


def test_ticker_of_a_symbol(ticker, fake_api):
    assert ticker.symbol == SYMBOL
    assert ticker.index == DIRAN
    assert ticker.url == f"https://www.tsetmc.com/instInfo/{DIRAN}"
    assert ticker.adjust is False
    assert ticker.daily_records_csv_path == "tickers_data/دیران.csv"
    assert ticker.adjusted_daily_records_csv_path == "tickers_data/دیران-ت.csv"
    # nothing is asked or written before it is needed
    assert fake_api.calls == []
    assert list(Path.cwd().iterdir()) == []


def test_ticker_accepts_arabic_letters_and_spaces():
    # ي and ك of the website in place of the Persian ی and ک
    ticker = tse.Ticker(" ديران ")
    assert ticker.symbol == SYMBOL
    assert ticker.index == DIRAN


def test_ticker_of_an_index_has_the_index_as_symbol():
    ticker = tse.Ticker("", index="25165947991415904")
    assert ticker.index == "25165947991415904"
    assert ticker.symbol == "25165947991415904"
    assert ticker.daily_records_csv_path == (
        "tickers_data/25165947991415904.csv"
    )


def test_unknown_symbol_is_an_error():
    with pytest.raises(ValueError, match="Symbol ناموجود not found"):
        tse.Ticker("ناموجود")


# ---------------------------------------------------------------------------
# information of the instrument


def test_instrument_information(ticker, fake_api):
    assert ticker.title == "ایران‌دارو"
    assert ticker.fulltitle == "ایران‌دارو"
    assert ticker.instrument_id == "IRO1IRDR0001"
    assert ticker.ci_sin == "IRO1IRDR0007"
    assert ticker.group_name == "مواد و محصولات دارويي"
    assert ticker.flow == "بورس"
    assert ticker.total_shares == 1780000000.0
    assert ticker.base_volume == 1.0
    assert ticker.sta_max == 24020.0
    assert ticker.sta_min == 22640.0
    assert ticker.min_week == 22000.0
    assert ticker.max_week == 24020.0
    assert ticker.min_year == 3633.0
    assert ticker.max_year == 24790.0
    assert ticker.month_average_volume == "18051688"
    assert ticker.float_shares == 49.0
    assert ticker.eps == 3064.0
    assert ticker.group_p_e_ratio == 11.85
    assert ticker.psr == 12734.175
    for name in ("total_shares", "base_volume", "sta_max", "min_year"):
        assert isinstance(getattr(ticker, name), float), name
    # the information is asked once
    assert fake_api.calls == [("instrument_info", DIRAN)]


def test_title_is_the_name_before_the_dash(ticker, fake_api, sample):
    info = sample("instrument_info")
    info["instrumentInfo"]["lVal30"] = "صندوق س.سپند كاريزما-س"
    fake_api.responses["instrument_info"] = info
    assert ticker.title == "صندوق س.سپند کاریزما"
    assert ticker.fulltitle == "صندوق س.سپند کاریزما-س"


def test_information_the_api_does_not_have_is_none(ticker, fake_api, sample):
    info = sample("instrument_info")
    info["instrumentInfo"]["eps"] = {
        "epsValue": None,
        "estimatedEPS": "",
        # the api sends 0 for a missing P/E of the sector and PSR
        "sectorPE": 0.0,
        "psr": 0.0,
    }
    info["instrumentInfo"]["staticThreshold"] = None
    info["instrumentInfo"]["minWeek"] = None
    info["instrumentInfo"]["maxYear"] = None
    info["instrumentInfo"]["kAjCapValCpsIdx"] = ""
    info["instrumentInfo"]["flow"] = 9
    fake_api.responses["instrument_info"] = info
    assert ticker.eps is None
    assert ticker.group_p_e_ratio is None
    assert ticker.psr is None
    assert ticker.p_e_ratio is None
    assert ticker.p_s_ratio is None
    assert ticker.sta_max is None
    assert ticker.sta_min is None
    assert ticker.min_week is None
    assert ticker.max_year is None
    assert ticker.float_shares is None
    assert ticker.flow == ""


def test_price_limits_are_none_when_the_api_sends_no_number(
    ticker, fake_api, sample
):
    info = sample("instrument_info")
    info["instrumentInfo"]["maxWeek"] = "-"
    fake_api.responses["instrument_info"] = info
    assert ticker.max_week is None
    assert ticker.min_week is None
    assert ticker.sta_max is None
    assert ticker.float_shares is None


def test_ratios_use_the_closing_price(ticker):
    # closing price 24020, EPS 3064 and PSR 12734.175
    assert ticker.p_e_ratio == pytest.approx(7.83943, abs=1e-5)
    assert ticker.p_s_ratio == pytest.approx(1.88626, abs=1e-5)


def test_fiscal_year(ticker, fake_api):
    assert ticker.fiscal_year == "09/30"
    # codal is asked with the symbol the way the api writes it
    assert ("codal_publisher", "ديران") in fake_api.calls


def test_fiscal_year_of_a_ticker_created_with_an_index(fake_api):
    assert tse.Ticker("", index=DIRAN).fiscal_year == "09/30"
    assert ("codal_publisher", "ديران") in fake_api.calls


@pytest.mark.parametrize(
    "answer",
    [
        {"codalPublisher": None},
        {"codalPublisher": {"financialYear": ""}},
        requests.HTTPError("500 Server Error"),
    ],
)
def test_fiscal_year_is_none_without_a_codal_introduction(
    ticker, fake_api, answer
):
    if isinstance(answer, Exception):
        fake_api.errors["codal_publisher"] = answer
    else:
        fake_api.responses["codal_publisher"] = answer
    assert ticker.fiscal_year is None


def test_last_trade_day_of_the_market():
    assert tse.Ticker.get_last_trade_day() == LAST_DAY


# ---------------------------------------------------------------------------
# real time information

BUY_ORDERS = [
    Order(count=419, volume=31322288, price=24020),
    Order(count=2, volume=13430, price=23860),
    Order(count=8, volume=158553, price=23330),
    Order(count=1, volume=1334, price=23000),
    Order(count=2, volume=451, price=22660),
]
SELL_ORDERS = [
    Order(count=1, volume=294, price=24070),
    Order(count=4, volume=6284, price=24790),
    Order(count=0, volume=0, price=0),
    Order(count=0, volume=0, price=0),
    Order(count=0, volume=0, price=0),
]


def test_real_time_info(ticker, fake_api):
    info = ticker.get_ticker_real_time_info_response()
    assert info == RealtimeTickerInfo(
        date_time=info.date_time,
        state="مجاز",
        last_price=24020,
        adj_close=24020,
        yesterday_price=23330,
        open_price=24020,
        high_price=24020,
        low_price=24020,
        count=99,
        volume=860939,
        value=20679754780,
        last_date=datetime.datetime(2026, 11, 23, 12, 29, 52),
        best_demand_vol=31322288,
        best_demand_price=24020,
        best_supply_vol=294,
        best_supply_price=24070,
        sell_orders=SELL_ORDERS,
        buy_orders=BUY_ORDERS,
        individual_trade_summary=TradeSummary(
            buy_vol=860939.0,
            buy_count=13.0,
            sell_vol=703139.0,
            sell_count=75.0,
        ),
        corporate_trade_summary=TradeSummary(
            buy_vol=0.0, buy_count=0.0, sell_vol=157800.0, sell_count=1.0
        ),
        nav=None,
        nav_date=None,
        # closing price times the 1,780,000,000 shares
        market_cap=42755600000000,
    )
    age = datetime.datetime.now() - info.date_time
    assert datetime.timedelta(0) <= age < datetime.timedelta(minutes=1)
    assert isinstance(info.last_price, int)
    # the price box, the order book and the client types, each once; دیران
    # is not a fund, so its NAV is not asked
    assert sorted(fake_api.calls) == [
        ("best_limits", DIRAN),
        ("client_type", DIRAN),
        ("closing_price_info", DIRAN),
        ("instrument_info", DIRAN),
    ]


def test_real_time_properties(ticker):
    assert ticker.state == "مجاز"
    assert ticker.last_price == 24020
    assert ticker.adj_close == 24020
    assert ticker.yesterday_price == 23330
    assert ticker.open_price == 24020
    assert ticker.high_price == 24020
    assert ticker.low_price == 24020
    assert ticker.count == 99
    assert ticker.volume == 860939
    assert ticker.value == 20679754780
    assert ticker.last_date == datetime.datetime(2026, 11, 23, 12, 29, 52)
    assert ticker.market_cap == 42755600000000.0
    assert ticker.best_demand_vol == 31322288
    assert ticker.best_demand_price == 24020
    assert ticker.best_supply_vol == 294
    assert ticker.best_supply_price == 24070
    assert ticker.nav is None
    assert ticker.nav_date is None


def test_real_time_properties_ask_only_for_what_they_need(ticker, fake_api):
    assert ticker.last_price == 24020
    assert fake_api.calls == [
        ("closing_price_info", DIRAN),
        # the number of shares, for the market cap
        ("instrument_info", DIRAN),
    ]
    fake_api.calls.clear()
    assert ticker.best_supply_price == 24070
    assert fake_api.calls == [("best_limits", DIRAN)]
    fake_api.calls.clear()
    assert ticker.nav is None
    assert fake_api.calls == []


@pytest.mark.parametrize(
    "code, title, state",
    [
        ("A ", "مجاز", "مجاز"),
        ("IS", "ممنوع-متوقف", "ممنوع-متوقف"),
        ("AR", "any title", "مجاز-محفوظ"),
        # a code the library does not know gets the title of the api
        ("ZZ", "عنوان تازه", "عنوان تازه"),
        (None, None, None),
    ],
)
def test_state_of_the_symbol(ticker, fake_api, sample, code, title, state):
    prices = sample("closing_price_info")
    prices["closingPriceInfo"]["instrumentState"]["cEtaval"] = code
    prices["closingPriceInfo"]["instrumentState"]["cEtavalTitle"] = title
    fake_api.responses["closing_price_info"] = prices
    assert ticker.state == state


def test_real_time_info_without_prices(ticker, fake_api):
    fake_api.responses["closing_price_info"] = {"closingPriceInfo": None}
    info = ticker.get_ticker_real_time_info_response()
    for name in (
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
        "market_cap",
    ):
        assert getattr(info, name) is None, name
    # the other parts are still there
    assert info.buy_orders == BUY_ORDERS
    assert info.individual_trade_summary is not None
    assert ticker.p_e_ratio is None
    assert ticker.p_s_ratio is None


def test_real_time_info_without_a_state_or_the_time_of_the_prices(
    ticker, fake_api, sample
):
    prices = sample("closing_price_info")
    prices["closingPriceInfo"]["instrumentState"] = None
    prices["closingPriceInfo"]["dEven"] = 0
    fake_api.responses["closing_price_info"] = prices
    assert ticker.state is None
    assert ticker.last_date is None
    assert ticker.last_price == 24020


def test_orders_put_the_best_price_first(ticker, fake_api, sample):
    levels = sample("best_limits")
    levels["bestLimits"].reverse()
    fake_api.responses["best_limits"] = levels
    info = ticker.get_ticker_real_time_info_response()
    assert info.buy_orders == BUY_ORDERS
    assert info.sell_orders == SELL_ORDERS


def test_real_time_info_without_orders_and_client_types(ticker, fake_api):
    fake_api.responses["best_limits"] = {"bestLimits": []}
    fake_api.responses["client_type"] = {"clientType": None}
    info = ticker.get_ticker_real_time_info_response()
    assert info.buy_orders == []
    assert info.sell_orders == []
    assert info.best_demand_vol is None
    assert info.best_demand_price is None
    assert info.best_supply_vol is None
    assert info.best_supply_price is None
    assert info.individual_trade_summary is None
    assert info.corporate_trade_summary is None
    assert info.last_price == 24020


@pytest.fixture
def fund(fake_api, sample) -> tse.Ticker:
    """The fund کاریس: the saved information of دیران with the ISIN of the
    fund, which starts with IRT like the one of every fund."""
    info = sample("instrument_info")
    info["instrumentInfo"]["instrumentID"] = "IRT3SSKF0001"
    fake_api.responses["instrument_info"] = info
    return tse.Ticker("کاریس")


def test_nav_of_a_fund(fund, fake_api):
    assert fund.nav == 94233
    assert isinstance(fund.nav, int)
    # the Jalali day of 2026-11-23 and the time the NAV was published
    assert fund.nav_date == "1405/9/2 12:33:36"
    assert ("etf", "69067576215760005") in fake_api.calls
    info = fund.get_ticker_real_time_info_response()
    assert info.nav == 94233
    assert info.nav_date == "1405/9/2 12:33:36"


@pytest.mark.parametrize(
    "answer",
    [
        {"etf": None},
        {"etf": {"pRedTran": None, "deven": 20261123, "hEven": 123336}},
        # the api answers 500 when it has no NAV for the fund
        requests.HTTPError("500 Server Error"),
    ],
)
def test_fund_without_a_nav(fund, fake_api, answer):
    if isinstance(answer, Exception):
        fake_api.errors["etf"] = answer
    else:
        fake_api.responses["etf"] = answer
    assert fund.nav is None
    assert fund.nav_date is None


def test_nav_without_the_day_it_was_published(fund, fake_api):
    fake_api.responses["etf"] = {
        "etf": {"pRedTran": 94233.0, "deven": 0, "hEven": 123336}
    }
    assert fund.nav == 94233
    assert fund.nav_date is None


def test_deleted_instruments_have_no_real_time_info(symbols_file, fake_api):
    symbols = {
        "فعال": {"index": "1", "code": "", "name": "", "old": ["2"]},
        # the index of a deleted symbol is in its own old list
        "حذفی": {"index": "3", "code": "", "name": "", "old": ["3", "4"]},
    }
    symbols_file.write_text(json.dumps(symbols), encoding="utf8")

    assert tse.Ticker("فعال").last_price == 24020
    # an index that is no old index of a symbol
    assert tse.Ticker("", index="5").last_price == 24020
    for deleted in (
        tse.Ticker("حذفی"),
        tse.Ticker("", index="2"),
        tse.Ticker("", index="4"),
    ):
        with pytest.raises(RuntimeError, match="inactive ticker"):
            deleted.get_ticker_real_time_info_response()
        with pytest.raises(RuntimeError, match="inactive ticker"):
            _ = deleted.last_price
    # the history of a deleted instrument can still be read
    assert len(tse.Ticker("", index="2").history) == 60


# ---------------------------------------------------------------------------
# daily history


def test_history(ticker, fake_api):
    history = ticker.history
    assert list(history.columns) == HISTORY_COLUMNS
    assert len(history) == 60
    assert history.iloc[0].to_dict() == {
        "date": pd.Timestamp("2026-09-01"),
        "open": 15460.0,
        "high": 15460.0,
        "low": 15210.0,
        "adjClose": 15460.0,
        "value": 994717211730,
        "volume": 64360415,
        "count": 1973,
        "yesterday": 15010.0,
        "close": 15460.0,
    }
    assert history.iloc[-1].to_dict() == {
        "date": pd.Timestamp("2026-11-23"),
        "open": 24020.0,
        "high": 24020.0,
        "low": 24020.0,
        "adjClose": 24020.0,
        "value": 20679754780,
        "volume": 860939,
        "count": 99,
        "yesterday": 23330.0,
        "close": 24020.0,
    }
    # oldest day first
    assert history["date"].is_monotonic_increasing
    assert pd.api.types.is_datetime64_any_dtype(history["date"])
    prices = ["open", "high", "low", "adjClose", "yesterday", "close"]
    assert (history.dtypes[prices] == "float64").all()
    assert (history.dtypes[["value", "volume", "count"]] == "int64").all()
    assert fake_api.calls == [("closing_price_daily_list", DIRAN)]


def test_history_is_loaded_once_and_saved_to_a_csv_file(ticker, fake_api):
    history = ticker.history
    assert ticker.history is history
    assert len(fake_api.calls) == 1
    saved = pd.read_csv("tickers_data/دیران.csv")
    assert list(saved.columns) == HISTORY_COLUMNS
    assert len(saved) == 60
    assert saved["date"].iloc[-1] == "2026-11-23"
    assert saved["adjClose"].iloc[-1] == 24020.0


def test_history_leaves_out_days_without_a_trade(ticker, fake_api, sample):
    days = sample("closing_price_daily_list")
    assert days["closingPriceDaily"][1]["dEven"] == 20261122
    days["closingPriceDaily"][1]["zTotTran"] = 0.0
    fake_api.responses["closing_price_daily_list"] = days
    history = ticker.history
    assert len(history) == 59
    assert pd.Timestamp(DAY) not in set(history["date"])
    assert DAY not in ticker.trade_dates


def test_saved_history_is_read_from_the_csv_file(ticker, fake_api):
    downloaded = ticker.history
    fake_api.calls.clear()

    again = tse.Ticker(SYMBOL).history
    # only the last days are asked, to see that the file has them all
    assert fake_api.calls == [("recent_closing_price_daily_list", DIRAN)]
    pd.testing.assert_frame_equal(again, downloaded)
    pd.testing.assert_frame_equal(tse.Ticker(SYMBOL).from_file(), downloaded)


def saved_history_until(last_day: str) -> None:
    """Write the csv file of دیران with the saved daily history up to a
    day (YYYY-MM-DD)."""
    history = tse.download(SYMBOL)[SYMBOL]
    Path("tickers_data").mkdir(exist_ok=True)
    history[history["date"] <= last_day].to_csv(
        "tickers_data/دیران.csv", index=False
    )


def test_saved_history_without_the_last_days_is_downloaded_again(fake_api):
    saved_history_until("2026-11-21")
    fake_api.calls.clear()

    history = tse.Ticker(SYMBOL).history
    assert fake_api.calls == [
        ("recent_closing_price_daily_list", DIRAN),
        ("closing_price_daily_list", DIRAN),
    ]
    assert len(history) == 60
    assert history["date"].iloc[-1] == pd.Timestamp(LAST_DAY)
    assert len(pd.read_csv("tickers_data/دیران.csv")) == 60


def test_empty_saved_history_is_downloaded_again(fake_api):
    saved_history_until("2000-01-01")
    fake_api.calls.clear()
    assert len(tse.Ticker(SYMBOL).history) == 60
    assert fake_api.calls == [("closing_price_daily_list", DIRAN)]


def test_saved_history_is_used_when_the_api_has_no_recent_days(fake_api):
    saved_history_until("2026-11-21")
    fake_api.calls.clear()
    fake_api.responses["recent_closing_price_daily_list"] = {
        "closingPriceDaily": []
    }
    history = tse.Ticker(SYMBOL).history
    assert history["date"].iloc[-1] == pd.Timestamp("2026-11-21")
    assert fake_api.calls == [("recent_closing_price_daily_list", DIRAN)]


@pytest.mark.parametrize(
    "last_saved_day, downloads_again",
    [
        # the 12 recent days start on 2026-11-08: they reach back to the
        # last saved day, so nothing was traded since
        ("2026-11-10", False),
        # the days between the last saved day and the 12 recent ones are
        # not known
        ("2026-11-04", True),
    ],
)
def test_saved_history_and_recent_days_without_a_trade(
    fake_api, sample, last_saved_day, downloads_again
):
    saved_history_until(last_saved_day)
    fake_api.calls.clear()
    recent = sample("recent_closing_price_daily_list")
    for day in recent["closingPriceDaily"]:
        day["zTotTran"] = 0.0
    fake_api.responses["recent_closing_price_daily_list"] = recent

    _ = tse.Ticker(SYMBOL).history
    downloaded = ("closing_price_daily_list", DIRAN) in fake_api.calls
    assert downloaded is downloads_again


def test_adjusted_history(fake_api, sample):
    days = sample("closing_price_daily_list")
    # the newest day opens at half the closing price of the day before,
    # like after a capital increase
    assert days["closingPriceDaily"][1]["pClosing"] == 23330.0
    days["closingPriceDaily"][0]["priceYesterday"] = 11665.0
    fake_api.responses["closing_price_daily_list"] = days

    adjusted = tse.Ticker(SYMBOL, adjust=True).history
    assert adjusted["adjClose"].iloc[-1] == 24020.0
    # the older days are halved
    assert adjusted["adjClose"].iloc[-2] == 11665.0
    assert adjusted["adjClose"].iloc[0] == 7730.0
    assert adjusted["yesterday"].iloc[0] == 7505.0
    assert [path.name for path in Path("tickers_data").iterdir()] == [
        "دیران-ت.csv"
    ]

    fake_api.calls.clear()
    again = tse.Ticker(SYMBOL, adjust=True).history
    assert fake_api.calls == [("recent_closing_price_daily_list", DIRAN)]
    pd.testing.assert_frame_equal(again, adjusted)
    # a ticker that is not adjusted does not read the adjusted file
    assert tse.Ticker(SYMBOL).history["adjClose"].iloc[0] == 15460.0


def test_history_of_a_ticker_created_with_an_index(fake_api):
    ticker = tse.Ticker("", index="25165947991415904")
    assert len(ticker.history) == 60
    assert fake_api.calls == [
        ("closing_price_daily_list", "25165947991415904")
    ]
    assert Path("tickers_data/25165947991415904.csv").exists()


def test_trade_dates(ticker):
    dates = ticker.trade_dates
    assert len(dates) == 60
    assert dates[0] == datetime.date(2026, 9, 1)
    assert dates[-3:] == [datetime.date(2026, 11, 21), DAY, LAST_DAY]
    assert all(type(day) is datetime.date for day in dates)


def test_valid_dates_are_the_traded_days_of_a_range(ticker):
    # 2026-11-19 and 20 are a Thursday and a Friday, the market is closed
    assert ticker.get_valid_dates(datetime.date(2026, 11, 18), LAST_DAY) == [
        datetime.date(2026, 11, 18),
        datetime.date(2026, 11, 21),
        DAY,
        LAST_DAY,
    ]
    assert ticker.get_valid_dates(DAY, DAY) == [DAY]
    assert (
        ticker.get_valid_dates(
            datetime.date(2026, 11, 19), datetime.date(2026, 11, 20)
        )
        == []
    )
    assert ticker.get_valid_dates(LAST_DAY, DAY) == []


# ---------------------------------------------------------------------------
# client types

CLIENT_TYPES_COLUMNS = [
    "date",
    "individual_buy_count",
    "corporate_buy_count",
    "individual_sell_count",
    "corporate_sell_count",
    "individual_buy_vol",
    "corporate_buy_vol",
    "individual_sell_vol",
    "corporate_sell_vol",
    "individual_buy_value",
    "corporate_buy_value",
    "individual_sell_value",
    "corporate_sell_value",
    "individual_buy_mean_price",
    "individual_sell_mean_price",
    "corporate_buy_mean_price",
    "corporate_sell_mean_price",
    "individual_ownership_change",
]


def test_client_types(ticker, fake_api):
    client_types = ticker.client_types
    assert fake_api.calls == [("client_type_history", DIRAN)]
    assert list(client_types.columns) == CLIENT_TYPES_COLUMNS
    assert len(client_types) == 60
    # newest day first
    assert client_types.iloc[1].to_dict() == {
        "date": "20261122",
        "individual_buy_count": 63,
        "corporate_buy_count": 1,
        "individual_sell_count": 60,
        "corporate_sell_count": 2,
        "individual_buy_vol": 4772247,
        "corporate_buy_vol": 100000,
        "individual_sell_vol": 484421,
        "corporate_sell_vol": 4387826,
        "individual_buy_value": 111336522510,
        "corporate_buy_value": 2333000000,
        "individual_sell_value": 11301541930,
        "corporate_sell_value": 102367980580,
        # value / volume, every trade of the day was at 23330
        "individual_buy_mean_price": 23330.0,
        "individual_sell_mean_price": 23330.0,
        "corporate_buy_mean_price": 23330.0,
        "corporate_sell_mean_price": 23330.0,
        # shares the corporations sold minus the ones they bought
        "individual_ownership_change": 4287826.0,
    }
    assert client_types["date"].iloc[0] == "20261123"
    assert client_types["date"].iloc[-1] == "20260901"
    newest = client_types.iloc[0]
    assert newest["individual_ownership_change"] == 157800.0
    # corporations bought nothing that day
    assert math.isnan(newest["corporate_buy_mean_price"])
    oldest = client_types.iloc[-1]
    assert oldest["individual_buy_mean_price"] == pytest.approx(
        15455.3527, abs=1e-4
    )
    counts_and_values = CLIENT_TYPES_COLUMNS[1:13]
    assert (client_types.dtypes[counts_and_values] == "int64").all()
    assert (client_types.dtypes[CLIENT_TYPES_COLUMNS[13:]] == "float64").all()


def test_client_types_without_any_day_is_an_error(ticker, fake_api):
    fake_api.responses["client_type_history"] = {"clientType": []}
    with pytest.raises(RuntimeError, match="cannot download client types"):
        _ = ticker.client_types


# ---------------------------------------------------------------------------
# shareholders

HOLDING_COMPANY = "شركت گروه داروئي سبحان -سهامي عام -"
INVESTMENT_COMPANY = "شركت سرمايه گذاري اعتلاءالبرز-سهامي عام -"
PERSON = "شخص حقيقي"

SHAREHOLDERS_HISTORY_COLUMNS = [
    "date",
    "shareholder_id",
    "shareholder_shares",
    "shareholder_percentage",
    "shareholder_instrument_id",
    "shareholder_name",
    "change",
]

# the shareholders of DAY in the saved response, which also has the ones of
# the next trading day
SHAREHOLDERS_OF_DAY = {
    "shareholder_id": [28196811, 28197135, 28197564, 28198857, 28198961],
    "shareholder_shares": [
        24481108.0,
        36754390.0,
        40329158.0,
        851537355.0,
        41909509.0,
    ],
    "shareholder_percentage": [1.375, 2.064, 2.265, 47.839, 2.354],
    "shareholder_instrument_id": ["IRO1IRDR0007"] * 5,
    "shareholder_name": [
        PERSON,
        PERSON,
        PERSON,
        HOLDING_COMPANY,
        INVESTMENT_COMPANY,
    ],
    "change": [1, 1, 1, 1, 1],
}


def test_shareholders(ticker, fake_api):
    shareholders = ticker.shareholders
    assert fake_api.calls == [("shareholders", DIRAN)]
    assert shareholders.to_dict("list") == {
        "id": [1429364, 1432293, 1428398, 1433048, 1432292],
        "shareholder": [
            HOLDING_COMPANY,
            INVESTMENT_COMPANY,
            PERSON,
            PERSON,
            PERSON,
        ],
        "shares": [
            851537355.0,
            41909509.0,
            40329158.0,
            36754390.0,
            24481108.0,
        ],
        "percentage": [47.839, 2.354, 2.265, 2.064, 1.375],
        "change": [0.0, 0.0, 0.0, 0.0, 0.0],
    }
    assert (shareholders.dtypes[["shares", "change"]] == "float64").all()


def test_shareholders_history(ticker, fake_api):
    history = ticker.get_shareholders_history(
        from_when=datetime.timedelta(days=2),
        to_when=datetime.datetime(2026, 11, 22),
    )
    assert list(history.columns) == SHAREHOLDERS_HISTORY_COLUMNS
    # the 20th is a Friday; the answer for the 21st has no row of that
    # day or an earlier one
    assert history.to_dict("list") == {
        "date": [pd.Timestamp(DAY)] * 5,
        **SHAREHOLDERS_OF_DAY,
    }
    assert str(history["shareholder_shares"].dtype) == "float64"
    assert [
        call for call in fake_api.calls if call[0] != "day_shareholders"
    ] == [("closing_price_daily_list", DIRAN)]
    assert [
        call for call in fake_api.calls if call[0] == "day_shareholders"
    ] == [
        ("day_shareholders", DIRAN, datetime.datetime(2026, 11, 21)),
        ("day_shareholders", DIRAN, datetime.datetime(2026, 11, 22)),
    ]


def test_shareholders_history_of_days_without_a_trade(ticker, fake_api):
    history = ticker.get_shareholders_history(
        from_when=datetime.timedelta(days=2),
        to_when=datetime.datetime(2026, 11, 22),
        only_trade_days=False,
    )
    assert len(history) == 5
    asked = [
        call[2] for call in fake_api.calls if call[0] == "day_shareholders"
    ]
    assert asked == [
        datetime.datetime(2026, 11, 20),
        datetime.datetime(2026, 11, 21),
        datetime.datetime(2026, 11, 22),
    ]


def test_shareholders_history_up_to_now_when_no_end_is_given(ticker, fake_api):
    # today is after the last day of the saved history, so no day is asked
    history = ticker.get_shareholders_history(from_when=datetime.timedelta(0))
    assert list(history.columns) == SHAREHOLDERS_HISTORY_COLUMNS
    assert history.empty
    assert "day_shareholders" not in {call[0] for call in fake_api.calls}


def test_shareholders_history_async_on_a_session_of_the_caller(ticker):
    async def history_on_own_session() -> pd.DataFrame:
        async with client.open_session(limit=2) as session:
            history = await ticker.get_shareholders_history_async(
                from_when=datetime.timedelta(0),
                to_when=datetime.datetime(2026, 11, 22),
                session=session,
            )
            # the session of the caller stays open
            assert not session.closed
            return history

    history = asyncio.run(history_on_own_session())
    assert history["shareholder_id"].tolist() == (
        SHAREHOLDERS_OF_DAY["shareholder_id"]
    )


def test_total_shares_history(ticker, fake_api):
    history = asyncio.run(
        ticker.get_total_shares_history_async(
            from_when=datetime.timedelta(days=3),
            to_when=datetime.datetime(2026, 11, 23, 12),
        )
    )
    assert history.to_dict("list") == {
        "date": [datetime.date(2026, 11, 21), DAY, LAST_DAY],
        "total_shares": [1780000000.0] * 3,
    }
    assert str(history["total_shares"].dtype) == "float64"
    assert fake_api.calls[1:] == [
        ("instrument_history", DIRAN, datetime.date(2026, 11, 21)),
        ("instrument_history", DIRAN, DAY),
        ("instrument_history", DIRAN, LAST_DAY),
    ]


def test_total_shares_history_of_days_without_a_trade(ticker):
    history = asyncio.run(
        ticker.get_total_shares_history_async(
            from_when=datetime.timedelta(days=3),
            to_when=datetime.datetime(2026, 11, 23, 12),
            only_open_days=False,
        )
    )
    assert history["date"].tolist() == [
        datetime.date(2026, 11, 20),
        datetime.date(2026, 11, 21),
        DAY,
        LAST_DAY,
    ]


def test_total_shares_history_up_to_now_when_no_end_is_given(ticker):
    history = asyncio.run(
        ticker.get_total_shares_history_async(from_when=datetime.timedelta(0))
    )
    assert list(history.columns) == ["date", "total_shares"]
    assert history.empty


# ---------------------------------------------------------------------------
# trades of the current day


def test_trades_of_the_current_day(ticker, fake_api):
    trades = ticker.get_trade_details()
    assert fake_api.calls == [("trades", DIRAN)]
    assert list(trades.columns) == ["date", "volume", "price"]
    # the api sent one of the 99 trades twice
    assert len(trades) == 99
    assert trades.iloc[0].to_dict() == {
        "date": datetime.time(9, 0, 35),
        "volume": 16000,
        "price": 24020.0,
    }
    assert trades.iloc[-1].to_dict() == {
        "date": datetime.time(12, 29, 51),
        "volume": 500,
        "price": 24020.0,
    }
    assert trades["date"].is_monotonic_increasing
    # the count and volume of the day in the saved price box
    assert trades["volume"].sum() == ticker.volume == 860939
    assert len(trades) == ticker.count
    assert str(trades["volume"].dtype) == "int64"
    assert str(trades["price"].dtype) == "float64"
    # the arguments for past days do nothing, no file is written
    assert len(ticker.get_trade_details(to_csv=True, timeframe="1m")) == 99
    assert list(Path.cwd().iterdir()) == []


def test_trades_of_the_current_day_are_ordered_and_not_canceled(
    ticker, fake_api, sample
):
    data = sample("trades")
    last = data["trade"].pop()
    assert (last["nTran"], last["qTitTran"]) == (99, 500)
    # the newest trade comes first and the first one is canceled
    data["trade"].insert(0, last)
    assert data["trade"][1]["nTran"] == 1
    data["trade"][1]["canceled"] = 1
    fake_api.responses["trades"] = data

    trades = ticker.get_trade_details()
    assert len(trades) == 98
    assert trades["volume"].iloc[-1] == 500
    assert trades["volume"].sum() == 860939 - 16000


def test_no_trades_in_the_current_day(ticker, fake_api):
    fake_api.responses["trades"] = {"trade": []}
    trades = ticker.get_trade_details()
    assert list(trades.columns) == ["date", "volume", "price"]
    assert trades.empty


# ---------------------------------------------------------------------------
# trades of past days


def test_trades_of_a_past_day(ticker, fake_api):
    result = ticker.get_trade_details(DAY)
    assert list(result) == [DAY]
    trades = result[DAY]
    assert ("trade_history", DIRAN, DAY) in fake_api.calls
    assert list(trades.columns) == ["price", "volume"]
    assert trades.index.name == "datetime"
    assert len(trades) == 177
    assert trades.index[0] == pd.Timestamp("2026-11-22 09:00:35")
    assert trades.index[-1] == pd.Timestamp("2026-11-22 12:27:24")
    assert trades.index.is_monotonic_increasing
    assert trades.iloc[-1].to_dict() == {"price": 23330.0, "volume": 5000}
    assert str(trades["price"].dtype) == "float64"
    assert str(trades["volume"].dtype) == "int64"
    # nothing is written unless asked
    assert not Path("trade_details_history").exists()


def test_trades_of_a_past_day_add_up_to_the_totals_of_the_day(ticker):
    trades = ticker.get_trade_details(DAY)[DAY]
    history = ticker.history
    totals = history[history["date"] == pd.Timestamp(DAY)].iloc[0]
    assert len(trades) == totals["count"] == 177
    assert trades["volume"].sum() == totals["volume"] == 4872247


def test_trades_of_a_range_of_days(ticker, fake_api):
    result = ticker.get_trade_details(datetime.date(2026, 11, 19), DAY)
    # the 19th and 20th are not trading days
    assert list(result) == [datetime.date(2026, 11, 21), DAY]
    assert [call for call in fake_api.calls if call[0] == "trade_history"] == [
        ("trade_history", DIRAN, datetime.date(2026, 11, 21)),
        ("trade_history", DIRAN, DAY),
    ]
    # every trade has the day it was asked for
    first_day = result[datetime.date(2026, 11, 21)]
    assert first_day.index[0] == pd.Timestamp("2026-11-21 09:00:35")
    assert len(first_day) == 177


def test_trades_of_a_day_the_market_was_closed(ticker, fake_api):
    assert ticker.get_trade_details(datetime.date(2026, 11, 20)) == {}
    assert "trade_history" not in {call[0] for call in fake_api.calls}


def test_days_without_a_trade_are_left_out(ticker, fake_api, sample):
    canceled = sample("trade_history")
    for row in canceled["tradeHistory"]:
        row["canceled"] = 1
    fake_api.responses["trade_history"] = canceled
    assert ticker.get_trade_details(DAY) == {}
    fake_api.responses["trade_history"] = {"tradeHistory": []}
    assert ticker.get_trade_details(DAY) == {}


def test_repeated_and_canceled_trades_of_a_past_day_are_skipped(
    ticker, fake_api, sample
):
    data = sample("trade_history")
    rows = data["tradeHistory"]
    assert (rows[0]["nTran"], rows[0]["qTitTran"]) == (177, 5000)
    assert (rows[1]["nTran"], rows[1]["qTitTran"]) == (176, 500)
    rows[1]["canceled"] = 1
    rows.append(dict(rows[0]))
    fake_api.responses["trade_history"] = data

    trades = ticker.get_trade_details(DAY)[DAY]
    assert len(trades) == 176
    assert trades["volume"].sum() == 4872247 - 500


@pytest.mark.parametrize(
    "timeframe, candles",
    [
        ("30s", 57),
        ("1m", 52),
        ("5m", 30),
        ("10m", 18),
        ("15m", 13),
        ("30m", 7),
        ("1h", 4),
    ],
)
def test_candles_of_every_timeframe(ticker, timeframe, candles):
    frame = ticker.get_trade_details(DAY, timeframe=timeframe)[DAY]
    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert len(frame) == candles
    assert frame["volume"].sum() == 4872247
    assert frame.index.is_monotonic_increasing


def test_hourly_candles_of_a_past_day(ticker):
    candles = ticker.get_trade_details(DAY, timeframe="1h")[DAY]
    assert candles.index.name == "datetime"
    assert candles.index.tolist() == [
        pd.Timestamp("2026-11-22 09:00"),
        pd.Timestamp("2026-11-22 10:00"),
        pd.Timestamp("2026-11-22 11:00"),
        pd.Timestamp("2026-11-22 12:00"),
    ]
    # the price stayed at the upper limit the whole day
    assert candles.to_dict("list") == {
        "open": [23330.0] * 4,
        "high": [23330.0] * 4,
        "low": [23330.0] * 4,
        "close": [23330.0] * 4,
        "volume": [3828197, 30771, 970355, 42924],
    }
    assert str(candles["volume"].dtype) == "int64"
    assert (
        candles.dtypes[["open", "high", "low", "close"]] == "float64"
    ).all()


def a_trade(number: int, time: int, price: float, volume: int) -> dict:
    """A row of the trades of a day the way the api sends it."""
    return {
        "nTran": number,
        "hEven": time,
        "qTitTran": volume,
        "pTran": price,
        "canceled": 0,
    }


def test_candles_have_the_first_highest_lowest_and_last_price(
    ticker, fake_api
):
    fake_api.responses["trade_history"] = {
        "tradeHistory": [
            # newest first, like the api
            a_trade(5, 90300, 110.0, 5),
            a_trade(4, 90105, 95.0, 4),
            a_trade(3, 90050, 90.0, 3),
            a_trade(2, 90040, 120.0, 2),
            a_trade(1, 90010, 100.0, 1),
        ]
    }
    candles = ticker.get_trade_details(DAY, timeframe="1m")[DAY]
    # no candle for 09:02, nothing was traded in that minute
    assert candles.index.tolist() == [
        pd.Timestamp("2026-11-22 09:00"),
        pd.Timestamp("2026-11-22 09:01"),
        pd.Timestamp("2026-11-22 09:03"),
    ]
    assert candles.to_dict("list") == {
        "open": [100.0, 95.0, 110.0],
        "high": [120.0, 95.0, 110.0],
        "low": [90.0, 95.0, 110.0],
        "close": [90.0, 95.0, 110.0],
        "volume": [6, 4, 5],
    }


def test_unknown_timeframe_is_an_error(ticker, fake_api):
    with pytest.raises(ValueError, match="timeframe is not valid"):
        ticker.get_trade_details(DAY, timeframe="2m")
    assert fake_api.calls == []


def test_trades_of_several_days_in_one_frame(ticker):
    first_day = datetime.date(2026, 11, 21)
    result = ticker.get_trade_details(first_day, DAY, aggregate=True)
    assert list(result) == ["aggregate"]
    trades = result["aggregate"]
    assert list(trades.columns) == ["price", "volume"]
    assert len(trades) == 2 * 177
    assert trades.index.is_monotonic_increasing
    assert trades.index[0] == pd.Timestamp("2026-11-21 09:00:35")
    assert trades.index[-1] == pd.Timestamp("2026-11-22 12:27:24")


def test_candles_of_several_days_in_one_frame(ticker):
    first_day = datetime.date(2026, 11, 21)
    candles = ticker.get_trade_details(
        first_day, DAY, timeframe="1h", aggregate=True
    )["aggregate"]
    assert candles.index.tolist() == [
        pd.Timestamp(f"2026-11-{day} {hour}:00")
        for day in (21, 22)
        for hour in ("09", "10", "11", "12")
    ]
    assert candles["volume"].tolist() == [3828197, 30771, 970355, 42924] * 2


def test_trades_of_past_days_are_written_to_csv_files(ticker):
    first_day = datetime.date(2026, 11, 21)
    result = ticker.get_trade_details(first_day, DAY, to_csv=True)
    folder = Path("trade_details_history")
    assert sorted(path.name for path in folder.iterdir()) == [
        "trade_details_2026-11-21.csv",
        "trade_details_2026-11-22.csv",
    ]
    saved = pd.read_csv(
        folder / "trade_details_2026-11-22.csv",
        index_col="datetime",
        parse_dates=True,
    )
    assert list(saved.columns) == ["price", "volume"]
    assert saved.index.tolist() == result[DAY].index.tolist()
    assert saved["volume"].tolist() == result[DAY]["volume"].tolist()
    assert saved["price"].tolist() == result[DAY]["price"].tolist()


def test_candles_are_written_to_a_folder_of_the_caller(ticker, tmp_path):
    folder = tmp_path / "some" / "candles"
    ticker.get_trade_details(
        DAY, to_csv=True, base_path=str(folder), timeframe="1h"
    )
    [path] = folder.iterdir()
    assert path.name == "trade_details_2026-11-22.csv"
    assert path.read_text().splitlines() == [
        "datetime,open,high,low,close,volume",
        "2026-11-22 09:00:00,23330.0,23330.0,23330.0,23330.0,3828197",
        "2026-11-22 10:00:00,23330.0,23330.0,23330.0,23330.0,30771",
        "2026-11-22 11:00:00,23330.0,23330.0,23330.0,23330.0,970355",
        "2026-11-22 12:00:00,23330.0,23330.0,23330.0,23330.0,42924",
    ]
    assert not Path("trade_details_history").exists()


def test_aggregated_trades_are_written_to_one_csv_file(ticker, tmp_path):
    ticker.get_trade_details(
        datetime.date(2026, 11, 21),
        DAY,
        to_csv=True,
        base_path=str(tmp_path / "trades"),
        aggregate=True,
    )
    [path] = (tmp_path / "trades").iterdir()
    assert path.name == "trade_details_aggregate.csv"
    assert len(pd.read_csv(path)) == 2 * 177


def test_get_trade_details_of_a_symbol(fake_api, tmp_path):
    result = tse.get_trade_details(SYMBOL, DAY)
    assert list(result) == [DAY]
    assert len(result[DAY]) == 177
    assert ("trade_history", DIRAN, DAY) in fake_api.calls

    candles = tse.get_trade_details(
        symbol_name=SYMBOL,
        start_date=datetime.date(2026, 11, 21),
        end_date=DAY,
        to_csv=True,
        base_path=str(tmp_path / "out"),
        timeframe="30m",
        aggregate=True,
    )
    assert list(candles) == ["aggregate"]
    assert len(candles["aggregate"]) == 2 * 7
    assert [path.name for path in (tmp_path / "out").iterdir()] == [
        "trade_details_aggregate.csv"
    ]


# ---------------------------------------------------------------------------
# export


def test_ticker_real_time_data_to_csv(ticker):
    frame = tse.ticker_real_time_data_to_csv(ticker)
    assert len(frame) == 1
    row = frame.iloc[0].to_dict()
    assert isinstance(row.pop("date_time"), datetime.datetime)
    assert row == {
        "state": "مجاز",
        "last_price": 24020,
        "adj_close": 24020,
        "yesterday_price": 23330,
        "open_price": 24020,
        "high_price": 24020,
        "low_price": 24020,
        "count": 99,
        "volume": 860939,
        "value": 20679754780,
        "last_date": pd.Timestamp("2026-11-23 12:29:52"),
        "best_demand_vol": 31322288,
        "best_demand_price": 24020,
        "best_supply_vol": 294,
        "best_supply_price": 24070,
        "nav": None,
        "nav_date": None,
        "market_cap": 42755600000000.0,
        "individual_trade_summary.buy_vol": 860939.0,
        "individual_trade_summary.buy_count": 13.0,
        "individual_trade_summary.sell_vol": 703139.0,
        "individual_trade_summary.sell_count": 75.0,
        "corporate_trade_summary.buy_vol": 0.0,
        "corporate_trade_summary.buy_count": 0.0,
        "corporate_trade_summary.sell_vol": 157800.0,
        "corporate_trade_summary.sell_count": 1.0,
        "symbol": SYMBOL,
        "name": "ایران‌دارو",
        "group_name": "مواد و محصولات دارويي",
        "fiscal_year": "09/30",
        "eps": 3064.0,
        "p_e_ratio": pytest.approx(7.83943, abs=1e-5),
        "group_p_e_ratio": 11.85,
        "psr": 12734.175,
        "p_s_ratio": pytest.approx(1.88626, abs=1e-5),
        "base_volume": 1.0,
        "flow": "بورس",
        "sta_max": 24020.0,
        "sta_min": 22640.0,
        "min_week": 22000.0,
        "max_week": 24020.0,
        "min_year": 3633.0,
        "max_year": 24790.0,
        "month_average_volume": "18051688",
    }


def test_export_ticker_history_as_csv(ticker):
    frame = tse.export_ticker_history_as_csv(ticker)
    # the daily history and the client types of the same day in one row
    assert list(frame.columns) == HISTORY_COLUMNS + CLIENT_TYPES_COLUMNS[1:]
    assert len(frame) == 60
    assert frame["date"].is_monotonic_increasing
    day = frame[frame["date"] == pd.Timestamp(DAY)].iloc[0]
    assert day["adjClose"] == 23330.0
    assert day["volume"] == 4872247
    assert day["count"] == 177
    assert day["individual_buy_vol"] == 4772247
    assert day["corporate_buy_vol"] == 100000
    assert day["individual_ownership_change"] == 4287826.0


def test_export_keeps_the_days_only_one_of_the_two_histories_has(
    ticker, fake_api, sample
):
    client_types = sample("client_type_history")
    newest = client_types["clientType"].pop(0)
    assert newest["recDate"] == 20261123
    client_types["clientType"].append({**newest, "recDate": 20260831})
    fake_api.responses["client_type_history"] = client_types

    frame = tse.export_ticker_history_as_csv(ticker)
    assert len(frame) == 61
    # a day with client types and no prices
    first = frame.iloc[0]
    assert first["date"] == pd.Timestamp("2026-08-31")
    assert math.isnan(first["adjClose"])
    assert first["individual_buy_vol"] == 860939
    # a day with prices and no client types
    last = frame.iloc[-1]
    assert last["date"] == pd.Timestamp(LAST_DAY)
    assert last["adjClose"] == 24020.0
    assert math.isnan(last["individual_buy_vol"])
