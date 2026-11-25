"""Tests of pytse_client.tsetmc_api: every parse function on the saved
response of its endpoint, the conversions and the client."""

import asyncio
import dataclasses
import datetime
import inspect
import io
import types
import typing
from pathlib import Path
from typing import Any

import aiohttp
import pytest
import requests
from requests.adapters import HTTPAdapter

from pytse_client.tsetmc_api import (
    _convert,
    best_limits,
    client,
    client_type,
    closing_price,
    codal,
    fund,
    index,
    instrument,
    market,
    shareholder,
    trade,
)

DIRAN = "69090868458637360"  # دیران, the instrument of most samples
SHASTA = "2400322364771558"  # شستا
FUND = "69067576215760005"  # fund کاریس
TOTAL_INDEX = "32097828799138957"  # شاخص کل
# day of the samples of the History page
DAY = datetime.date(2026, 11, 22)

DATA_DIR = Path(__file__).parent / "data"

# name of an endpoint (its TsetmcApi method without call_) -> the function
# that parses its response
PARSERS = {
    "market_overview": market.parse_market_overview,
    "market_watch": market.parse_market_watch,
    "key_stats": market.parse_key_stats,
    "closing_price_info": closing_price.parse_closing_price_info,
    "closing_price_daily_list": closing_price.parse_closing_price_daily_list,
    "recent_closing_price_daily_list": (
        closing_price.parse_closing_price_daily_list
    ),
    "closing_price_daily_all_inst": (
        closing_price.parse_closing_price_daily_all_inst
    ),
    "best_limits": best_limits.parse_best_limits,
    "best_limits_history": best_limits.parse_best_limits_history,
    "client_type": client_type.parse_client_type,
    "client_type_all": client_type.parse_client_type_all,
    "client_type_history": client_type.parse_client_type_history,
    "trades": trade.parse_trades,
    "trade_history": trade.parse_trade_history,
    "shareholders": shareholder.parse_shareholders,
    "day_shareholders": shareholder.parse_day_shareholders,
    "instrument_info": instrument.parse_instrument_info,
    "instrument_search": instrument.parse_instrument_search,
    "instrument_history": instrument.parse_instrument_history,
    "index_history": index.parse_index_history,
    "index_intraday": index.parse_index_intraday,
    "indices": index.parse_indices,
    "index_companies": index.parse_index_companies,
    "etf": fund.parse_etf,
    "codal_publisher": codal.parse_codal_publisher,
}


def _matches(value: Any, hint: Any) -> bool:
    """True when a value has the type of an annotation."""
    if hint is Any:
        return True
    if hint is type(None):
        return value is None
    origin = typing.get_origin(hint)
    if origin in (typing.Union, types.UnionType):
        return any(_matches(value, arg) for arg in typing.get_args(hint))
    if origin is list:
        (item_hint,) = typing.get_args(hint)
        return isinstance(value, list) and all(
            _matches(item, item_hint) for item in value
        )
    # bool is an int and datetime a date in python, they are not here
    if hint is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if hint is float:
        return isinstance(value, float)
    if hint is datetime.date:
        return isinstance(value, datetime.date) and not isinstance(
            value, datetime.datetime
        )
    return isinstance(value, hint)


def assert_field_types(value: Any, path: str | None = None) -> None:
    """Assert that every field of a dataclass (or of every dataclass in a
    list, nested ones included) has the type of its annotation."""
    if isinstance(value, list):
        for i, item in enumerate(value):
            assert_field_types(item, f"{path or 'rows'}[{i}]")
        return
    assert dataclasses.is_dataclass(value), f"{path}: {value!r}"
    path = path or type(value).__name__
    hints = typing.get_type_hints(type(value))
    for field in dataclasses.fields(value):
        field_value = getattr(value, field.name)
        hint = hints[field.name]
        assert _matches(
            field_value, hint
        ), f"{path}.{field.name} = {field_value!r} is not {hint}"
        if dataclasses.is_dataclass(field_value) or (
            isinstance(field_value, list)
            and field_value
            and dataclasses.is_dataclass(field_value[0])
        ):
            assert_field_types(field_value, f"{path}.{field.name}")


@pytest.mark.parametrize("endpoint", list(PARSERS))
def test_parsed_fields_have_their_annotated_types(endpoint, sample):
    parsed = PARSERS[endpoint](sample(endpoint))
    assert parsed
    assert_field_types(parsed)


def test_assert_field_types_finds_a_wrong_type():
    wrong = trade.Trade(
        number=1,
        time=datetime.time(9),
        volume=10,
        # a float where the annotation says int
        price=24020.0,  # ty: ignore[invalid-argument-type]
        canceled=False,
    )
    with pytest.raises(AssertionError, match="Trade.price = 24020.0"):
        assert_field_types(wrong)
    with pytest.raises(AssertionError, match=r"rows\[1\]"):
        assert_field_types([dataclasses.replace(wrong, price=1), wrong])


# ---------------------------------------------------------------------------
# market


def test_parse_market_overview(sample):
    assert market.parse_market_overview(
        sample("market_overview")
    ) == market.MarketOverview(
        last_trade_date=datetime.date(2026, 11, 23),
        last_trade_time=datetime.time(17, 59, 58),
        index_value=8389814.07,
        index_change=62736.37,
        equal_weighted_index_value=2530324.54,
        equal_weighted_index_change=41825.9,
        trade_count=1035288,
        trade_volume=71681051307,
        trade_value=543415990624085,
        market_value=243085685225003584,
        base_market_value=0,
        state="F",
        state_title="بسته",
        last_data_date=None,
        last_data_time=datetime.time(0, 0),
    )


