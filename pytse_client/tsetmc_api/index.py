import datetime
from dataclasses import dataclass, field
from typing import Any

from pytse_client.tsetmc_api._convert import (
    to_date,
    to_optional_bool,
    to_optional_date,
    to_optional_float,
    to_optional_int,
    to_optional_str,
    to_optional_time,
    to_time,
)


@dataclass(frozen=True, slots=True)
class IndexHistory:
    date: datetime.date
    close: float
    low: float
    high: float
    ins_code: str | None = None


def parse_index_history(data: Any) -> list[IndexHistory]:
    return [
        IndexHistory(
            date=to_date(row["dEven"]),
            close=float(row["xNivInuClMresIbs"]),
            low=float(row["xNivInuPbMresIbs"]),
            high=float(row["xNivInuPhMresIbs"]),
            ins_code=to_optional_str(row.get("insCode")),
        )
        for row in data.get("indexB2") or []
    ]


@dataclass(frozen=True, slots=True)
class IndexIntraday:
    time: datetime.time
    value: float
    # since the previous day
    change_percent: float
    # low and high: of the day so far, 0 before the open
    low: float
    high: float
    date: datetime.date | None = None
    change: float | None = None
    # true for the newest row
    last: bool | None = None
    ins_code: str | None = None
    name: str | None = None
    c1: int | None = None
    c2: int | None = None
    c3: int | None = None
    c4: int | None = None


def parse_index_intraday(data: Any) -> list[IndexIntraday]:
    return [
        IndexIntraday(
            time=to_time(row["hEven"]),
            value=float(row["xDrNivJIdx004"]),
            change_percent=float(row["xVarIdxJRfV"]),
            low=float(row["xPbNivJIdx004"]),
            high=float(row["xPhNivJIdx004"]),
            date=to_optional_date(row.get("dEven")),
            change=to_optional_float(row.get("indexChange")),
            last=to_optional_bool(row.get("last")),
            ins_code=to_optional_str(row.get("insCode")),
            name=row.get("lVal30"),
            c1=row.get("c1"),
            c2=row.get("c2"),
            c3=row.get("c3"),
            c4=row.get("c4"),
        )
        for row in data["indexB1"] or []
    ]


@dataclass(frozen=True, slots=True)
class IndexLastValue:
    ins_code: str
    # sometimes holds the sector number, e.g. "27-فلزات اساسي"
    name: str
    time: datetime.time | None = None
    value: float | None = None
    change: float | None = None
    change_percent: float | None = None
    high: float | None = None
    low: float | None = None
    date: datetime.date | None = None
    last: bool | None = None
    c1: int | None = None
    c2: int | None = None
    c3: int | None = None
    c4: int | None = None


def parse_indices(data: Any) -> list[IndexLastValue]:
    return [
        IndexLastValue(
            ins_code=str(row["insCode"]),
            name=row["lVal30"],
            time=to_optional_time(row.get("hEven")),
            value=to_optional_float(row.get("xDrNivJIdx004")),
            change=to_optional_float(row.get("indexChange")),
            change_percent=to_optional_float(row.get("xVarIdxJRfV")),
            high=to_optional_float(row.get("xPhNivJIdx004")),
            low=to_optional_float(row.get("xPbNivJIdx004")),
            date=to_optional_date(row.get("dEven")),
            last=to_optional_bool(row.get("last")),
            c1=row.get("c1"),
            c2=row.get("c2"),
            c3=row.get("c3"),
            c4=row.get("c4"),
        )
        for row in data["indexB1"] or []
    ]


@dataclass(frozen=True, slots=True)
class IndexCompanyInstrument:
    symbol: str
    name: str | None = None
    ins_code: str | None = None
    c_val_mne: str | None = None
    latin_name: str | None = None
    c_soc_csac: str | None = None
    l_soc30: str | None = None
    market_code: str | None = None
    instrument_type: str | None = None
    flow: int | None = None
    company_isin: str | None = None
    total_shares: int | None = None
    base_volume: int | None = None
    isin: str | None = None
    board_code: str | None = None
    c_com_val: str | None = None
    last_date: int | None = None
    source_id: int | None = None
    flow_title: str | None = None
    board_title: str | None = None


