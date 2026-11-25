"""Tests of pytse_client.orderbook: get_orderbook on the saved changes of
the order book of دیران, from 06:01 to 09:05 of 2026-11-22."""

import datetime
from pathlib import Path

import pandas as pd
import pytest

import pytse_client as tse

SYMBOL = "دیران"
DIRAN = "69090868458637360"
DAY = datetime.date(2026, 11, 22)
KEY = "2026-11-22"

# columns of the full order book: the six numbers of each of the 5 levels
BOOK_COLUMNS = [
    f"{name}_{level}"
    for level in (1, 2, 3, 4, 5)
    for name in ("bid", "ask", "vol_bid", "vol_ask", "num_bid", "num_ask")
]

CHANGE_COLUMNS = [
    "depth",
    "bid",
    "ask",
    "vol_bid",
    "vol_ask",
    "num_bid",
    "num_ask",
]


def test_full_order_book_of_a_day(fake_api):
    result = tse.get_orderbook(SYMBOL, DAY, to_csv=True)
    assert list(result) == [KEY]
    book = result[KEY]
    assert ("best_limits_history", DIRAN, DAY) in fake_api.calls
    assert list(book.columns) == BOOK_COLUMNS
    # one row for every time the order book changed
    assert len(book) == 475
    assert book.index.is_monotonic_increasing
    assert book.index.is_unique
    assert book.index[0] == pd.Timestamp("2026-11-22 06:01:30")
    assert book.index[-1] == pd.Timestamp("2026-11-22 09:04:55")
    # the first answer of the day has all five levels
    assert book.iloc[0].to_dict() == {
        "bid_1": 22660.0,
        "ask_1": 23150.0,
        "vol_bid_1": 11327,
        "vol_ask_1": 1000,
        "num_bid_1": 5,
        "num_ask_1": 1,
        "bid_2": 22000.0,
        "ask_2": 23860.0,
        "vol_bid_2": 228,
        "vol_ask_2": 1331,
        "num_bid_2": 1,
        "num_ask_2": 2,
        "bid_3": 21520.0,
        "ask_3": 24070.0,
        "vol_bid_3": 500,
        "vol_ask_3": 294,
        "num_bid_3": 1,
        "num_ask_3": 1,
        "bid_4": 20720.0,
        "ask_4": 24790.0,
        "vol_bid_4": 242,
        "vol_ask_4": 6848,
        "num_bid_4": 1,
        "num_ask_4": 6,
        "bid_5": 18750.0,
        "ask_5": 0.0,
        "vol_bid_5": 500,
        "vol_ask_5": 0,
        "num_bid_5": 1,
        "num_ask_5": 0,
    }
    # the last change is of level 1 only, the other levels keep the last
    # state they had
    assert book.iloc[-1].to_dict() == {
        "bid_1": 23330.0,
        "ask_1": 23860.0,
        "vol_bid_1": 68523552,
        "vol_ask_1": 1331,
        "num_bid_1": 876,
        "num_ask_1": 2,
        "bid_2": 22660.0,
        "ask_2": 24070.0,
        "vol_bid_2": 320592,
        "vol_ask_2": 294,
        "num_bid_2": 25,
        "num_ask_2": 1,
        "bid_3": 22500.0,
        "ask_3": 24790.0,
        "vol_bid_3": 16000,
        "vol_ask_3": 6848,
        "num_bid_3": 1,
        "num_ask_3": 6,
        "bid_4": 22350.0,
        "ask_4": 0.0,
        "vol_bid_4": 100000,
        "vol_ask_4": 0,
        "num_bid_4": 1,
        "num_ask_4": 0,
        "bid_5": 22330.0,
        "ask_5": 0.0,
        "vol_bid_5": 5690,
        "vol_ask_5": 0,
        "num_bid_5": 1,
        "num_ask_5": 0,
    }
    assert not book.isna().any().any()

    [path] = Path("orderbook_hist_data").iterdir()
    assert path.name == "organized_orderbook_2026-11-22.csv"
    saved = pd.read_csv(path, index_col=0, parse_dates=True)
    assert list(saved.columns) == BOOK_COLUMNS
    assert saved.index.tolist() == book.index.tolist()
    assert saved["vol_bid_1"].tolist() == book["vol_bid_1"].tolist()