def test_parse_market_watch(sample):
    rows = market.parse_market_watch(sample("market_watch"))
    assert [row.symbol for row in rows] == [
        "شستا",
        "زاگرس",
        "فولاد",
        "خودرو",
        "كاريس",
        "ديران",
    ]
    diran = rows[-1]
    assert dataclasses.replace(
        diran, best_limits=[]
    ) == market.MarketWatchInstrument(
        ins_code=DIRAN,
        isin="IRO1IRDR0001",
        symbol="ديران",
        name="ايران‌دارو",
        time=datetime.time(12, 29, 52),
        first_price=24020,
        closing_price=24020,
        last_price=24020,
        trade_count=99,
        volume=860939,
        value=20679754780,
        low_price=24020,
        high_price=24020,
        yesterday_price=23330,
        eps=3064.0,
        base_volume=1,
        visit_count=13299,
        flow=1,
        sector_code="43 ",
        max_allowed_price=24020,
        min_allowed_price=22640,
        total_shares=1780000000,
        instrument_type=300,
        best_limits=[],
        pe=7.8,
        best_buy_price=24020,
        best_sell_price=24070,
        last_price_change=690,
        closing_price_change=690,
        board_code="N2",
        market_code="NO",
        nav=0,
        open_positions=0,
        id=0,
        date=None,
        p_closing=0,
        i_close=False,
        y_close=False,
        p_dr_cot_val=0,
        z_tot_tran=0,
        q_tot_tran5_j=0,
        q_tot_cap=0,
    )
    assert [dataclasses.astuple(level) for level in diran.best_limits] == [
        # level, buy count, volume and price, sell price, volume and
        # count, id of the last change
        (1, 419, 31322288, 24020, 24070, 294, 1, 16531217120),
        (2, 2, 13430, 23860, 24790, 6284, 4, 16530640644),
        (3, 8, 158553, 23330, 0, 0, 0, 16529217483),
        (4, 1, 1334, 23000, 0, 0, 0, 16528238733),
        (5, 2, 451, 22660, 0, 0, 0, 16529232202),
    ]
    assert_field_types(diran.best_limits)
    shasta = rows[0]
    assert shasta.ins_code == SHASTA
    assert shasta.name == "سرمايه گذاري تامين اجتماعي"
    assert shasta.pe == 15.2
    assert shasta.last_price_change == -80
    assert shasta.total_shares == 1636013456000
    assert [level.buy_price for level in shasta.best_limits] == [
        3480,
        3470,
        3420,
        3410,
        3360,
    ]


def test_parse_key_stats(sample):
    rows = market.parse_key_stats(sample("key_stats"))
    assert len(rows) == 526
    day = datetime.date(2026, 11, 23)
    assert rows[0] == market.InstrumentStatistic(
        ins_code=SHASTA, stat_id=1, value=4767321647133, date=day
    )
    assert rows[-1] == market.InstrumentStatistic(
        ins_code=DIRAN, stat_id=89, value=433, date=day
    )
    diran = {row.stat_id: row.value for row in rows if row.ins_code == DIRAN}
    # every statistic but 28, which the API did not send for دیران
    assert sorted(diran) == [i for i in range(1, 90) if i != 28]
    # a number without a decimal point is an int, with one a float
    assert diran[16] == 860939
    assert isinstance(diran[16], int)
    assert diran[13] == 24020.0
    assert isinstance(diran[13], float)
    assert diran[50] == 18055472.030769


def test_parse_key_stats_reads_exponents_as_floats():
    [row] = market.parse_key_stats(
        {
            "instValueAllInstAllParam": [
                {"insCode": 1, "dataType": "36", "dataValue": "4.2E13"}
            ]
        }
    )
    assert row == market.InstrumentStatistic(
        ins_code="1", stat_id=36, value=4.2e13, date=None
    )
    assert isinstance(row.value, float)


# ---------------------------------------------------------------------------
# closing_price


def test_parse_closing_price_info(sample):
    assert closing_price.parse_closing_price_info(
        sample("closing_price_info")
    ) == closing_price.ClosingPriceInfo(
        instrument_state=closing_price.InstrumentState(
            code="A ",
            title="مجاز",
            idn=0,
            date=None,
            time=datetime.time(0, 0),
            ins_code=None,
            symbol=None,
            name=None,
            real_time=datetime.time(0, 0),
            under_supervision=0,
        ),
        last_price=24020,
        closing_price=24020,
        yesterday_price=23330,
        first_price=24020,
        high_price=24020,
        low_price=24020,
        trade_count=99,
        volume=860939,
        value=20679754780,
        date=datetime.date(2026, 11, 23),
        time=datetime.time(12, 29, 52),
        last_time=datetime.time(12, 29, 52),
        last_date=datetime.date(2026, 11, 23),
        notional_value=0,
        open_positions=0,
        nav=0,
        price_change=0.0,
        last=True,
        id=0,
        ins_code="0",
        i_close=False,
        y_close=False,
        instrument=None,
        thirty_day_closing_history=None,
    )


def test_parse_closing_price_info_without_prices_or_state(sample):
    assert (
        closing_price.parse_closing_price_info({"closingPriceInfo": None})
        is None
    )
    data = sample("closing_price_info")
    data["closingPriceInfo"]["instrumentState"] = None
    data["closingPriceInfo"]["pDrCotVal"] = None
    data["closingPriceInfo"]["dEven"] = 0
    info = closing_price.parse_closing_price_info(data)
    assert info is not None
    assert info.instrument_state is None
    assert info.last_price is None
    assert info.date is None
    assert info.closing_price == 24020


def test_parse_closing_price_daily_list(sample):
    days = closing_price.parse_closing_price_daily_list(
        sample("closing_price_daily_list")
    )
    assert len(days) == 60
    # newest day first
    assert days[0] == closing_price.ClosingPriceDaily(
        date=datetime.date(2026, 11, 23),
        first_price=24020,
        high_price=24020,
        low_price=24020,
        closing_price=24020,
        last_price=24020,
        yesterday_price=23330,
        trade_count=99,
        volume=860939,
        value=20679754780,
        price_change=690.0,
        time=datetime.time(12, 29, 52),
        ins_code=DIRAN,
        last=False,
        id=0,
        i_close=False,
        y_close=True,
    )
    assert days[-1] == closing_price.ClosingPriceDaily(
        date=datetime.date(2026, 9, 1),
        first_price=15460,
        high_price=15460,
        low_price=15210,
        closing_price=15460,
        last_price=15460,
        yesterday_price=15010,
        trade_count=1973,
        volume=64360415,
        value=994717211730,
        price_change=450.0,
        time=datetime.time(12, 30, 3),
        ins_code=DIRAN,
        last=False,
        id=0,
        i_close=False,
        y_close=True,
    )


