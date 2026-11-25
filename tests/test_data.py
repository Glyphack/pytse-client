import asyncio
import json
import logging

import aiohttp
import pytest

from pytse_client import symbols_data
from pytse_client.data import generate_indices_name, update_symbols_json

TOTAL_INDEX = "32097828799138957"


@pytest.fixture
def indices_file(monkeypatch, tmp_path):
    path = tmp_path / "indices_name.json"
    monkeypatch.setattr(generate_indices_name, "INDICES_FILE", path)
    return path


def generate_indices(indices_file) -> dict:
    generate_indices_name.main()
    return json.loads(indices_file.read_text(encoding="utf8"))


def indices_answer(*rows: tuple[str, str]) -> dict:
    return {
        "indexB1": [{"insCode": code, "lVal30": title} for code, title in rows]
    }


@pytest.mark.parametrize(
    "title, name, section_number",
    [
        ("27-فلزات اساسي", "فلزات اساسي", 27),
        ("01-زراعت", "زراعت", 1),
        # the number of the section at the end, or without a dash
        ("بيمه و بازنشسته66", "بيمه و بازنشسته", 66),
        ("26محصولات كامپيوتري الكترونيكي", "محصولات كامپيوتري الكترونيكي", 26),
        # a number inside the title is no section number
        ("شاخص قيمت 50 شركت", "شاخص قيمت 50 شركت", ""),
        ("شاخص كل", "شاخص كل", ""),
        # dashes are cut everywhere
        ("شاخص قيمت(وزني-ارزشي)", "شاخص قيمت(وزنيارزشي)", ""),
    ],
)
def test_index_title(indices_file, fake_api, title, name, section_number):
    fake_api.responses["indices"] = indices_answer(("1", title))
    assert generate_indices(indices_file) == {
        name: {"index": "1", "section_number": section_number}
    }


def test_indices_keep_one_index_per_name(indices_file, fake_api, monkeypatch):
    answers = {
        1: indices_answer(
            ("1", "35-حمل و نقل"),
            ("2", "49-كاشي و سراميك"),
            ("3", "60-حمل و نقل"),
        ),
        2: indices_answer(("4", "كاشي و سراميك"), ("5", "شاخص كل فرابورس")),
    }
    monkeypatch.setattr(fake_api, "call_indices", answers.__getitem__)
    indices = generate_indices(indices_file)
    assert indices == {
        # the later index of a market replaces the earlier one
        "حمل و نقل": {"index": "3", "section_number": 60},
        # the index of the first market is kept
        "كاشي و سراميك": {"index": "2", "section_number": 49},
        "شاخص كل فرابورس": {"index": "5", "section_number": ""},
    }
    assert list(indices) == ["حمل و نقل", "كاشي و سراميك", "شاخص كل فرابورس"]


def test_financial_indices_of_the_saved_list(indices_file, fake_api):
    indices = generate_indices(indices_file)
    # the stock exchange, then fara bourse; the fake answers both with
    # the saved list of the stock exchange
    assert fake_api.calls == [("indices", 1), ("indices", 2)]
    # 58 indexes, two of them are named حمل و نقل
    assert len(indices) == 57
    assert indices["شاخص كل"] == {"index": TOTAL_INDEX, "section_number": ""}
    assert indices["زراعت"] == {
        "index": "34408080767216529",
        "section_number": 1,
    }
    assert indices["فلزات اساسي"] == {
        "index": "32453344048876642",
        "section_number": 27,
    }
    assert indices["بيمه و بازنشسته"]["section_number"] == 66
    assert indices["حمل و نقل"] == {
        "index": "24187097921483699",
        "section_number": 60,
    }
    assert next(iter(indices)) == "زراعت"


def test_financial_indices_of_one_market(indices_file, fake_api, monkeypatch):
    monkeypatch.setattr(generate_indices_name, "INDICES_FLOWS", (2,))
    indices = generate_indices(indices_file)
    assert fake_api.calls == [("indices", 2)]
    assert len(indices) == 57


