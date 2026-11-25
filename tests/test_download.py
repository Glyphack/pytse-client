"""Tests of pytse_client.download: the daily history of symbols and
financial indexes and the client types history, on saved responses."""

import json
import logging
from pathlib import Path

import jdatetime
import pandas as pd
import pytest

import pytse_client as tse
from pytse_client import symbols_data
from pytse_client.download import adjust_price

SYMBOL = "دیران"
DIRAN = "69090868458637360"
FOLAD = "46348559193224090"
INDEX_NAME = "شاخص كل"
TOTAL_INDEX = "32097828799138957"

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


def asked(fake_api, endpoint: str) -> list:
    """The first argument of every call of an endpoint, sorted: the
    downloads run in threads, so the order of the calls changes."""
    return sorted(call[1] for call in fake_api.calls if call[0] == endpoint)


# ---------------------------------------------------------------------------
# download


def test_download_a_symbol(fake_api):
    result = tse.download(SYMBOL)
    assert list(result) == [SYMBOL]
    history = result[SYMBOL]
    assert list(history.columns) == HISTORY_COLUMNS
    assert len(history) == 60
    # oldest day first
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
    assert history.iloc[1].to_dict() == {
        "date": pd.Timestamp("2026-09-02"),
        "open": 15100.0,
        "high": 15920.0,
        "low": 15100.0,
        # قیمت پایانی and آخرین معامله of the day
        "adjClose": 15470.0,
        "value": 422376430710,
        "volume": 27307330,
        "count": 782,
        "yesterday": 15460.0,
        "close": 15920.0,
    }
    assert history["date"].iloc[-1] == pd.Timestamp("2026-11-23")
    assert history["date"].is_monotonic_increasing
    assert pd.api.types.is_datetime64_any_dtype(history["date"])
    prices = ["open", "high", "low", "adjClose", "yesterday", "close"]
    assert (history.dtypes[prices] == "float64").all()
    assert (history.dtypes[["value", "volume", "count"]] == "int64").all()
    assert fake_api.calls == [("closing_price_daily_list", DIRAN)]
    # nothing is written unless asked
    assert list(Path.cwd().iterdir()) == []