def test_parse_recent_closing_price_daily_list(sample):
    days = closing_price.parse_closing_price_daily_list(
        sample("recent_closing_price_daily_list")
    )
    assert len(days) == 12
    assert days[0].date == datetime.date(2026, 11, 23)
    assert days[-1] == closing_price.ClosingPriceDaily(
        date=datetime.date(2026, 11, 8),
        first_price=20080,
        high_price=20110,
        low_price=19070,
        closing_price=19320,
        last_price=19070,
        yesterday_price=19650,
        trade_count=1032,
        volume=11131527,
        value=215112439290,
        price_change=-580.0,
        time=datetime.time(12, 29, 58),
        ins_code=DIRAN,
        last=False,
        id=0,
        i_close=False,
        y_close=True,
    )


def test_parse_closing_price_daily_all_inst(sample):
    rows = closing_price.parse_closing_price_daily_all_inst(
        sample("closing_price_daily_all_inst")
    )
    # five days of six instruments
    assert len(rows) == 30
    assert len({row.ins_code for row in rows}) == 6
    assert sorted({row.date for row in rows if row.date}) == [
        datetime.date(2026, 11, 17),
        datetime.date(2026, 11, 18),
        datetime.date(2026, 11, 21),
        datetime.date(2026, 11, 22),
        datetime.date(2026, 11, 23),
    ]
    assert rows[0] == closing_price.ClosingPriceDailyAllInst(
        ins_code=SHASTA,
        date=datetime.date(2026, 11, 17),
        time=datetime.time(0, 0),
        first_price=3640,
        high_price=3750,
        low_price=3640,
        closing_price=3650,
        last_price=3640,
        yesterday_price=3750,
        trade_count=14195,
        volume=1139030124,
        value=4162633024610,
        offset=0,
        id=0,
        i_close=False,
        y_close=False,
    )
    assert rows[-1] == closing_price.ClosingPriceDailyAllInst(
        ins_code=DIRAN,
        date=datetime.date(2026, 11, 23),
        time=datetime.time(0, 0),
        first_price=24020,
        high_price=24020,
        low_price=24020,
        closing_price=24020,
        last_price=24020,
        yesterday_price=23330,
        trade_count=99,
        volume=860939,
        value=20679754780,
        offset=0,
        id=0,
        i_close=False,
        y_close=False,
    )


# ---------------------------------------------------------------------------
# best_limits

# the live order book of the sample: level, buy count, volume and price,
# sell price, volume and count
BEST_LIMITS = [
    best_limits.BestLimit(1, 419, 31322288, 24020, 24070, 294, 1),
    best_limits.BestLimit(2, 2, 13430, 23860, 24790, 6284, 4),
    best_limits.BestLimit(3, 8, 158553, 23330, 0, 0, 0),
    best_limits.BestLimit(4, 1, 1334, 23000, 0, 0, 0),
    best_limits.BestLimit(5, 2, 451, 22660, 0, 0, 0),
]


def test_parse_best_limits(sample):
    assert best_limits.parse_best_limits(sample("best_limits")) == BEST_LIMITS
    assert best_limits.parse_best_limits({"bestLimits": None}) == []


def test_parse_best_limits_history(sample):
    rows = best_limits.parse_best_limits_history(sample("best_limits_history"))
    assert len(rows) == 533
    assert rows[0] == best_limits.BestLimitHistory(
        time=datetime.time(6, 1, 30),
        ref_id=16510846249,
        level=1,
        buy_count=5,
        buy_volume=11327,
        buy_price=22660,
        sell_price=23150,
        sell_volume=1000,
        sell_count=1,
        idn=0,
        date=None,
        title=None,
        ins_code=None,
    )
    assert rows[-1] == best_limits.BestLimitHistory(
        time=datetime.time(9, 4, 55),
        ref_id=16511840212,
        level=1,
        buy_count=876,
        buy_volume=68523552,
        buy_price=23330,
        sell_price=23860,
        sell_volume=1331,
        sell_count=2,
        idn=0,
        date=None,
        title=None,
        ins_code=None,
    )
    assert {row.level for row in rows} == {1, 2, 3, 4, 5}
    # in the order of the api, the oldest change first
    assert rows == sorted(rows, key=lambda row: row.time)
    assert (
        best_limits.parse_best_limits_history({"bestLimitsHistory": []}) == []
    )


# ---------------------------------------------------------------------------
# client_type

CLIENT_TYPE = client_type.ClientType(
    individual_buy_volume=860939,
    individual_buy_count=13,
    individual_sell_volume=703139,
    individual_sell_count=75,
    corporate_buy_volume=0,
    corporate_buy_count=0,
    corporate_sell_volume=157800,
    corporate_sell_count=1,
    ins_code=None,
    ddd_buy_volume=0,
    ddd_buy_count=0,
)


def test_parse_client_type(sample):
    assert client_type.parse_client_type(sample("client_type")) == CLIENT_TYPE
    assert client_type.parse_client_type({"clientType": None}) is None


def test_trade_summaries():
    assert client_type.individual_trade_summary(
        CLIENT_TYPE
    ) == client_type.TradeSummary(
        buy_vol=860939.0, buy_count=13.0, sell_vol=703139.0, sell_count=75.0
    )
    assert client_type.corporate_trade_summary(
        CLIENT_TYPE
    ) == client_type.TradeSummary(
        buy_vol=0.0, buy_count=0.0, sell_vol=157800.0, sell_count=1.0
    )
    summary = client_type.individual_trade_summary(CLIENT_TYPE)
    assert summary is not None
    assert isinstance(summary.buy_vol, float)
    assert isinstance(summary.buy_count, float)
    assert client_type.individual_trade_summary(None) is None
    assert client_type.corporate_trade_summary(None) is None