def test_indices_file_text(indices_file, fake_api):
    fake_api.responses["indices"] = indices_answer(
        ("32453344048876642", "27-فلزات اساسي"), (TOTAL_INDEX, "شاخص كل")
    )
    generate_indices_name.main()
    text = indices_file.read_text(encoding="utf8")
    assert list(json.loads(text)) == ["فلزات اساسي", "شاخص كل"]
    # the names are written as they are, not as \u escapes
    assert '"فلزات اساسي": {\n    "index": "32453344048876642",' in text


def test_indices_file_of_the_generator_is_the_one_the_package_reads():
    assert generate_indices_name.INDICES_FILE.name == "indices_name.json"
    packaged = json.loads(
        generate_indices_name.INDICES_FILE.read_text(encoding="utf8")
    )
    assert packaged == symbols_data.financial_indexes_information()


DIRAN = "69090868458637360"
# two more symbols of the saved search for دیران: one that is active and
# one that is deleted
MADIRA = "15917865009187760"
DELETED = "14058161288052046"
# a search answer with two active instruments and a deleted one of the
# symbol آبادا
ABADA_SEARCH = {
    "instrumentSearch": [
        {"insCode": "1", "lVal18AFC": "آبادا", "lastDate": 1},
        {"insCode": "2", "lVal18AFC": "آبادا", "lastDate": 0},
        {"insCode": "3", "lVal18AFC": "آباداح", "lastDate": 0},
        {"insCode": "4", "lVal18AFC": "آبادا", "lastDate": 1},
    ]
}

FOLAD_IN_FILE = {
    "index": "46348559193224090",
    "code": "IRO1FOLD0001",
    "name": "فولاد مبارکه اصفهان",
    "old": [],
}
DIRAN_IN_FILE = {
    "index": DIRAN,
    "code": "IRO1IRDR0001",
    "name": "ایراندارو",
    "old": [],
}
# the other symbols of the saved market watch
OTHERS_IN_FILE = {
    "خودرو": {
        "index": "65883838195688438",
        "code": "IRO1IKCO0001",
        "name": "ایران خودرو",
        "old": [],
    },
    "زاگرس": {
        "index": "13235547361447092",
        "code": "IRO3PZGZ0001",
        "name": "پتروشیمی زاگرس",
        "old": [],
    },
    "شستا": {
        "index": "2400322364771558",
        "code": "IRO1TAMN0001",
        "name": "سرمایه گذاری تامین اجتماعی",
        "old": [],
    },
    "کاریس": {
        "index": "69067576215760005",
        "code": "IRT3SSKF0001",
        "name": "صندوق س.سپند کاریزما-س",
        "old": [],
    },
}


def in_file(symbol: str, index: str, old: list[str] | None = None) -> dict:
    return {
        "index": index,
        "code": f"code of {symbol}",
        "name": f"name of {symbol}",
        "old": old or [],
    }


def market_watch_of(sample, *rows: tuple[str, str]) -> dict:
    row = sample("market_watch")["marketwatch"][0]
    return {
        "marketwatch": [
            {
                **row,
                "lva": symbol,
                "lvc": f"name of {symbol}",
                "insID": f"code of {symbol}",
                "insCode": code,
            }
            for symbol, code in rows
        ]
    }


def history_of(*codes: str) -> dict:
    return {"closingPriceDailyAllInst": [{"insCode": code} for code in codes]}


def instrument_info_by_code(monkeypatch, fake_api, sample, symbols):
    async def call_instrument_info_async(ins_code, session):
        fake_api.calls.append(("instrument_info", ins_code))
        if "instrument_info" in fake_api.errors:
            raise fake_api.errors["instrument_info"]
        info = sample("instrument_info")
        if ins_code in symbols:
            info["instrumentInfo"]["lVal18AFC"] = symbols[ins_code]
        return info

    monkeypatch.setattr(
        fake_api, "call_instrument_info_async", call_instrument_info_async
    )


