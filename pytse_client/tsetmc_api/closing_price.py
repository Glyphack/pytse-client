import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import (
    to_date,
    to_optional_bool,
    to_optional_date,
    to_optional_float,
    to_optional_int,
    to_optional_time,
)


@dataclass(frozen=True, slots=True)
class InstrumentState:
    # two letters padded with a space: "A " مجاز, "I " ممنوع,
    # "AS" مجاز-متوقف, "IS" ممنوع-متوقف, ...
    code: str | None
    title: str | None
    idn: int | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    ins_code: str | None = None
    symbol: str | None = None
    name: str | None = None
    real_time: datetime.time | None = None
    under_supervision: int | None = None


@dataclass(frozen=True, slots=True)
class ClosingPriceInfo:
    instrument_state: InstrumentState | None
    last_price: int | None
    closing_price: int | None
    yesterday_price: int | None
    first_price: int | None
    high_price: int | None
    low_price: int | None
    trade_count: int | None
    volume: int | None
    value: int | None
    date: datetime.date | None
    time: datetime.time | None
    last_time: datetime.time | None = None
    # last trading day of the instrument
    last_date: datetime.date | None = None
    # options only
    notional_value: int | None = None
    # options and futures only
    open_positions: int | None = None
    nav: int | None = None
    price_change: float | None = None
    last: bool | None = None
    id: int | None = None
    ins_code: str | None = None
    i_close: bool | None = None
    y_close: bool | None = None
    instrument: Any | None = None
    thirty_day_closing_history: Any | None = None


def parse_closing_price_info(data: Any) -> ClosingPriceInfo | None:
    info = data["closingPriceInfo"]
    if not info:
        return None
    state = info["instrumentState"]
    instrument_state = None
    if state:
        instrument_state = InstrumentState(
            code=state["cEtaval"],
            title=state["cEtavalTitle"],
            idn=state.get("idn"),
            date=to_optional_date(state.get("dEven")),
            time=to_optional_time(state.get("hEven")),
            ins_code=state.get("insCode"),
            symbol=state.get("lVal18AFC"),
            name=state.get("lVal30"),
            real_time=to_optional_time(state.get("realHeven")),
            under_supervision=state.get("underSupervision"),
        )
    return ClosingPriceInfo(
        instrument_state=instrument_state,
        last_price=to_optional_int(info["pDrCotVal"]),
        closing_price=to_optional_int(info["pClosing"]),
        yesterday_price=to_optional_int(info["priceYesterday"]),
        first_price=to_optional_int(info["priceFirst"]),
        high_price=to_optional_int(info["priceMax"]),
        low_price=to_optional_int(info["priceMin"]),
        trade_count=to_optional_int(info["zTotTran"]),
        volume=to_optional_int(info["qTotTran5J"]),
        value=to_optional_int(info["qTotCap"]),
        date=to_optional_date(info["dEven"]),
        time=to_optional_time(info["hEven"]),
        last_time=to_optional_time(info.get("lastHEven")),
        last_date=to_optional_date(info.get("finalLastDate")),
        notional_value=to_optional_int(info.get("nvt")),
        open_positions=to_optional_int(info.get("mop")),
        nav=to_optional_int(info.get("pRedTran")),
        price_change=to_optional_float(info.get("priceChange")),
        last=to_optional_bool(info.get("last")),
        id=info.get("id"),
        ins_code=info.get("insCode"),
        i_close=to_optional_bool(info.get("iClose")),
        y_close=to_optional_bool(info.get("yClose")),
        instrument=info.get("instrument"),
        thirty_day_closing_history=info.get("thirtyDayClosingHistory"),
    )


@dataclass(frozen=True, slots=True)
class ClosingPriceDaily:
    date: datetime.date
    first_price: int
    high_price: int
    low_price: int
    closing_price: int
    last_price: int
    yesterday_price: int
    trade_count: int
    volume: int
    value: int
    # last trade price minus yesterday's price
    price_change: float | None = None
    time: datetime.time | None = None
    ins_code: str | None = None
    last: bool | None = None
    id: int | None = None
    i_close: bool | None = None
    y_close: bool | None = None


def parse_closing_price_daily_list(data: Any) -> list[ClosingPriceDaily]:
    return [
        ClosingPriceDaily(
            date=to_date(row["dEven"]),
            first_price=int(row["priceFirst"]),
            high_price=int(row["priceMax"]),
            low_price=int(row["priceMin"]),
            closing_price=int(row["pClosing"]),
            last_price=int(row["pDrCotVal"]),
            yesterday_price=int(row["priceYesterday"]),
            trade_count=int(row["zTotTran"]),
            volume=int(row["qTotTran5J"]),
            value=int(row["qTotCap"]),
            price_change=to_optional_float(row.get("priceChange")),
            time=to_optional_time(row.get("hEven")),
            ins_code=row.get("insCode"),
            last=to_optional_bool(row.get("last")),
            id=row.get("id"),
            i_close=to_optional_bool(row.get("iClose")),
            y_close=to_optional_bool(row.get("yClose")),
        )
        for row in data["closingPriceDaily"] or []
    ]


@dataclass(frozen=True, slots=True)
class ClosingPriceDailyAllInst:
    ins_code: str
    date: datetime.date | None = None
    time: datetime.time | None = None
    first_price: int | None = None
    high_price: int | None = None
    low_price: int | None = None
    closing_price: int | None = None
    last_price: int | None = None
    yesterday_price: int | None = None
    trade_count: int | None = None
    volume: int | None = None
    value: int | None = None
    offset: int | None = None
    id: int | None = None
    i_close: bool | None = None
    y_close: bool | None = None


def parse_closing_price_daily_all_inst(
    data: Any,
) -> list[ClosingPriceDailyAllInst]:
    return [
        ClosingPriceDailyAllInst(
            ins_code=row["insCode"],
            date=to_optional_date(row.get("dEven")),
            time=to_optional_time(row.get("hEven")),
            first_price=to_optional_int(row.get("priceFirst")),
            high_price=to_optional_int(row.get("priceMax")),
            low_price=to_optional_int(row.get("priceMin")),
            closing_price=to_optional_int(row.get("pClosing")),
            last_price=to_optional_int(row.get("pDrCotVal")),
            yesterday_price=to_optional_int(row.get("priceYesterday")),
            trade_count=to_optional_int(row.get("zTotTran")),
            volume=to_optional_int(row.get("qTotTran5J")),
            value=to_optional_int(row.get("qTotCap")),
            offset=row.get("offset"),
            id=row.get("id"),
            i_close=to_optional_bool(row.get("iClose")),
            y_close=to_optional_bool(row.get("yClose")),
        )
        for row in data["closingPriceDailyAllInst"] or []
    ]