def test_parse_client_type_all(sample):
    rows = client_type.parse_client_type_all(sample("client_type_all"))
    assert len(rows) == 6
    assert rows[0] == client_type.ClientType(
        individual_buy_volume=702550185,
        individual_buy_count=4618,
        individual_sell_volume=487855525,
        individual_sell_count=1833,
        corporate_buy_volume=396080041,
        corporate_buy_count=39,
        corporate_sell_volume=610774701,
        corporate_sell_count=24,
        ins_code=SHASTA,
        ddd_buy_volume=0,
        ddd_buy_count=0,
    )
    # the same totals as the answer for one instrument, plus its code
    assert rows[-1] == dataclasses.replace(CLIENT_TYPE, ins_code=DIRAN)
    assert client_type.parse_client_type_all({"clientTypeAllDto": None}) == []


def test_parse_client_type_history(sample):
    days = client_type.parse_client_type_history(sample("client_type_history"))
    assert len(days) == 60
    # newest day first
    assert days[0] == client_type.ClientTypeHistory(
        date=datetime.date(2026, 11, 23),
        individual_buy_count=13,
        corporate_buy_count=0,
        individual_sell_count=75,
        corporate_sell_count=1,
        individual_buy_volume=860939,
        corporate_buy_volume=0,
        individual_sell_volume=703139,
        corporate_sell_volume=157800,
        individual_buy_value=20679754780,
        corporate_buy_value=0,
        individual_sell_value=16889398780,
        corporate_sell_value=3790356000,
        ins_code=DIRAN,
    )
    assert days[-1] == client_type.ClientTypeHistory(
        date=datetime.date(2026, 9, 1),
        individual_buy_count=494,
        corporate_buy_count=4,
        individual_sell_count=380,
        corporate_sell_count=5,
        individual_buy_volume=63435274,
        corporate_buy_volume=925141,
        individual_sell_volume=59656878,
        corporate_sell_volume=4703537,
        individual_buy_value=980414531870,
        corporate_buy_value=14302679860,
        individual_sell_value=922000529710,
        corporate_sell_value=72716682020,
        ins_code=DIRAN,
    )


# ---------------------------------------------------------------------------
# trade


def a_trade(number: int, **changes: Any) -> trade.Trade:
    """A trade with the values the samples have in the fields that are
    the same in every row."""
    values: dict[str, Any] = {
        "number": number,
        "time": datetime.time(9, 0, 35),
        "volume": 100,
        "price": 24020,
        "canceled": False,
        "ins_code": None,
        "date": None,
        "q_tit_ng_j": 0,
        "i_sens_var_p": "\x00",
        "p_ph_sea_cot_j": 0,
        "p_pb_sea_cot_j": 0,
        "i_anu_tran": 0,
        "xq_var_pj_dr_p_rf": 0.0,
    }
    return trade.Trade(**{**values, **changes})


def test_parse_trades(sample):
    trades = trade.parse_trades(sample("trades"))
    assert len(trades) == 100
    assert trades[0] == a_trade(1, volume=16000)
    assert trades[-1] == a_trade(
        99, time=datetime.time(12, 29, 51), volume=500
    )
    # the api sent trade 24 twice
    assert [t.number for t in trades[22:26]] == [23, 24, 24, 25]
    assert trades[23] == trades[24]
    assert trade.parse_trades({"trade": None}) == []


def test_parse_trade_history(sample):
    trades = trade.parse_trade_history(sample("trade_history"))
    assert len(trades) == 177
    assert trades[0] == a_trade(
        177, time=datetime.time(12, 27, 24), volume=5000, price=23330
    )
    assert trades[-1] == a_trade(6, volume=220, price=23330)
    assert sorted(t.number for t in trades) == list(range(1, 178))
    assert trade.parse_trade_history({"tradeHistory": []}) == []


def test_unique_trades_gives_every_trade_of_the_sample_once(sample):
    trades = trade.unique_trades(trade.parse_trades(sample("trades")))
    assert [t.number for t in trades] == list(range(1, 100))
    # the totals of the day in the closing_price_info sample
    assert sum(t.volume for t in trades) == 860939


def test_unique_trades_skips_canceled_and_repeated_trades():
    first = a_trade(1)
    canceled = a_trade(2, canceled=True)
    third = a_trade(3, volume=300)
    third_again = a_trade(3, volume=300)
    assert trade.unique_trades([third, first, canceled, third_again]) == [
        third,
        first,
    ]
    assert trade.unique_trades([]) == []


# ---------------------------------------------------------------------------
# shareholder


def test_parse_shareholders(sample):
    rows = shareholder.parse_shareholders(sample("shareholders"))
    assert len(rows) == 5
    assert rows[0] == shareholder.Shareholder(
        share_id=1429364,
        name="شركت گروه داروئي سبحان -سهامي عام -",
        company_isin="IRO1IRDR0007",
        date=None,
        shares=851537355,
        percentage=47.839,
        change=1,
        change_amount=0,
        shareholder_id=0,
    )
    assert rows[-1] == shareholder.Shareholder(
        share_id=1432292,
        name="شخص حقيقي",
        company_isin="IRO1IRDR0007",
        date=None,
        shares=24481108,
        percentage=1.375,
        change=1,
        change_amount=0,
        shareholder_id=0,
    )
    assert shareholder.parse_shareholders({"shareHolder": None}) == []


def test_parse_day_shareholders(sample):
    rows = shareholder.parse_day_shareholders(sample("day_shareholders"))
    # the shareholders of the next trading day, then the ones of the day
    assert [row.date for row in rows] == [
        *[datetime.date(2026, 11, 23)] * 5,
        *[DAY] * 5,
    ]
    assert rows[0] == shareholder.Shareholder(
        share_id=28211267,
        name="شركت گروه داروئي سبحان -سهامي عام -",
        company_isin="IRO1IRDR0007",
        date=datetime.date(2026, 11, 23),
        shares=851537355,
        percentage=47.839,
        change=1,
        change_amount=0,
        shareholder_id=0,
    )
    assert rows[-1] == shareholder.Shareholder(
        share_id=28198961,
        name="شركت سرمايه گذاري اعتلاءالبرز-سهامي عام -",
        company_isin="IRO1IRDR0007",
        date=DAY,
        shares=41909509,
        percentage=2.354,
        change=1,
        change_amount=0,
        shareholder_id=0,
    )