@pytest.fixture
def empty_market(fake_api):
    fake_api.responses["market_watch"] = {"marketwatch": []}
    fake_api.responses["closing_price_daily_all_inst"] = history_of()
    fake_api.responses["instrument_search"] = {"instrumentSearch": []}


def update(symbols_file, current: dict | None = None) -> dict:
    if current is not None:
        symbols_file.write_text(
            json.dumps(current, ensure_ascii=False), encoding="utf8"
        )
    asyncio.run(update_symbols_json.main())
    return json.loads(symbols_file.read_text(encoding="utf8"))


def test_sort_by_the_persian_alphabet(symbols_file, empty_market):
    current = {
        symbol: in_file(symbol, "1")
        for symbol in (
            "گلدیرا",
            "فولاد",
            "کاریس",
            "آبادا",
            "پارس",
            "دیران",
            "اخابر",
            "فملی",
            "دی",
            "18719101",
        )
    }
    # پ, ک and گ are after ف in unicode, not in the alphabet
    assert list(update(symbols_file, current)) == [
        "18719101",
        "آبادا",
        "اخابر",
        "پارس",
        "دی",
        "دیران",
        "فملی",
        "فولاد",
        "کاریس",
        "گلدیرا",
    ]


def test_sort_ignores_spaces_and_zero_width_non_joiners(
    symbols_file, empty_market
):
    current = {s: in_file(s, "1") for s in ("های وب", "ها‌ی", "هاما")}
    assert list(update(symbols_file, current)) == ["هاما", "ها‌ی", "های وب"]


def test_market_watch_rows_that_are_no_symbols_are_skipped(
    symbols_file, empty_market, fake_api, sample
):
    symbols_file.unlink()
    market_watch = sample("market_watch")
    row = market_watch["marketwatch"][0]
    market_watch["marketwatch"] = [
        {
            **row,
            "lva": "سرمايه‌گذاري",
            "lvc": "سرمايه‌گذاري‌ نمونه\t",
            "insID": " IRO1XXXX0001 ",
            "insCode": "1",
        },
        # bonds, options and other symbols that end with a number
        {
            **row,
            "lva": "ضفلا1409",
            "lvc": "اختيارخ فولاد-3000-1404/11/08",
            "insID": "IRO9FOLD0C41",
            "insCode": "2",
        },
        {**row, "lva": " ", "insCode": "3"},
        {**row, "lva": None, "lvc": None, "insID": None, "insCode": "4"},
    ]
    fake_api.responses["market_watch"] = market_watch
    assert update(symbols_file) == {
        "سرمایه‌گذاری": {
            "index": "1",
            "code": "IRO1XXXX0001",
            "name": "سرمایهگذاری نمونه",
            "old": [],
        }
    }


def test_symbols_of_the_closing_price_history(
    symbols_file, empty_market, fake_api, capsys
):
    symbols_file.unlink()
    fake_api.responses["closing_price_daily_all_inst"] = history_of(
        "2", "1", "2"
    )
    # the fake answers each code with the saved information of دیران
    saved = update(symbols_file)
    assert sorted(
        call for call in fake_api.calls if call[0] == "instrument_info"
    ) == [("instrument_info", "1"), ("instrument_info", "2")]
    assert (
        "closing price history: 2 instruments, 2 not in the market watch, "
        "2 symbols"
    ) in capsys.readouterr().out.splitlines()
    # the first of the two is kept, and dropped as the search does not
    # know it
    assert saved == {}


def test_instrument_codes_that_are_no_symbols_are_skipped(
    symbols_file, empty_market, fake_api, sample, capsys
):
    symbols_file.unlink()
    fake_api.responses["closing_price_daily_all_inst"] = history_of("1")
    info = sample("instrument_info")
    info["instrumentInfo"]["lVal18AFC"] = "اخزا123"
    fake_api.responses["instrument_info"] = info
    update(symbols_file)
    assert (
        "closing price history: 1 instruments, 1 not in the market watch, "
        "0 symbols"
    ) in capsys.readouterr().out.splitlines()


