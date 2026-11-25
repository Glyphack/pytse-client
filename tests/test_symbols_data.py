"""Tests of pytse_client.symbols_data: the symbols and financial indexes
that come with the package, and the lookup of a missing symbol."""

import json
import logging
from dataclasses import astuple

import pytest
import requests

from pytse_client import symbols_data
from pytse_client.symbols_data import MarketSymbol
from pytse_client.tsetmc_api.instrument import parse_instrument_search

FOLAD = "46348559193224090"
DIRAN = "69090868458637360"
# the symbol دیران the way the saved search and instrument info give it
DIRAN_SYMBOL = MarketSymbol(
    code="IRO1IRDR0001",
    symbol="دیران",
    name="ایراندارو",
    index=DIRAN,
    old=[],
)
# a deleted instrument of the saved search for دیران
DELETED = "14058161288052046"
# a search answer with two active instruments and a deleted one of the
# symbol آبادا, and a deleted instrument of another symbol
ABADA_SEARCH = {
    "instrumentSearch": [
        {"insCode": "1", "lVal18AFC": "آبادا", "lastDate": 1},
        {"insCode": "2", "lVal18AFC": "آبادا", "lastDate": 0},
        {"insCode": "3", "lVal18AFC": "آباداح", "lastDate": 0},
        {"insCode": "4", "lVal18AFC": "آبادا", "lastDate": 1},
    ]
}


def test_index_of_a_symbol():
    assert symbols_data.get_ticker_index("فولاد") == FOLAD
    assert symbols_data.get_ticker_index("وبملت") == "778253364357513"
    assert symbols_data.get_ticker_index("ناموجود") is None


def test_symbols_information():
    info = symbols_data.symbols_information()
    assert len(info) > 1000
    assert info["فولاد"] == {
        "index": FOLAD,
        "code": "IRO1FOLD0001",
        "name": "فولاد مبارکه اصفهان",
        "old": [],
    }
    for value in info.values():
        assert set(value) == {"index", "code", "name", "old"}
        assert value["index"].isdigit()
    # the file is read once
    assert symbols_data.symbols_information() is info


def test_symbols_and_names_have_persian_letters():
    for symbol, value in symbols_data.symbols_information().items():
        text = symbol + value["name"]
        # no ي and ك of the website, and no zero width non-joiner in names
        assert "ي" not in text, symbol
        assert "ك" not in text, symbol
        assert "‌" not in value["name"], symbol
        assert symbol == symbol.strip()


def test_old_indexes_of_a_symbol():
    assert symbols_data.get_ticker_old_index("آبادا") == ["18621338450655320"]
    assert symbols_data.get_ticker_old_index("فولاد") == []
    assert symbols_data.get_ticker_old_index("ناموجود") == []
    # the list is a copy, changing it does not change the symbols
    symbols_data.get_ticker_old_index("آبادا").append("1")
    assert symbols_data.get_ticker_old_index("آبادا") == ["18621338450655320"]


def test_deleted_symbols_have_their_index_in_their_old_list():
    info = symbols_data.symbols_information()
    assert info["شوش"]["index"] in info["شوش"]["old"]
    assert info["فولاد"]["index"] not in info["فولاد"]["old"]


def test_old_indexes_are_not_active_under_another_symbol():
    # an index in the old list of a symbol is read as a part of the
    # history of that symbol, and a Ticker of that index is taken as
    # deleted. A renamed instrument keeps its index under the new symbol,
    # so that index must not be in the old list of the previous symbol.
    info = symbols_data.symbols_information()
    active = {
        value["index"]: symbol
        for symbol, value in info.items()
        if value["index"] not in value["old"]
    }
    conflicts = [
        (symbol, old, active[old])
        for symbol, value in info.items()
        for old in value["old"]
        if old in active and active[old] != symbol
    ]
    assert conflicts == []


def test_all_symbols():
    symbols = symbols_data.all_symbols()
    assert isinstance(symbols, set)
    assert symbols == set(symbols_data.symbols_information())
    assert {"فولاد", "دیران", "کاریس", "شوش"} <= symbols