# ---------------------------------------------------------------------------
# instrument


def test_parse_instrument_info(sample):
    assert instrument.parse_instrument_info(
        sample("instrument_info")
    ) == instrument.InstrumentInfo(
        eps=instrument.InstrumentEps(
            estimated_eps=3064.0, sector_pe=11.85, psr=12734.175
        ),
        sector=instrument.InstrumentSector(
            name="مواد و محصولات دارويي", code="43 ", date=None
        ),
        static_threshold=instrument.StaticThreshold(
            max_price=24020,
            min_price=22640,
            ins_code=None,
            date=None,
            time=datetime.time(0, 0),
        ),
        min_week=22000,
        max_week=24020,
        min_year=3633,
        max_year=24790,
        month_average_volume=18051688,
        free_float=49.0,
        symbol="ديران",
        name="ايران‌دارو",
        flow=1,
        isin="IRO1IRDR0001",
        company_isin="IRO1IRDR0007",
        total_shares=1780000000,
        base_volume=1,
        ins_code=DIRAN,
        flow_title="بازار بورس",
        latin_name="Iran Darou",
        board_code="N2",
        board_title="بازار دوم (تابلوی اصلی) بورس",
        c_com_val="1",
        instrument_type="300",
        nav=0.0,
        contract_size=0,
        etf_issued_units=0,
        etf_unit_date=None,
        fara_desc="",
        under_supervision=0,
        top_inst=0,
        source_id=1,
        last_date=0,
        date=None,
    )


def test_parse_instrument_info_without_eps_threshold_and_free_float(sample):
    data = sample("instrument_info")
    data["instrumentInfo"]["eps"]["estimatedEPS"] = ""
    data["instrumentInfo"]["staticThreshold"] = None
    data["instrumentInfo"]["kAjCapValCpsIdx"] = ""
    data["instrumentInfo"]["zTitad"] = None
    info = instrument.parse_instrument_info(data)
    assert info.eps.estimated_eps is None
    assert info.static_threshold is None
    assert info.free_float is None
    assert info.total_shares is None


def test_parse_instrument_search(sample):
    results = instrument.parse_instrument_search(sample("instrument_search"))
    assert len(results) == 19
    assert results[0] == instrument.InstrumentSearchResult(
        ins_code=DIRAN,
        symbol="ديران",
        last_date=1,
        name="ايران‌دارو",
        flow=1,
        flow_title="بازار بورس",
        board_code="N2",
        board_title="بازار دوم بورس",
        retail_ins_code="24110439411336879",
        compensatory_ins_code="33411623986547832",
        block_ins_code="60505507009012750",
        source_id=1,
        company_isin=None,
        isin=None,
        c_com_val=None,
        total_shares=0,
        base_volume=0,
    )
    assert not results[0].is_deleted
    # the only old deleted instrument of the sample
    assert [row.symbol for row in results if row.is_deleted] == ["عماديران"]
    assert results[-1].ins_code == "14058161288052046"
    assert results[-1].last_date == 0


def test_parse_instrument_search_without_rows_or_last_date():
    assert instrument.parse_instrument_search({}) == []
    assert instrument.parse_instrument_search({"instrumentSearch": None}) == []
    [row] = instrument.parse_instrument_search(
        {
            "instrumentSearch": [
                {"insCode": 5, "lVal18AFC": "نماد", "lastDate": None}
            ]
        }
    )
    assert row == instrument.InstrumentSearchResult(
        ins_code="5", symbol="نماد", last_date=0
    )
    assert row.is_deleted


def test_parse_instrument_history(sample):
    assert instrument.parse_instrument_history(
        sample("instrument_history")
    ) == instrument.InstrumentHistory(
        total_shares=1780000000,
        base_volume=1,
        symbol="ديران",
        name="ايران‌دارو",
        flow=1,
        flow_title="بازار بورس",
        isin="IRO1IRDR0001",
        company_isin="IRO1IRDR0007",
        board_code="N2",
        board_title="بازار دوم (تابلوی اصلی) بورس",
        c_com_val="1",
        ins_code="0",
        last_date=0,
        source_id=0,
    )


# ---------------------------------------------------------------------------
# index


def test_parse_index_history(sample):
    days = index.parse_index_history(sample("index_history"))
    assert len(days) == 60
    # oldest day first; the code, a number in the json, is a str
    assert days[0] == index.IndexHistory(
        date=datetime.date(2026, 9, 1),
        close=6583932.3,
        low=6583930.0,
        high=6699460.0,
        ins_code=TOTAL_INDEX,
    )
    assert days[-1] == index.IndexHistory(
        date=datetime.date(2026, 11, 23),
        close=8389814.1,
        low=8380810.0,
        high=8447260.0,
        ins_code=TOTAL_INDEX,
    )
    assert index.parse_index_history({}) == []


def test_parse_index_intraday(sample):
    rows = index.parse_index_intraday(sample("index_intraday"))
    assert len(rows) == 126
    assert rows[0] == index.IndexIntraday(
        time=datetime.time(8, 30),
        value=8327077.7,
        change_percent=0.0,
        low=0.0,
        high=0.0,
        date=datetime.date(2026, 11, 23),
        change=0.0,
        last=False,
        ins_code=None,
        name=None,
        c1=0,
        c2=0,
        c3=0,
        c4=0,
    )
    assert rows[-1] == index.IndexIntraday(
        time=datetime.time(19, 4, 23),
        value=8389814.07,
        change_percent=0.7534,
        low=8380810.01,
        high=8447267.19,
        date=datetime.date(2026, 11, 23),
        change=0.0,
        last=True,
        ins_code=None,
        name=None,
        c1=0,
        c2=0,
        c3=0,
        c4=0,
    )
    assert index.parse_index_intraday({"indexB1": None}) == []