def test_instrument_codes_whose_information_cannot_be_read_are_skipped(
    symbols_file, empty_market, fake_api, no_waiting, caplog, capsys
):
    symbols_file.unlink()
    fake_api.responses["closing_price_daily_all_inst"] = history_of("1")
    fake_api.errors["instrument_info"] = aiohttp.ClientError("no answer")
    with caplog.at_level(logging.WARNING, logger="pytse"):
        update(symbols_file)
    assert (
        "closing price history: 1 instruments, 1 not in the market watch, "
        "0 symbols"
    ) in capsys.readouterr().out.splitlines()
    assert "cannot read instrument info of 1" in caplog.text


def test_symbols_of_the_current_file(symbols_file, empty_market, capsys):
    current = {
        "آبادا": {
            "index": "37661500521100963",
            "code": "IRO1NBAB0001",
            "name": "تولید نیروی برق آبادان",
            "old": ["18621338450655320"],
        },
        # numbers and missing values are read as text
        "ناقص": {"index": 5, "code": None, "old": [7]},
        "تهی": {},
    }
    # the search does not know them, so each is deleted: its code goes to
    # its old list
    assert update(symbols_file, current) == {
        "آبادا": {
            "index": "37661500521100963",
            "code": "IRO1NBAB0001",
            "name": "تولید نیروی برق آبادان",
            "old": ["18621338450655320", "37661500521100963"],
        },
        "تهی": {"index": "", "code": "", "name": "", "old": []},
        "ناقص": {"index": "5", "code": "", "name": "", "old": ["7", "5"]},
    }
    assert capsys.readouterr().out.splitlines()[0] == (
        "symbols in the current symbols_name.json: 3"
    )


def test_old_indexes_of_symbols_of_the_saved_search(
    symbols_file, empty_market, fake_api, sample, monkeypatch
):
    del fake_api.responses["instrument_search"]
    # active in the market watch
    market_watch = sample("market_watch")
    market_watch["marketwatch"] = [market_watch["marketwatch"][-1]]
    fake_api.responses["market_watch"] = market_watch
    # not in the market watch: مادیرا, which the search has with another
    # code, and ناموجود, which is not in the search
    fake_api.responses["closing_price_daily_all_inst"] = history_of("9", "5")
    instrument_info_by_code(
        monkeypatch, fake_api, sample, {"9": "مادیرا", "5": "ناموجود"}
    )
    current = {
        "دیران": {**DIRAN_IN_FILE, "index": "111", "old": ["222"]},
        # only a deleted instrument in the search
        "عمادیران": in_file("عمادیران", DELETED, old=["333"]),
    }
    assert update(symbols_file, current) == {
        # the code of the file and its old list are the old codes
        "دیران": {
            "index": DIRAN,
            "code": "IRO1IRDR0001",
            "name": "ایراندارو",
            "old": ["222", "111"],
        },
        # the code and name of the search, the ISIN of the instrument info
        "مادیرا": {
            "index": MADIRA,
            "code": "IRO1IRDR0001",
            "name": "صنایع مادیران",
            "old": [],
        },
        # deleted: its own code is in its old list
        "عمادیران": in_file("عمادیران", DELETED, old=[DELETED, "333"]),
    }
    # besides the codes of the history, the ISIN is asked only for the
    # symbol with a new code
    assert sorted(
        call[1] for call in fake_api.calls if call[0] == "instrument_info"
    ) == sorted(["9", "5", MADIRA])