def test_changes_of_the_order_book_of_a_day(fake_api, tmp_path):
    folder = tmp_path / "some" / "books"
    result = tse.get_orderbook(
        SYMBOL,
        start_date=DAY,
        end_date=DAY,
        to_csv=True,
        base_path=str(folder),
        diff_orderbook=True,
        async_requests=False,
    )
    assert list(result) == [KEY]
    changes = result[KEY]
    assert ("best_limits_history", DIRAN, DAY) in fake_api.calls
    assert list(changes.columns) == CHANGE_COLUMNS
    assert changes.index.name == "datetime"
    # one row for every change of a level
    assert len(changes) == 533
    assert changes["depth"].value_counts().to_dict() == {
        1: 473,
        2: 36,
        4: 10,
        5: 8,
        3: 6,
    }
    # ordered by time, then by level
    assert changes.index.is_monotonic_increasing
    assert changes["depth"].tolist()[:5] == [1, 2, 3, 4, 5]
    assert changes.iloc[0].to_dict() == {
        "depth": 1,
        "bid": 22660.0,
        "ask": 23150.0,
        "vol_bid": 11327,
        "vol_ask": 1000,
        "num_bid": 5,
        "num_ask": 1,
    }
    assert changes.index[-1] == pd.Timestamp("2026-11-22 09:04:55")
    assert changes.iloc[-1].to_dict() == {
        "depth": 1,
        "bid": 23330.0,
        "ask": 23860.0,
        "vol_bid": 68523552,
        "vol_ask": 1331,
        "num_bid": 876,
        "num_ask": 2,
    }
    assert (changes.dtypes[["bid", "ask"]] == "float64").all()
    whole_numbers = ["depth", "vol_bid", "vol_ask", "num_bid", "num_ask"]
    assert (changes.dtypes[whole_numbers] == "int64").all()

    [path] = folder.iterdir()
    assert path.name == "organized_orderbook_2026-11-22.csv"
    assert path.read_text().splitlines()[:3] == [
        "datetime,depth,bid,ask,vol_bid,vol_ask,num_bid,num_ask",
        "2026-11-22 06:01:30,1,22660.0,23150.0,11327,1000,5,1",
        "2026-11-22 06:01:30,2,22000.0,23860.0,228,1331,1,2",
    ]
    assert not Path("orderbook_hist_data").exists()


def a_change(time: int, level: int, bid: float, bid_volume: int) -> dict:
    """A change of a level of the order book the way the api sends it,
    with the same sell side every time."""
    return {
        "hEven": time,
        "refID": time,
        "number": level,
        "zOrdMeDem": 1,
        "qTitMeDem": bid_volume,
        "pMeDem": bid,
        "pMeOf": 110.0,
        "qTitMeOf": 20,
        "zOrdMeOf": 2,
    }


def test_order_book_of_a_range_of_days_keeps_the_last_state_of_a_level(
    fake_api,
):
    fake_api.responses["best_limits_history"] = {
        "bestLimitsHistory": [
            a_change(90000, level=1, bid=100.0, bid_volume=10),
            a_change(90000, level=2, bid=90.0, bid_volume=5),
            a_change(90005, level=1, bid=101.0, bid_volume=15),
            a_change(90010, level=2, bid=95.0, bid_volume=5),
        ]
    }
    # 2026-11-19 and 20 are not trading days, they can only be the start
    # of a range when the dates are not checked
    result = tse.get_orderbook(
        SYMBOL,
        datetime.date(2026, 11, 19),
        DAY,
        ignore_date_validation=True,
    )
    assert list(result) == ["2026-11-21", KEY]
    asked = [
        call for call in fake_api.calls if call[0] == "best_limits_history"
    ]
    assert asked == [
        ("best_limits_history", DIRAN, datetime.date(2026, 11, 21)),
        ("best_limits_history", DIRAN, DAY),
    ]
    assert result["2026-11-21"].index.tolist() == [
        pd.Timestamp("2026-11-21 09:00:00"),
        pd.Timestamp("2026-11-21 09:00:05"),
        pd.Timestamp("2026-11-21 09:00:10"),
    ]
    book = result[KEY]
    assert book.index.tolist() == [
        pd.Timestamp("2026-11-22 09:00:00"),
        pd.Timestamp("2026-11-22 09:00:05"),
        pd.Timestamp("2026-11-22 09:00:10"),
    ]
    assert book[["bid_1", "vol_bid_1", "bid_2", "ask_2"]].to_dict("list") == {
        "bid_1": [100.0, 101.0, 101.0],
        "vol_bid_1": [10, 15, 15],
        "bid_2": [90.0, 90.0, 95.0],
        "ask_2": [110.0, 110.0, 110.0],
    }
    # the levels that never changed have no value
    assert book[BOOK_COLUMNS[12:]].isna().all().all()


def test_day_without_a_change_has_an_empty_order_book(fake_api):
    fake_api.responses["best_limits_history"] = {"bestLimitsHistory": []}
    book = tse.get_orderbook(SYMBOL, DAY)[KEY]
    assert list(book.columns) == BOOK_COLUMNS
    assert book.empty


@pytest.mark.parametrize(
    "start, end, not_traded",
    [
        (datetime.date(2026, 11, 20), None, "2026-11-20"),
        (datetime.date(2026, 11, 20), DAY, "2026-11-20"),
        (
            datetime.date(2026, 11, 18),
            datetime.date(2026, 11, 19),
            "2026-11-19",
        ),
    ],
)
def test_start_and_end_must_be_trading_days(fake_api, start, end, not_traded):
    with pytest.raises(
        Exception, match=f"{not_traded} is not a valid trade day"
    ):
        tse.get_orderbook(SYMBOL, start, end)
    assert "best_limits_history" not in {call[0] for call in fake_api.calls}


def test_unknown_symbol_is_an_error():
    with pytest.raises(ValueError, match="Symbol ناموجود not found"):
        tse.get_orderbook("ناموجود", DAY)