def test_parse_indices(sample):
    rows = index.parse_indices(sample("indices"))
    assert len(rows) == 58
    assert rows[0] == index.IndexLastValue(
        ins_code="34408080767216529",
        name="01-زراعت",
        time=datetime.time(19, 4, 22),
        value=1694011.84,
        change=28064.01,
        change_percent=1.6846,
        high=1694011.84,
        low=1685790.28,
        date=None,
        last=False,
        c1=0,
        c2=0,
        c3=0,
        c4=0,
    )
    [total] = [row for row in rows if row.ins_code == TOTAL_INDEX]
    assert total == index.IndexLastValue(
        ins_code=TOTAL_INDEX,
        name="شاخص كل",
        time=datetime.time(19, 4, 23),
        value=8389814.07,
        change=62736.37,
        change_percent=0.7534,
        high=8447267.19,
        low=8380810.01,
        date=None,
        last=False,
        c1=0,
        c2=0,
        c3=0,
        c4=0,
    )


def test_parse_index_companies(sample):
    companies = index.parse_index_companies(sample("index_companies"))
    assert [company.instrument.symbol for company in companies.companies] == [
        "خودرو",
        "ديران",
        "شستا",
        "فولاد",
    ]
    assert companies.companies[-1] == index.IndexCompany(
        ins_code="46348559193224090",
        instrument=index.IndexCompanyInstrument(
            symbol="فولاد",
            name="فولاد مباركه اصفهان",
            ins_code="46348559193224090",
            flow=0,
            total_shares=0,
            base_volume=0,
            last_date=0,
            source_id=0,
        ),
        closing_price=5120,
        price_change=140.0,
        last_price=5120,
        first_price=0,
        yesterday_price=4980,
        high_price=5120,
        low_price=5070,
        trade_count=26766,
        volume=2839687355,
        value=14535400168410,
        instrument_state=None,
        last_time=datetime.time(0, 0),
        last_date=None,
        notional_value=0,
        open_positions=0,
        nav=0,
        thirty_day_closing_history=None,
        last=False,
        id=0,
        date=None,
        time=datetime.time(0, 0),
        i_close=False,
        y_close=False,
    )
    assert len(companies.thirty_day_history) == 116
    assert companies.thirty_day_history[0] == index.IndexCompanyClosingPrice(
        ins_code=SHASTA,
        date=datetime.date(2026, 10, 14),
        closing_price=3970,
        last_price=0,
        trade_count=0,
        volume=0,
        value=0,
        time=datetime.time(0, 0),
        id=0,
        i_close=False,
        y_close=False,
    )
    assert companies.thirty_day_history[-1].ins_code == DIRAN
    assert companies.thirty_day_history[-1].closing_price == 24020
    assert index.parse_index_companies(
        {"indexCompany": None}
    ) == index.IndexCompanies(companies=[], thirty_day_history=[])


# ---------------------------------------------------------------------------
# fund and codal


def test_parse_etf(sample):
    assert fund.parse_etf(sample("etf")) == fund.Etf(
        redemption_nav=94233,
        date=datetime.date(2026, 11, 23),
        time=datetime.time(12, 33, 36),
        subscription_nav=95142,
        ins_code=FUND,
        i_close=0,
    )
    assert fund.parse_etf({"etf": None}) is None
    assert fund.parse_etf({}) is None


def test_parse_codal_publisher(sample):
    data = sample("codal_publisher")
    raw = data["codalPublisher"]
    assert codal.parse_codal_publisher(data) == codal.CodalPublisher(
        financial_year="09/30",
        id=44781019,
        symbol="ديران",
        display_symbol="ديران",
        name="ایران دارو",
        isic="432317",
        reporting_type="1000000",
        # the names, phone, fax and email of the sample are placeholders
        executive_manager="نام مدیر عامل",
        financial_manager="نام مدیر مالی",
        tel_no="02100000000",
        fax_no="02100000000",
        email="info@example.com",
        # long texts, as they are in the sample
        address=raw["address"],
        office_address=raw["officeAddress"],
        share_office_address=raw["shareOfficeAddress"],
        website=raw["website"],
        activity_subject=raw["activitySubject"],
        state="0",
        company_type="0",
        inspector="مفيد راهبر",
        auditor_name="موسسه حسابرسی مفید راهبر",
        # سرمایه ثبت شده, sent as the text "1780000"
        listed_capital=1780000,
        national_code="10100394490",
    )
    assert raw["address"].startswith("تهران")
    assert codal.parse_codal_publisher({"codalPublisher": None}) is None
    assert codal.parse_codal_publisher({}) is None


@pytest.mark.parametrize(
    "text, listed_capital",
    [
        ("1935000000", 1935000000),
        ("1,780,000", 1780000),
        ("", None),
        ("نامشخص", None),
    ],
)
def test_listed_capital_of_the_codal_publisher(sample, text, listed_capital):
    data = sample("codal_publisher")
    data["codalPublisher"]["listedCapital"] = text
    publisher = codal.parse_codal_publisher(data)
    assert publisher is not None
    assert publisher.listed_capital == listed_capital
    assert type(publisher.listed_capital) is type(listed_capital)


# ---------------------------------------------------------------------------
# _convert


def test_dates_and_times_of_the_api():
    assert _convert.to_date(20261116) == datetime.date(2026, 11, 16)
    assert _convert.to_optional_date(20261116) == datetime.date(2026, 11, 16)
    assert _convert.to_optional_date(0) is None
    assert _convert.to_optional_date(None) is None
    assert _convert.to_time(90017) == datetime.time(9, 0, 17)
    assert _convert.to_time(122952) == datetime.time(12, 29, 52)
    assert _convert.to_optional_time(0) == datetime.time(0, 0)
    assert _convert.to_optional_time(None) is None


@pytest.mark.parametrize(
    "convert, value, expected",
    [
        (_convert.to_optional_int, 24020.0, 24020),
        (_convert.to_optional_int, None, None),
        (_convert.to_optional_float, 3, 3.0),
        (_convert.to_optional_float, None, None),
        (_convert.to_optional_bool, 1, True),
        (_convert.to_optional_bool, False, False),
        (_convert.to_optional_bool, None, None),
        (_convert.to_optional_str, 32097828799138957, "32097828799138957"),
        (_convert.to_optional_str, None, None),
        (_convert.number_text_to_float, "693", 693.0),
        (_convert.number_text_to_float, "1,250.5", 1250.5),
        (_convert.number_text_to_float, 7.8, 7.8),
        (_convert.number_text_to_float, "", None),
        (_convert.number_text_to_float, None, None),
        (_convert.number_text_to_float, "-", None),
    ],
)
def test_optional_conversions(convert, value, expected):
    converted = convert(value)
    assert converted == expected
    assert type(converted) is type(expected)