def test_symbols_by_their_index():
    by_index = symbols_data.map_index_to_symbols()
    assert by_index[FOLAD] == {
        "code": "IRO1FOLD0001",
        "name": "فولاد مبارکه اصفهان",
        "old": [],
        "symbol": "فولاد",
    }
    assert by_index["37661500521100963"]["symbol"] == "آبادا"
    assert by_index["37661500521100963"]["old"] == ["18621338450655320"]
    # old indexes are not keys
    assert "18621338450655320" not in by_index
    indexes = {
        value["index"] for value in symbols_data.symbols_information().values()
    }
    assert set(by_index) == indexes


def test_index_of_a_financial_index():
    # the names have the ك and ي of the website
    assert symbols_data.get_financial_index("شاخص كل") == "32097828799138957"
    assert (
        symbols_data.get_financial_index("شاخص كل فرابورس")
        == "43685683301327984"
    )
    assert symbols_data.get_financial_index("شاخص کل") is None
    assert symbols_data.get_financial_index("ناموجود") is None


def test_financial_indexes_information():
    info = symbols_data.financial_indexes_information()
    assert len(info) == 70
    assert info["فلزات اساسي"] == {
        "index": "32453344048876642",
        "section_number": 27,
    }
    assert info["شاخص كل"] == {
        "index": "32097828799138957",
        "section_number": "",
    }
    for name, value in info.items():
        assert set(value) == {"index", "section_number"}
        assert "ی" not in name and "ک" not in name, name
    # every index has its own code
    assert len({value["index"] for value in info.values()}) == 70
    assert symbols_data.financial_indexes_information() is info


def test_all_financial_index():
    names = symbols_data.all_financial_index()
    assert isinstance(names, set)
    assert names == set(symbols_data.financial_indexes_information())
    assert {"شاخص كل", "شاخص صنعت", "فلزات اساسي"} <= names


NEW_SYMBOL = MarketSymbol(
    code="IRO1NBAB0001",
    symbol="آبادا",
    name="تولید نیروی برق آبادان",
    index="37661500521100963",
    old=["18621338450655320"],
)
NEW_SYMBOL_IN_FILE = {
    "index": "37661500521100963",
    "code": "IRO1NBAB0001",
    "name": "تولید نیروی برق آبادان",
    "old": ["18621338450655320"],
}


def test_append_symbol_to_the_file_and_to_the_loaded_symbols(symbols_file):
    # the temporary symbols file has only فولاد
    assert symbols_data.all_symbols() == {"فولاد"}

    symbols_data.append_symbol_to_file(NEW_SYMBOL)
    assert symbols_data.get_ticker_index("آبادا") == "37661500521100963"
    assert symbols_data.get_ticker_old_index("آبادا") == ["18621338450655320"]
    saved = json.loads(symbols_file.read_text(encoding="utf8"))
    assert list(saved) == ["فولاد", "آبادا"]
    assert saved["آبادا"] == NEW_SYMBOL_IN_FILE
    assert saved["فولاد"]["index"] == FOLAD
    # the letters are written as they are, not as \u escapes
    assert "آبادا" in symbols_file.read_text(encoding="utf8")


def test_append_symbol_before_the_symbols_are_loaded(symbols_file):
    symbols_data.append_symbol_to_file(NEW_SYMBOL)
    assert symbols_data.symbols_information() == {
        "فولاد": json.loads(symbols_file.read_text(encoding="utf8"))["فولاد"],
        "آبادا": NEW_SYMBOL_IN_FILE,
    }


@pytest.mark.xfail(
    strict=True,
    reason="append_symbol_to_file writes over the start of the file and "
    "keeps the rest, so a shorter content leaves the end of the old one",
)
def test_append_symbol_replaces_a_symbol_of_the_file(symbols_file):
    renamed = MarketSymbol(
        code="IRO1FOLD0001",
        symbol="فولاد",
        name="new name",
        index="1",
        old=[FOLAD],
    )
    symbols_data.append_symbol_to_file(renamed)
    saved = json.loads(symbols_file.read_text(encoding="utf8"))
    assert saved == {
        "فولاد": {
            "index": "1",
            "code": "IRO1FOLD0001",
            "name": "new name",
            "old": [FOLAD],
        }
    }