def test_download_writes_a_csv_file_per_symbol():
    tse.download([SYMBOL, "فولاد"], write_to_csv=True)
    folder = Path("tickers_data")
    assert sorted(path.name for path in folder.iterdir()) == [
        "دیران.csv",
        "فولاد.csv",
    ]
    saved = pd.read_csv(folder / "دیران.csv")
    assert list(saved.columns) == HISTORY_COLUMNS
    assert len(saved) == 60
    assert saved.iloc[-1].to_dict() == {
        "date": "2026-11-23",
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


def test_download_writes_to_a_folder_of_the_caller(tmp_path):
    folder = tmp_path / "some" / "folder"
    tse.download(SYMBOL, write_to_csv=True, base_path=str(folder))
    assert [path.name for path in folder.iterdir()] == ["دیران.csv"]
    assert not Path("tickers_data").exists()


def test_download_with_jalali_dates():
    history = tse.download(SYMBOL, include_jdate=True)[SYMBOL]
    assert list(history.columns) == [*HISTORY_COLUMNS, "jdate"]
    assert history["jdate"].iloc[0] == jdatetime.date(1405, 6, 10)
    assert history["jdate"].iloc[-1] == jdatetime.date(1405, 9, 2)


@pytest.mark.parametrize("symbols", [[SYMBOL, "فولاد"], {SYMBOL, "فولاد"}])
def test_download_several_symbols(fake_api, symbols):
    result = tse.download(symbols)
    assert set(result) == {SYMBOL, "فولاد"}
    assert len(result[SYMBOL]) == 60
    assert len(result["فولاد"]) == 60
    assert asked(fake_api, "closing_price_daily_list") == [FOLAD, DIRAN]


def test_download_accepts_arabic_letters_and_spaces(fake_api):
    # ي and ك of the website in place of the Persian ی and ک
    result = tse.download(" ديران ")
    assert list(result) == [SYMBOL]
    assert fake_api.calls == [("closing_price_daily_list", DIRAN)]


def test_download_includes_the_history_of_old_indexes(symbols_file, fake_api):
    symbols = {
        "شکبیر": {"index": "2", "code": "", "name": "", "old": ["1"]},
        # the index of a deleted symbol is in its own old list
        "حذفی": {"index": "4", "code": "", "name": "", "old": ["4", "3"]},
    }
    symbols_file.write_text(json.dumps(symbols), encoding="utf8")

    result = tse.download("شكبير")
    assert list(result) == ["شکبیر"]
    assert asked(fake_api, "closing_price_daily_list") == ["1", "2"]
    # the days of both instruments in one frame, ordered by day
    history = result["شکبیر"]
    assert len(history) == 120
    assert history["date"].is_monotonic_increasing
    assert history.index.tolist() == list(range(120))

    fake_api.calls.clear()
    assert len(tse.download("حذفی")["حذفی"]) == 120
    assert asked(fake_api, "closing_price_daily_list") == ["3", "4"]


def test_download_by_the_code_of_an_instrument(fake_api):
    result = tse.download("25165947991415904")
    assert list(result) == ["25165947991415904"]
    assert len(result["25165947991415904"]) == 60
    assert fake_api.calls == [
        ("closing_price_daily_list", "25165947991415904")
    ]


def test_download_all_symbols(symbols_file, fake_api):
    result = tse.download("all", write_to_csv=True)
    # the temporary symbols file has one symbol
    assert list(result) == ["فولاد"]
    assert fake_api.calls == [("closing_price_daily_list", FOLAD)]
    assert Path("tickers_data/فولاد.csv").exists()


def test_download_looks_an_unknown_symbol_up_and_remembers_it(
    symbols_file, fake_api
):
    assert symbols_data.get_ticker_index(SYMBOL) is None

    result = tse.download(SYMBOL)
    assert len(result[SYMBOL]) == 60
    assert fake_api.calls == [
        ("instrument_search", SYMBOL),
        ("instrument_info", DIRAN),
        ("closing_price_daily_list", DIRAN),
    ]
    found = {
        "index": DIRAN,
        "code": "IRO1IRDR0001",
        "name": "ایراندارو",
        "old": [],
    }
    assert symbols_data.symbols_information()[SYMBOL] == found
    saved = json.loads(symbols_file.read_text(encoding="utf8"))
    assert list(saved) == ["فولاد", SYMBOL]
    assert saved[SYMBOL] == found

    # the next download does not search again
    fake_api.calls.clear()
    tse.download(SYMBOL)
    assert fake_api.calls == [("closing_price_daily_list", DIRAN)]


def test_download_of_a_symbol_the_search_does_not_find(symbols_file, fake_api):
    before = symbols_file.read_text(encoding="utf8")
    with pytest.raises(Exception, match="Cannot find symbol: ناموجود"):
        tse.download("ناموجود")
    assert fake_api.calls == [("instrument_search", "ناموجود")]
    assert symbols_file.read_text(encoding="utf8") == before


def test_download_skips_a_symbol_that_was_never_traded(
    fake_api, capsys, caplog
):
    fake_api.responses["closing_price_daily_list"] = {"closingPriceDaily": []}
    with caplog.at_level(logging.ERROR, logger="pytse"):
        assert tse.download(SYMBOL) == {}
    assert "Cannot read daily trade records for symbol: دیران" in caplog.text
    assert "download did not complete" in capsys.readouterr().out


def a_day(day: int, yesterday: float, price: float) -> dict:
    """A row of the daily history the way the api sends it, with one
    price for the whole day."""
    return {
        "dEven": day,
        "priceFirst": price,
        "priceMax": price,
        "priceMin": price,
        "pClosing": price,
        "pDrCotVal": price,
        "priceYesterday": yesterday,
        "zTotTran": 10.0,
        "qTotTran5J": 1000.0,
        "qTotCap": 1000.0 * price,
    }


# a history with two capital increases: the price of "yesterday" on
# 2026-01-02 and 2026-01-04 is not the closing price of the day before.
# Newest day first, like the api.
TWO_CAPITAL_INCREASES = {
    "closingPriceDaily": [
        a_day(20260105, yesterday=300.0, price=400.0),
        a_day(20260104, yesterday=200.0, price=300.0),
        a_day(20260103, yesterday=600.0, price=800.0),
        a_day(20260102, yesterday=500.0, price=600.0),
        a_day(20260101, yesterday=800.0, price=1000.0),
    ]
}


def test_download_adjusted_prices(fake_api):
    fake_api.responses["closing_price_daily_list"] = TWO_CAPITAL_INCREASES

    history = tse.download(SYMBOL)[SYMBOL]
    assert history["adjClose"].tolist() == [1000.0, 600.0, 800.0, 300.0, 400.0]

    adjusted = tse.download(SYMBOL, adjust=True)[SYMBOL]
    # 200 / 800 for the days before the second increase, and that times
    # 500 / 1000 for the day before the first one
    assert adjusted["adjClose"].tolist() == [125.0, 150.0, 200.0, 300.0, 400.0]
    assert adjusted["yesterday"].tolist() == [
        100.0,
        125.0,
        150.0,
        200.0,
        300.0,
    ]
    for column in ("open", "high", "low", "close"):
        assert adjusted[column].tolist() == adjusted["adjClose"].tolist()
    # every adjusted day starts at the closing price of the day before
    assert (
        adjusted["yesterday"].tolist()[1:]
        == adjusted["adjClose"].tolist()[:-1]
    )
    # only prices are adjusted
    for column in ("date", "value", "volume", "count"):
        assert adjusted[column].tolist() == history[column].tolist()


def test_download_adjusted_prices_of_a_history_without_an_increase():
    adjusted = tse.download(SYMBOL, adjust=True)[SYMBOL]
    pd.testing.assert_frame_equal(adjusted, tse.download(SYMBOL)[SYMBOL])


def test_download_writes_adjusted_prices_to_their_own_file(fake_api):
    fake_api.responses["closing_price_daily_list"] = TWO_CAPITAL_INCREASES
    tse.download(SYMBOL, write_to_csv=True, adjust=True)
    [path] = Path("tickers_data").iterdir()
    assert path.name == "دیران-ت.csv"
    assert pd.read_csv(path)["adjClose"].tolist() == [
        125.0,
        150.0,
        200.0,
        300.0,
        400.0,
    ]


def test_adjust_price_leaves_frames_it_cannot_adjust():
    empty = pd.DataFrame(columns=HISTORY_COLUMNS)
    assert adjust_price(empty) is empty
    # the rows must be numbered from 0, the way download returns them
    history = tse.download(SYMBOL)[SYMBOL].set_index("date")
    assert adjust_price(history) is history


# ---------------------------------------------------------------------------
# download_financial_indexes


def test_download_a_financial_index(fake_api):
    # the Persian ک is the Arabic ك of the names of the website
    result = tse.download_financial_indexes("شاخص کل")
    assert list(result) == [INDEX_NAME]
    history = result[INDEX_NAME]
    assert fake_api.calls == [("index_history", TOTAL_INDEX)]
    assert list(history.columns) == ["date", "high", "low", "close"]
    assert len(history) == 60
    assert history.iloc[0].to_dict() == {
        "date": pd.Timestamp("2026-09-01"),
        "high": 6699460.0,
        "low": 6583930.0,
        "close": 6583932.3,
    }
    assert history.iloc[-1].to_dict() == {
        "date": pd.Timestamp("2026-11-23"),
        "high": 8447260.0,
        "low": 8380810.0,
        "close": 8389814.1,
    }
    assert history["date"].is_monotonic_increasing
    assert (history.dtypes[["high", "low", "close"]] == "float64").all()
    assert list(Path.cwd().iterdir()) == []


def test_download_a_financial_index_with_jalali_dates_to_a_csv_file(tmp_path):
    history = tse.download_financial_indexes(
        INDEX_NAME, write_to_csv=True, include_jdate=True
    )[INDEX_NAME]
    assert list(history.columns) == ["date", "high", "low", "close", "jdate"]
    assert history["jdate"].iloc[0] == jdatetime.date(1405, 6, 10)
    [path] = Path("financial_index_data").iterdir()
    assert path.name == "شاخص كل.csv"
    assert path.read_text(encoding="utf8").splitlines()[:2] == [
        "date,high,low,close,jdate",
        "2026-09-01,6699460.0,6583930.0,6583932.3,1405-06-10",
    ]

    folder = tmp_path / "indexes"
    tse.download_financial_indexes(
        INDEX_NAME, write_to_csv=True, base_path=str(folder)
    )
    assert [path.name for path in folder.iterdir()] == ["شاخص كل.csv"]


def test_download_a_financial_index_by_its_code(fake_api):
    result = tse.download_financial_indexes("43685683301327984")
    assert list(result) == ["43685683301327984"]
    assert fake_api.calls == [("index_history", "43685683301327984")]


def test_download_several_financial_indexes(fake_api):
    result = tse.download_financial_indexes([INDEX_NAME, "شاخص صنعت"])
    assert set(result) == {INDEX_NAME, "شاخص صنعت"}
    assert len(asked(fake_api, "index_history")) == 2
    assert TOTAL_INDEX in asked(fake_api, "index_history")


def test_download_all_financial_indexes(fake_api):
    result = tse.download_financial_indexes("all")
    assert set(result) == symbols_data.all_financial_index()
    assert len(result) == len(fake_api.calls) == 70
    assert all(len(history) == 60 for history in result.values())


def test_download_an_unknown_financial_index(fake_api):
    with pytest.raises(
        Exception, match="Cannot find financial index: ناموجود"
    ):
        tse.download_financial_indexes("ناموجود")
    assert fake_api.calls == []


def test_download_a_financial_index_without_a_history(fake_api):
    fake_api.responses["index_history"] = {"indexB2": []}
    with pytest.raises(ValueError, match="Expected valid financial index"):
        tse.download_financial_indexes(INDEX_NAME)


# ---------------------------------------------------------------------------
# download_client_types_records


def test_download_client_types_of_a_symbol(fake_api):
    result = tse.download_client_types_records(SYMBOL)
    assert list(result) == [SYMBOL]
    records = result[SYMBOL]
    assert fake_api.calls == [("client_type_history", DIRAN)]
    assert list(records.columns) == CLIENT_TYPES_COLUMNS
    assert len(records) == 60
    # newest day first
    assert records.iloc[0].to_dict() == {
        "date": pd.Timestamp("2026-11-23"),
        "individual_buy_count": 13,
        "corporate_buy_count": 0,
        "individual_sell_count": 75,
        "corporate_sell_count": 1,
        "individual_buy_vol": 860939,
        "corporate_buy_vol": 0,
        "individual_sell_vol": 703139,
        "corporate_sell_vol": 157800,
        "individual_buy_value": 20679754780,
        "corporate_buy_value": 0,
        "individual_sell_value": 16889398780,
        "corporate_sell_value": 3790356000,
        "individual_buy_mean_price": 24020.0,
        "individual_sell_mean_price": 24020.0,
        # corporations bought nothing that day
        "corporate_buy_mean_price": pytest.approx(float("nan"), nan_ok=True),
        "corporate_sell_mean_price": 24020.0,
        "individual_ownership_change": 157800.0,
    }
    assert records["date"].iloc[-1] == pd.Timestamp("2026-09-01")
    assert pd.api.types.is_datetime64_any_dtype(records["date"])
    assert (records.dtypes[CLIENT_TYPES_COLUMNS[1:13]] == "int64").all()
    assert (records.dtypes[CLIENT_TYPES_COLUMNS[13:]] == "float64").all()
    assert list(Path.cwd().iterdir()) == []


def test_download_client_types_with_jalali_dates_to_a_csv_file(tmp_path):
    records = tse.download_client_types_records(
        SYMBOL, write_to_csv=True, include_jdate=True
    )[SYMBOL]
    assert list(records.columns) == [*CLIENT_TYPES_COLUMNS, "jdate"]
    assert records["jdate"].iloc[0] == jdatetime.date(1405, 9, 2)
    [path] = Path("client_types_data").iterdir()
    assert path.name == "دیران.csv"
    saved = pd.read_csv(path, index_col=0)
    assert list(saved.columns) == [*CLIENT_TYPES_COLUMNS, "jdate"]
    assert saved["date"].iloc[0] == "2026-11-23"
    assert saved["jdate"].iloc[0] == "1405-09-02"
    assert saved["individual_buy_vol"].iloc[0] == 860939

    folder = tmp_path / "client types"
    tse.download_client_types_records(
        SYMBOL, write_to_csv=True, base_path=str(folder)
    )
    assert [path.name for path in folder.iterdir()] == ["دیران.csv"]


def test_download_client_types_of_several_symbols(fake_api):
    result = tse.download_client_types_records(["ديران", "فولاد"])
    assert set(result) == {SYMBOL, "فولاد"}
    assert asked(fake_api, "client_type_history") == [FOLAD, DIRAN]


def test_download_client_types_of_all_symbols(symbols_file, fake_api):
    result = tse.download_client_types_records("all")
    assert list(result) == ["فولاد"]
    assert fake_api.calls == [("client_type_history", FOLAD)]


def test_download_client_types_looks_an_unknown_symbol_up(
    symbols_file, fake_api
):
    result = tse.download_client_types_records(SYMBOL)
    assert len(result[SYMBOL]) == 60
    assert fake_api.calls == [
        ("instrument_search", SYMBOL),
        ("instrument_info", DIRAN),
        ("client_type_history", DIRAN),
    ]
    assert symbols_data.get_ticker_index(SYMBOL) == DIRAN
    assert SYMBOL in json.loads(symbols_file.read_text(encoding="utf8"))


def test_download_client_types_of_a_symbol_the_search_does_not_find(
    symbols_file,
):
    with pytest.raises(Exception, match="Cannot find symbol: ناموجود"):
        tse.download_client_types_records("ناموجود")


def test_download_client_types_skips_a_symbol_without_records(
    fake_api, capsys
):
    fake_api.responses["client_type_history"] = {"clientType": []}
    assert tse.download_client_types_records(SYMBOL) == {}
    assert "could not download client types" in capsys.readouterr().out