# ---------------------------------------------------------------------------
# client


def endpoint_methods() -> list[str]:
    """Names of the call methods of the TsetmcApi protocol."""
    return [
        name for name in vars(client.TsetmcApi) if name.startswith("call_")
    ]


def test_every_endpoint_has_a_saved_response_and_a_parser():
    endpoints = {
        name.removeprefix("call_").removesuffix("_async")
        for name in endpoint_methods()
    }
    assert endpoints == set(PARSERS)
    assert {path.stem for path in DATA_DIR.glob("*.json")} == endpoints


def test_implementations_have_the_signatures_of_the_protocol(fake_api):
    assert len(endpoint_methods()) == 28
    for implementation in (type(fake_api), client.HttpTsetmcApi):
        for name in endpoint_methods():
            expected = inspect.signature(getattr(client.TsetmcApi, name))
            actual = inspect.signature(getattr(implementation, name))
            assert actual == expected, f"{implementation.__name__}.{name}"
            assert inspect.iscoroutinefunction(
                getattr(implementation, name)
            ) == name.endswith("_async")


def test_library_uses_the_fake_api_in_unit_tests(fake_api, sample):
    assert client.api is fake_api
    assert client.api.call_trades(DIRAN) == sample("trades")

    async def ask() -> Any:
        async with client.open_session(limit=1) as session:
            return await client.api.call_trade_history_async(
                DIRAN, DAY, session
            )

    assert asyncio.run(ask()) == sample("trade_history")
    assert fake_api.calls == [("trades", DIRAN), ("trade_history", DIRAN, DAY)]


def test_fake_api_can_answer_with_another_response_or_an_error(fake_api):
    fake_api.responses["etf"] = {"etf": None}
    fake_api.errors["trades"] = requests.ConnectionError("no answer")
    assert client.api.call_etf(FUND) == {"etf": None}
    with pytest.raises(requests.ConnectionError, match="no answer"):
        client.api.call_trades(DIRAN)


def test_unit_tests_cannot_reach_the_network():
    with pytest.raises(pytest.fail.Exception, match="tried to reach"):
        client.HttpTsetmcApi().call_market_overview()

    async def ask():
        async with client.open_session(limit=1) as session:
            await client.HttpTsetmcApi().call_instrument_info_async(
                DIRAN, session
            )

    with pytest.raises(pytest.fail.Exception, match="tried to reach"):
        asyncio.run(ask())


class Transport:
    """Stands in for the network under requests: keeps the requests that
    are sent and answers each one with the given status and body."""

    def __init__(
        self, monkeypatch: pytest.MonkeyPatch, status: int, body: bytes
    ) -> None:
        self.sent: list[requests.PreparedRequest] = []
        self.status = status
        self.body = body
        monkeypatch.setattr(HTTPAdapter, "send", self.send)

    def send(
        self, request: requests.PreparedRequest, **kwargs: Any
    ) -> requests.Response:
        self.sent.append(request)
        response = requests.Response()
        response.status_code = self.status
        response.raw = io.BytesIO(self.body)
        response.url = request.url or ""
        response.request = request
        return response


API = "https://cdn.tsetmc.com/api"
# the text فولاد the way it is sent in a url
FOLAD_IN_URL = "%D9%81%D9%88%D9%84%D8%A7%D8%AF"
# the market watch of every paper type with the order book of each row;
# the [ and ] of the parameter names are sent as %5B and %5D
MARKET_WATCH_URL = (
    f"{API}/ClosingPrice/GetMarketWatch?market=0&industrialGroup="
    "&paperTypes%5B0%5D=1&paperTypes%5B1%5D=2&paperTypes%5B2%5D=3"
    "&paperTypes%5B3%5D=4&paperTypes%5B4%5D=5&paperTypes%5B5%5D=6"
    "&paperTypes%5B6%5D=7&paperTypes%5B7%5D=8&paperTypes%5B8%5D=9"
    "&showTraded=false&withBestLimits=true"
)

# method of HttpTsetmcApi, its arguments -> the url it asks for
SYNC_URLS = [
    ("call_market_overview", (), f"{API}/MarketData/GetMarketOverview/1"),
    ("call_market_watch", (), MARKET_WATCH_URL),
    (
        "call_key_stats",
        (),
        f"{API}/MarketData/GetInstValueAllInstAllParam",
    ),
    (
        "call_closing_price_info",
        (DIRAN,),
        f"{API}/ClosingPrice/GetClosingPriceInfo/{DIRAN}",
    ),
    (
        "call_closing_price_daily_list",
        (DIRAN,),
        f"{API}/ClosingPrice/GetClosingPriceDailyList/{DIRAN}/0",
    ),
    (
        "call_recent_closing_price_daily_list",
        (DIRAN,),
        f"{API}/ClosingPrice/GetClosingPriceDailyList/{DIRAN}/12",
    ),
    (
        "call_closing_price_daily_all_inst",
        (),
        f"{API}/ClosingPrice/GetClosingPriceDailyAllInst",
    ),
    ("call_best_limits", (DIRAN,), f"{API}/BestLimits/{DIRAN}"),
    (
        "call_best_limits_history",
        (DIRAN, DAY),
        f"{API}/BestLimits/{DIRAN}/20261122",
    ),
    (
        "call_client_type",
        (DIRAN,),
        f"{API}/ClientType/GetClientType/{DIRAN}/1/0",
    ),
    ("call_client_type_all", (), f"{API}/ClientType/GetClientTypeAll"),
    (
        "call_client_type_history",
        (DIRAN,),
        f"{API}/ClientType/GetClientTypeHistory/{DIRAN}",
    ),
    ("call_trades", (DIRAN,), f"{API}/Trade/GetTrade/{DIRAN}"),
    (
        "call_shareholders",
        (DIRAN,),
        f"{API}/Shareholder/GetInstrumentShareHolderLast/{DIRAN}",
    ),
    (
        "call_instrument_info",
        (DIRAN,),
        f"{API}/Instrument/GetInstrumentInfo/{DIRAN}",
    ),
    (
        "call_instrument_search",
        (" فولاد ",),
        f"{API}/Instrument/GetInstrumentSearch/{FOLAD_IN_URL}",
    ),
    (
        "call_index_history",
        (TOTAL_INDEX,),
        f"{API}/Index/GetIndexB2History/{TOTAL_INDEX}",
    ),
    (
        "call_index_intraday",
        (TOTAL_INDEX,),
        f"{API}/Index/GetIndexB1LastDay/{TOTAL_INDEX}",
    ),
    ("call_indices", (2,), f"{API}/Index/GetIndexB1LastAll/All/2"),
    (
        "call_index_companies",
        (TOTAL_INDEX,),
        f"{API}/ClosingPrice/GetIndexCompany/{TOTAL_INDEX}",
    ),
    ("call_etf", (FUND,), f"{API}/Fund/GetETFByInsCode/{FUND}"),
    (
        "call_codal_publisher",
        ("فولاد",),
        f"{API}/Codal/GetCodalPublisherBySymbol/{FOLAD_IN_URL}",
    ),
]