def test_clean_symbol_and_name():
    # the Arabic ي and ك of the website become the Persian ی and ک
    assert symbols_data.clean_symbol(" كاريس ") == "کاریس"
    # a zero width non-joiner stays inside a symbol and is cut from a name
    assert symbols_data.clean_symbol("سرمايه‌گذاري") == "سرمایه‌گذاری"
    assert symbols_data.clean_name("ايران‌دارو\t") == "ایراندارو"
    assert symbols_data.clean_name(" سرمايه‌گذاري‌ نمونه ") == (
        "سرمایهگذاری نمونه"
    )


def test_match_search_results_of_a_symbol():
    results = parse_instrument_search(ABADA_SEARCH)
    active, old = symbols_data.match_search_results(results, "آبادا")
    assert active is not None
    assert active.ins_code == "1"
    assert old == ["2"]
    # of two active instruments the preferred one wins
    active, _ = symbols_data.match_search_results(
        results, "آبادا", preferred_index="4"
    )
    assert active is not None
    assert active.ins_code == "4"
    active, _ = symbols_data.match_search_results(
        results, "آبادا", preferred_index="9"
    )
    assert active is not None
    assert active.ins_code == "1"
    # only the instruments with exactly the symbol count
    active, old = symbols_data.match_search_results(results, "آباداح")
    assert active is None
    assert old == ["3"]
    assert symbols_data.match_search_results(results, "آباد") == (None, [])


def test_match_search_results_of_the_saved_search(sample):
    results = parse_instrument_search(sample("instrument_search"))
    # 19 instruments have ديران in their symbol or name, one is the symbol
    active, old = symbols_data.match_search_results(results, "ديران")
    assert active is not None
    assert active.ins_code == DIRAN
    assert old == []
    active, old = symbols_data.match_search_results(results, "عمادیران")
    assert active is None
    assert old == [DELETED]


def test_symbol_info_of_a_symbol(fake_api):
    info = symbols_data.get_symbol_info("دیران")
    assert info is not None
    assert astuple(info) == astuple(DIRAN_SYMBOL)
    assert fake_api.calls == [
        ("instrument_search", "دیران"),
        ("instrument_info", DIRAN),
    ]


def test_symbol_info_searches_with_persian_letters(fake_api):
    info = symbols_data.get_symbol_info(" ديران ")
    assert info is not None
    assert astuple(info) == astuple(DIRAN_SYMBOL)
    assert fake_api.calls[0] == ("instrument_search", "دیران")


def test_symbol_info_has_the_old_instruments_of_the_symbol(fake_api):
    fake_api.responses["instrument_search"] = ABADA_SEARCH
    info = symbols_data.get_symbol_info("آبادا")
    assert info is not None
    assert info.index == "1"
    assert info.old == ["2"]
    # the search has no name, it is read from the instrument info
    assert info.name == "ایراندارو"
    assert fake_api.calls[1] == ("instrument_info", "1")


def test_symbol_info_of_a_symbol_without_an_active_instrument(fake_api):
    assert symbols_data.get_symbol_info("ناموجود") is None
    # deleted in the saved search
    assert symbols_data.get_symbol_info("عمادیران") is None
    assert symbols_data.get_symbol_info("  ") is None
    assert fake_api.calls == [
        ("instrument_search", "ناموجود"),
        ("instrument_search", "عمادیران"),
    ]


def test_symbol_info_without_the_instrument_info(fake_api, caplog):
    fake_api.errors["instrument_info"] = requests.ConnectionError("no answer")
    with caplog.at_level(logging.WARNING, logger="pytse"):
        info = symbols_data.get_symbol_info("دیران")
    assert info is not None
    # the ISIN is only in the instrument info
    assert astuple(info) == ("", "دیران", "ایراندارو", DIRAN, [])
    assert "cannot read the ISIN of دیران" in caplog.text


def test_symbol_info_fails_when_the_search_fails(fake_api):
    fake_api.errors["instrument_search"] = requests.ConnectionError("down")
    with pytest.raises(requests.ConnectionError, match="down"):
        symbols_data.get_symbol_info("دیران")