@dataclass(frozen=True, slots=True)
class IndexCompany:
    ins_code: str
    instrument: IndexCompanyInstrument
    closing_price: int | None = None
    # last trade price minus yesterday's price
    price_change: float | None = None
    last_price: int | None = None
    first_price: int | None = None
    yesterday_price: int | None = None
    high_price: int | None = None
    low_price: int | None = None
    trade_count: int | None = None
    volume: int | None = None
    value: int | None = None
    instrument_state: Any | None = None
    last_time: datetime.time | None = None
    last_date: datetime.date | None = None
    notional_value: int | None = None
    open_positions: int | None = None
    nav: int | None = None
    thirty_day_closing_history: Any | None = None
    last: bool | None = None
    id: int | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    i_close: bool | None = None
    y_close: bool | None = None


@dataclass(frozen=True, slots=True)
class IndexCompanyClosingPrice:
    ins_code: str | None = None
    date: datetime.date | None = None
    closing_price: int | None = None
    last_price: int | None = None
    trade_count: int | None = None
    volume: int | None = None
    value: int | None = None
    time: datetime.time | None = None
    id: int | None = None
    i_close: bool | None = None
    y_close: bool | None = None


@dataclass(frozen=True, slots=True)
class IndexCompanies:
    companies: list[IndexCompany]
    thirty_day_history: list[IndexCompanyClosingPrice] = field(
        default_factory=list
    )


def parse_index_companies(data: Any) -> IndexCompanies:
    companies = []
    for row in data["indexCompany"] or []:
        instrument = row["instrument"]
        companies.append(
            IndexCompany(
                ins_code=str(row["insCode"]),
                instrument=IndexCompanyInstrument(
                    symbol=instrument["lVal18AFC"],
                    name=instrument.get("lVal30"),
                    ins_code=to_optional_str(instrument.get("insCode")),
                    c_val_mne=instrument.get("cValMne"),
                    latin_name=instrument.get("lVal18"),
                    c_soc_csac=instrument.get("cSocCSAC"),
                    l_soc30=instrument.get("lSoc30"),
                    market_code=instrument.get("yMarNSC"),
                    instrument_type=to_optional_str(instrument.get("yVal")),
                    flow=instrument.get("flow"),
                    company_isin=instrument.get("cIsin"),
                    total_shares=to_optional_int(instrument.get("zTitad")),
                    base_volume=to_optional_int(instrument.get("baseVol")),
                    isin=instrument.get("instrumentID"),
                    board_code=instrument.get("cgrValCot"),
                    c_com_val=instrument.get("cComVal"),
                    last_date=instrument.get("lastDate"),
                    source_id=instrument.get("sourceID"),
                    flow_title=instrument.get("flowTitle"),
                    board_title=instrument.get("cgrValCotTitle"),
                ),
                closing_price=to_optional_int(row.get("pClosing")),
                price_change=to_optional_float(row.get("priceChange")),
                last_price=to_optional_int(row.get("pDrCotVal")),
                first_price=to_optional_int(row.get("priceFirst")),
                yesterday_price=to_optional_int(row.get("priceYesterday")),
                high_price=to_optional_int(row.get("priceMax")),
                low_price=to_optional_int(row.get("priceMin")),
                trade_count=to_optional_int(row.get("zTotTran")),
                volume=to_optional_int(row.get("qTotTran5J")),
                value=to_optional_int(row.get("qTotCap")),
                instrument_state=row.get("instrumentState"),
                last_time=to_optional_time(row.get("lastHEven")),
                last_date=to_optional_date(row.get("finalLastDate")),
                notional_value=to_optional_int(row.get("nvt")),
                open_positions=to_optional_int(row.get("mop")),
                nav=to_optional_int(row.get("pRedTran")),
                thirty_day_closing_history=row.get("thirtyDayClosingHistory"),
                last=to_optional_bool(row.get("last")),
                id=row.get("id"),
                date=to_optional_date(row.get("dEven")),
                time=to_optional_time(row.get("hEven")),
                i_close=to_optional_bool(row.get("iClose")),
                y_close=to_optional_bool(row.get("yClose")),
            )
        )
    thirty_day_history = [
        IndexCompanyClosingPrice(
            ins_code=to_optional_str(row.get("insCode")),
            date=to_optional_date(row.get("dEven")),
            closing_price=to_optional_int(row.get("pClosing")),
            last_price=to_optional_int(row.get("pDrCotVal")),
            trade_count=to_optional_int(row.get("zTotTran")),
            volume=to_optional_int(row.get("qTotTran5J")),
            value=to_optional_int(row.get("qTotCap")),
            time=to_optional_time(row.get("hEven")),
            id=row.get("id"),
            i_close=to_optional_bool(row.get("iClose")),
            y_close=to_optional_bool(row.get("yClose")),
        )
        for row in data.get("relatedCompanyThirtyDayHistory") or []
    ]
    return IndexCompanies(
        companies=companies, thirty_day_history=thirty_day_history
    )