@pytest.mark.parametrize("method, args, url", SYNC_URLS)
def test_http_api_asks_the_url_of_the_endpoint(monkeypatch, method, args, url):
    transport = Transport(monkeypatch, 200, b'{"rows": [1, 2]}')
    answer = getattr(client.HttpTsetmcApi(), method)(*args)
    assert answer == {"rows": [1, 2]}
    [request] = transport.sent
    assert request.method == "GET"
    assert request.url == url
    assert request.headers["Referer"] == "https://www.tsetmc.com/"


def test_http_api_has_a_call_for_every_sync_method_of_the_protocol():
    assert [method for method, _, _ in SYNC_URLS] == [
        name for name in endpoint_methods() if not name.endswith("_async")
    ]


def test_http_api_raises_for_an_error_status_or_a_body_that_is_no_json(
    monkeypatch,
):
    Transport(monkeypatch, 404, b"{}")
    with pytest.raises(requests.HTTPError, match="404"):
        client.HttpTsetmcApi().call_trades(DIRAN)
    # the api answers 500 for an instrument that is not a fund
    Transport(monkeypatch, 500, b"{}")
    with pytest.raises(requests.HTTPError, match="500"):
        client.HttpTsetmcApi().call_etf(DIRAN)
    Transport(monkeypatch, 200, b"<html>")
    with pytest.raises(requests.RequestException):
        client.HttpTsetmcApi().call_trades(DIRAN)


class Answer:
    """One answer of a Session: the response of aiohttp and the context
    manager that session.get returns."""

    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body

    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(self, *error: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientError(f"status {self.status}")

    async def text(self) -> str:
        return self.body


@dataclasses.dataclass
class Session:
    """Stands in for an aiohttp session: keeps the requests that are sent
    and gives every one of them the same answer."""

    answer: Answer
    urls: list[str] = dataclasses.field(default_factory=list)
    headers: list[dict[str, str]] = dataclasses.field(default_factory=list)

    def get(
        self, url: Any, headers: dict[str, str], timeout: Any, ssl: Any
    ) -> Answer:
        self.urls.append(str(url))
        self.headers.append(headers)
        return self.answer


def ask_async(session: Session, method: str, *args: Any) -> Any:
    """The answer of an async method of HttpTsetmcApi on a session."""
    call = getattr(client.HttpTsetmcApi(), method)
    return asyncio.run(call(*args, session))


ASYNC_URLS = [
    (
        "call_best_limits_history_async",
        (DIRAN, DAY),
        f"{API}/BestLimits/{DIRAN}/20261122",
    ),
    (
        "call_trade_history_async",
        (DIRAN, DAY),
        f"{API}/Trade/GetTradeHistory/{DIRAN}/20261122/false",
    ),
    (
        "call_day_shareholders_async",
        (DIRAN, DAY),
        f"{API}/Shareholder/{DIRAN}/20261122",
    ),
    (
        "call_instrument_info_async",
        (DIRAN,),
        f"{API}/Instrument/GetInstrumentInfo/{DIRAN}",
    ),
    (
        "call_instrument_search_async",
        (" فولاد ",),
        f"{API}/Instrument/GetInstrumentSearch/{FOLAD_IN_URL}",
    ),
    (
        "call_instrument_history_async",
        (DIRAN, DAY),
        f"{API}/Instrument/GetInstrumentHistory/{DIRAN}/20261122",
    ),
]


@pytest.mark.parametrize("method, args, url", ASYNC_URLS)
def test_http_api_asks_the_url_of_the_endpoint_async(method, args, url):
    session = Session(Answer(200, '{"rows": [1, 2]}'))
    assert ask_async(session, method, *args) == {"rows": [1, 2]}
    assert session.urls == [url]
    assert session.headers[0]["User-Agent"].startswith("Mozilla/5.0")


def test_http_api_has_a_call_for_every_async_method_of_the_protocol():
    assert [method for method, _, _ in ASYNC_URLS] == [
        name for name in endpoint_methods() if name.endswith("_async")
    ]


def test_http_api_sends_the_page_of_the_day_as_referer_of_its_history():
    session = Session(Answer(200, "{}"))
    ask_async(session, "call_instrument_history_async", DIRAN, DAY)
    assert session.headers[0]["Referer"] == (
        f"https://www.tsetmc.com/History/{DIRAN}/20261122"
    )


def test_open_session_limits_the_requests_on_the_way():
    async def limit_of_new_session() -> int:
        async with client.open_session(limit=7) as session:
            assert isinstance(session, aiohttp.ClientSession)
            connector = session.connector
            assert connector is not None
            return connector.limit

    assert asyncio.run(limit_of_new_session()) == 7