def test_old_indexes_when_a_symbol_has_several_instruments(
    symbols_file, empty_market, fake_api, sample
):
    fake_api.responses["instrument_search"] = ABADA_SEARCH
    # of the two active instruments the one of the symbol is kept
    assert update(symbols_file, {"آبادا": in_file("آبادا", "4")}) == {
        "آبادا": in_file("آبادا", "4", old=["2"])
    }

    # the market watch has a code the search does not list as active
    symbols_file.unlink()
    fake_api.responses["market_watch"] = market_watch_of(
        sample, ("آبادا", "9")
    )
    assert update(symbols_file) == {"آبادا": in_file("آبادا", "9", old=["2"])}


def test_a_missing_isin_is_read(
    symbols_file, empty_market, fake_api, no_waiting, caplog
):
    del fake_api.responses["instrument_search"]
    without_code = {**DIRAN_IN_FILE, "code": ""}
    assert update(symbols_file, {"دیران": without_code}) == {
        "دیران": DIRAN_IN_FILE
    }

    fake_api.errors["instrument_info"] = aiohttp.ClientError("no answer")
    with caplog.at_level(logging.WARNING, logger="pytse"):
        saved = update(symbols_file, {"دیران": without_code})
    assert saved == {"دیران": without_code}
    assert "cannot read the ISIN of دیران" in caplog.text


def test_what_is_known_is_kept_when_the_search_fails(
    symbols_file,
    empty_market,
    fake_api,
    sample,
    monkeypatch,
    no_waiting,
    caplog,
):
    fake_api.errors["instrument_search"] = aiohttp.ClientError("no answer")
    fake_api.responses["market_watch"] = market_watch_of(
        sample,
        # also in the file, which has an old code
        ("شکبیر", "1"),
        # in the market watch only
        ("تازه", "2"),
    )
    # in none of the two
    fake_api.responses["closing_price_daily_all_inst"] = history_of("4")
    instrument_info_by_code(monkeypatch, fake_api, sample, {"4": "ناموجود"})
    current = {
        "شکبیر": in_file("شکبیر", "1", old=["11"]),
        # in the file only
        "قدیمی": in_file("قدیمی", "33", old=["34"]),
    }
    with caplog.at_level(logging.WARNING, logger="pytse"):
        saved = update(symbols_file, current)
    assert {
        symbol: (value["index"], value["old"])
        for symbol, value in saved.items()
    } == {
        "شکبیر": ("1", ["11"]),
        "تازه": ("2", []),
        # the symbol of the file as it is
        "قدیمی": ("33", ["34"]),
    }
    assert "cannot look شکبیر up" in caplog.text


def test_progress_is_logged_every_200_symbols(
    symbols_file, empty_market, caplog
):
    current = {
        f"نماد {number}": in_file(f"نماد {number}", str(number))
        for number in range(200)
    }
    with caplog.at_level(logging.INFO, logger="pytse"):
        saved = update(symbols_file, current)
    assert len(saved) == 200
    assert "looked up 200/200 symbols" in caplog.text


def test_old_indexes_active_under_another_symbol_are_removed(
    symbols_file, empty_market, fake_api, no_waiting
):
    # the search fails, so each symbol of the file is kept as it is
    fake_api.errors["instrument_search"] = aiohttp.ClientError("no answer")
    current = {
        # a renamed fund: a company has its former symbol with another
        # code, and the code of the fund is active under سافرون
        "سحرخیز": in_file("سحرخیز", "2", old=["1"]),
        "سافرون": in_file("سافرون", "1"),
        # a deleted symbol whose code is active under its new symbol
        "اکسیژن": in_file("اکسیژن", "3", old=["3"]),
        "رواج": in_file("رواج", "3"),
        # a deleted symbol, its code stays in its old list
        "شوش": in_file("شوش", "4", old=["4", "5"]),
        # an old code that no other symbol uses
        "آبادا": in_file("آبادا", "6", old=["7"]),
    }
    saved = update(symbols_file, current)
    assert {symbol: value["old"] for symbol, value in saved.items()} == {
        "سحرخیز": [],
        "سافرون": [],
        "اکسیژن": [],
        "رواج": [],
        "شوش": ["4", "5"],
        "آبادا": ["7"],
    }


