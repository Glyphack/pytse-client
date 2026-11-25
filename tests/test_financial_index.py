"""Tests of pytse_client.financial_index: FinancialIndex on the saved
responses of the index شاخص کل."""

import datetime
from pathlib import Path

import jdatetime
import pandas as pd
import pytest

import pytse_client as tse

# the name with the Arabic ك of the website, the way the package saves it
NAME = "شاخص كل"
TOTAL_INDEX = "32097828799138957"


@pytest.fixture
def index() -> tse.FinancialIndex:
    return tse.FinancialIndex(NAME)


def test_financial_index_of_a_name(index, fake_api):
    assert index.symbol == NAME
    # nothing is asked or written before it is needed
    assert fake_api.calls == []
    assert list(Path.cwd().iterdir()) == []


def test_name_with_persian_letters(fake_api):
    # ک and ی in place of the ك and ي of the website
    index = tse.FinancialIndex("شاخص کل")
    assert index.symbol == NAME
    assert index.last_value == 8389814.07
    assert fake_api.calls == [("index_intraday", TOTAL_INDEX)]


def test_another_index_is_asked_with_its_own_code(fake_api):
    assert tse.FinancialIndex("شاخص قيمت 50 شركت").low == 8380810.01
    assert fake_api.calls == [("index_intraday", "69932667409721265")]


def test_financial_index_of_a_code(fake_api):
    index = tse.FinancialIndex(symbol="", index=TOTAL_INDEX)
    assert index.symbol == TOTAL_INDEX
    assert index.last_value == 8389814.07
    assert len(index.history) == 60
    assert fake_api.calls == [
        ("index_intraday", TOTAL_INDEX),
        ("index_history", TOTAL_INDEX),
    ]


def test_unknown_name_is_an_error():
    with pytest.raises(ValueError, match="Financial index ناموجود not found"):
        tse.FinancialIndex("ناموجود")


def test_last_values_of_the_day(index):
    assert index.last_update == "19:04"
    assert index.last_value == 8389814.07
    assert index.high == 8447267.19
    assert index.low == 8380810.01


def test_last_values_are_the_ones_of_the_newest_row(index, fake_api, sample):
    intraday = sample("index_intraday")
    intraday["indexB1"].reverse()
    fake_api.responses["index_intraday"] = intraday
    assert index.last_update == "19:04"
    assert index.last_value == 8389814.07


def test_intraday_values(index, fake_api):
    intraday = index.intraday_price
    assert fake_api.calls == [("index_intraday", TOTAL_INDEX)]
    assert list(intraday.columns) == [
        "value",
        "change_percentage",
        "low",
        "high",
    ]
    assert intraday.index.name == "time"
    assert len(intraday) == 126
    assert intraday.index[0] == datetime.time(8, 30)
    assert intraday.index[-1] == datetime.time(19, 4, 23)
    assert intraday.index.is_monotonic_increasing
    # before the market opens the low and high of the day are 0
    assert intraday.iloc[0].to_dict() == {
        "value": 8327077.7,
        "change_percentage": 0.0,
        "low": 0.0,
        "high": 0.0,
    }
    assert intraday.iloc[-1].to_dict() == {
        "value": 8389814.07,
        "change_percentage": 0.7534,
        "low": 8380810.01,
        "high": 8447267.19,
    }
    assert (intraday.dtypes == "float64").all()


def test_index_without_values_today(index, fake_api):
    fake_api.responses["index_intraday"] = {"indexB1": []}
    for name in ("last_update", "last_value", "high", "low"):
        with pytest.raises(RuntimeError, match="no intraday data"):
            getattr(index, name)
    assert index.intraday_price.empty


def test_history(index, fake_api):
    history = index.history
    assert list(history.columns) == ["date", "high", "low", "close", "jdate"]
    assert len(history) == 60
    # oldest day first
    assert history.iloc[0].to_dict() == {
        "date": pd.Timestamp("2026-09-01"),
        "high": 6699460.0,
        "low": 6583930.0,
        "close": 6583932.3,
        "jdate": jdatetime.date(1405, 6, 10),
    }
    assert history.iloc[-1].to_dict() == {
        "date": pd.Timestamp("2026-11-23"),
        "high": 8447260.0,
        "low": 8380810.0,
        "close": 8389814.1,
        "jdate": jdatetime.date(1405, 9, 2),
    }
    # loaded once and not written unless asked
    assert index.history is history
    assert fake_api.calls == [("index_history", TOTAL_INDEX)]
    assert list(Path.cwd().iterdir()) == []


def test_history_is_written_to_a_csv_file_when_asked(tmp_path):
    history = tse.FinancialIndex(NAME, write_history=True).history
    [path] = Path("financial_index_data").iterdir()
    assert path.name == "شاخص كل.csv"
    saved = pd.read_csv(path)
    assert list(saved.columns) == ["date", "high", "low", "close", "jdate"]
    assert saved["close"].tolist() == history["close"].tolist()
    assert saved["jdate"].iloc[-1] == "1405-09-02"

    folder = tmp_path / "some" / "indexes"
    _ = tse.FinancialIndex(
        NAME, base_path=str(folder), write_history=True
    ).history
    assert [path.name for path in folder.iterdir()] == ["شاخص كل.csv"]


def test_contributing_symbols(index, fake_api):
    # the symbols have the Persian ی and ک
    assert index.contributing_symbols == [
        {"symbol": "خودرو", "index": "65883838195688438"},
        {"symbol": "دیران", "index": "69090868458637360"},
        {"symbol": "شستا", "index": "2400322364771558"},
        {"symbol": "فولاد", "index": "46348559193224090"},
    ]
    _ = index.contributing_symbols
    assert fake_api.calls == [("index_companies", TOTAL_INDEX)]