def test_update_writes_the_symbols_of_the_market_watch(
    symbols_file, fake_api, capsys
):
    symbols_file.unlink()
    symbols_file.parent.rmdir()

    saved = update(symbols_file)
    assert saved == {
        **OTHERS_IN_FILE,
        "فولاد": FOLAD_IN_FILE,
        "دیران": DIRAN_IN_FILE,
    }
    # in the order of the Persian alphabet
    assert list(saved) == ["خودرو", "دیران", "زاگرس", "شستا", "فولاد", "کاریس"]
    assert capsys.readouterr().out.splitlines() == [
        "symbols in the current symbols_name.json: 0",
        "market watch: 6 instruments, 6 symbols",
        (
            "closing price history: 6 instruments, 0 not in the market "
            "watch, 0 symbols"
        ),
        "Total deduplicated symbols: 6",
        "finished fetching old indexes, symbols: 6",
    ]
    assert fake_api.calls[:2] == [
        ("market_watch",),
        ("closing_price_daily_all_inst",),
    ]
    # every symbol is looked up with the search
    searches = [
        call for call in fake_api.calls if call[0] == "instrument_search"
    ]
    assert len(searches) == 6


def test_update_reads_back_the_file_it_writes(symbols_file, fake_api):
    symbols_file.unlink()
    update(symbols_file)
    text = symbols_file.read_text(encoding="utf8")
    # the letters are written as they are, not as \u escapes
    assert '"خودرو": {\n    "index": "65883838195688438",' in text

    update(symbols_file)
    assert symbols_file.read_text(encoding="utf8") == text


def test_update_adds_suspended_and_deleted_symbols(
    symbols_file, fake_api, sample, capsys
):
    # دیران is not in the market watch, like a suspended symbol; the
    # closing price history still has it
    market_watch = sample("market_watch")
    assert market_watch["marketwatch"].pop()["insCode"] == DIRAN
    fake_api.responses["market_watch"] = market_watch
    current = {
        "فولاد": FOLAD_IN_FILE,
        # دیران had other instrument codes before
        "دیران": {**DIRAN_IN_FILE, "index": "111", "old": ["222"]},
        # the search knows this symbol as deleted
        "عمادیران": {"index": DELETED, "code": "c", "name": "n", "old": []},
    }

    saved = update(symbols_file, current)
    assert saved == {
        **OTHERS_IN_FILE,
        "فولاد": FOLAD_IN_FILE,
        # the code of the instrument info, the codes of the file are old
        "دیران": {**DIRAN_IN_FILE, "old": ["222", "111"]},
        # kept, with its own code in its old list
        "عمادیران": {
            "index": DELETED,
            "code": "c",
            "name": "n",
            "old": [DELETED],
        },
    }
    assert list(saved) == [
        "خودرو",
        "دیران",
        "زاگرس",
        "شستا",
        "عمادیران",
        "فولاد",
        "کاریس",
    ]
    assert capsys.readouterr().out.splitlines() == [
        "symbols in the current symbols_name.json: 3",
        "market watch: 5 instruments, 5 symbols",
        (
            "closing price history: 6 instruments, 1 not in the market "
            "watch, 1 symbols"
        ),
        "Total deduplicated symbols: 7",
        "finished fetching old indexes, symbols: 7",
    ]
    # the symbol and ISIN of the suspended instrument are read from its
    # instrument info
    assert ("instrument_info", DIRAN) in fake_api.calls


def test_update_takes_a_symbol_from_its_first_source(symbols_file, fake_api):
    # فولاد is in the market watch and in the file with another code
    current = {"فولاد": {"index": "111", "code": "c", "name": "n", "old": []}}
    saved = update(symbols_file, current)
    assert saved["فولاد"] == {**FOLAD_IN_FILE, "old": ["111"]}
