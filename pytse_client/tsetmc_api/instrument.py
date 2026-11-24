import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import (
    number_text_to_float,
    to_optional_date,
    to_optional_float,
    to_optional_int,
    to_optional_str,
    to_optional_time,
)


@dataclass(frozen=True, slots=True)
class InstrumentEps:
    estimated_eps: float | None
    sector_pe: float | None
    # sales per share
    psr: float | None
    eps_value: float | None = None


@dataclass(frozen=True, slots=True)
class InstrumentSector:
    name: str | None
    # padded with a space, e.g. "27 "
    code: str | None = None
    date: datetime.date | None = None


@dataclass(frozen=True, slots=True)
class StaticThreshold:
    # allowed price range of the day
    max_price: int | None
    min_price: int | None
    ins_code: str | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None


@dataclass(frozen=True, slots=True)
class InstrumentInfo:
    eps: InstrumentEps
    sector: InstrumentSector
    static_threshold: StaticThreshold | None
    min_week: int | None
    max_week: int | None
    min_year: int | None
    max_year: int | None
    # average daily volume of the last month
    month_average_volume: int | None
    # percent
    free_float: float | None
    symbol: str
    name: str
    # 1 بازار بورس, 2 بازار فرابورس, 3 بازار مشتقه
    flow: int | None
    isin: str | None
    company_isin: str | None
    total_shares: int | None
    base_volume: int | None
    ins_code: str | None = None
    flow_title: str | None = None
    latin_name: str | None = None
    board_code: str | None = None
    board_title: str | None = None
    c_com_val: str | None = None
    # "300" for a share
    instrument_type: str | None = None
    nav: float | None = None
    # options and futures only
    contract_size: int | None = None
    etf_issued_units: int | None = None
    etf_unit_date: datetime.date | None = None
    # text shown under the title on the website
    fara_desc: str | None = None
    under_supervision: int | None = None
    top_inst: int | None = None
    # 1 بورس, 2 فرابورس
    source_id: int | None = None
    last_date: int | None = None
    date: datetime.date | None = None
    c_val_mne: str | None = None
    c_soc_csac: str | None = None
    l_soc30: str | None = None
    market_code: str | None = None


def parse_instrument_info(data: Any) -> InstrumentInfo:
    info = data["instrumentInfo"]
    eps = info["eps"]
    sector = info["sector"]
    threshold = info["staticThreshold"]
    return InstrumentInfo(
        eps=InstrumentEps(
            estimated_eps=number_text_to_float(eps["estimatedEPS"]),
            sector_pe=number_text_to_float(eps["sectorPE"]),
            psr=number_text_to_float(eps["psr"]),
            eps_value=to_optional_float(eps.get("epsValue")),
        ),
        sector=InstrumentSector(
            name=sector["lSecVal"],
            code=sector.get("cSecVal"),
            date=to_optional_date(sector.get("dEven")),
        ),
        static_threshold=(
            StaticThreshold(
                max_price=to_optional_int(threshold["psGelStaMax"]),
                min_price=to_optional_int(threshold["psGelStaMin"]),
                ins_code=threshold.get("insCode"),
                date=to_optional_date(threshold.get("dEven")),
                time=to_optional_time(threshold.get("hEven")),
            )
            if threshold
            else None
        ),
        min_week=to_optional_int(info["minWeek"]),
        max_week=to_optional_int(info["maxWeek"]),
        min_year=to_optional_int(info["minYear"]),
        max_year=to_optional_int(info["maxYear"]),
        month_average_volume=to_optional_int(info["qTotTran5JAvg"]),
        free_float=number_text_to_float(info["kAjCapValCpsIdx"]),
        symbol=info["lVal18AFC"],
        name=info["lVal30"],
        flow=to_optional_int(info["flow"]),
        isin=info["instrumentID"],
        company_isin=info["cIsin"],
        total_shares=to_optional_int(info["zTitad"]),
        base_volume=to_optional_int(info["baseVol"]),
        ins_code=to_optional_str(info.get("insCode")),
        flow_title=info.get("flowTitle"),
        latin_name=info.get("lVal18"),
        board_code=info.get("cgrValCot"),
        board_title=info.get("cgrValCotTitle"),
        c_com_val=info.get("cComVal"),
        instrument_type=to_optional_str(info.get("yVal")),
        nav=to_optional_float(info.get("nav")),
        contract_size=to_optional_int(info.get("contractSize")),
        etf_issued_units=to_optional_int(info.get("etfIssuedUnit")),
        etf_unit_date=to_optional_date(info.get("etfUnitDeven")),
        fara_desc=info.get("faraDesc"),
        under_supervision=to_optional_int(info.get("underSupervision")),
        top_inst=to_optional_int(info.get("topInst")),
        source_id=to_optional_int(info.get("sourceID")),
        last_date=to_optional_int(info.get("lastDate")),
        date=to_optional_date(info.get("dEven")),
        c_val_mne=info.get("cValMne"),
        c_soc_csac=info.get("cSocCSAC"),
        l_soc30=info.get("lSoc30"),
        market_code=info.get("yMarNSC"),
    )


@dataclass(frozen=True, slots=True)
class InstrumentSearchResult:
    ins_code: str
    symbol: str | None
    # 0 for an old deleted instrument, 1 otherwise
    last_date: int
    name: str | None = None
    flow: int | None = None
    flow_title: str | None = None
    # "E1" for the energy exchange
    board_code: str | None = None
    board_title: str | None = None
    # the same symbol on the odd lot market
    retail_ins_code: str | None = None
    # the same symbol on the compensatory market
    compensatory_ins_code: str | None = None
    # the same symbol on the block trade market
    block_ins_code: str | None = None
    # 1 بورس, 2 فرابورس
    source_id: int | None = None
    company_isin: str | None = None
    isin: str | None = None
    c_com_val: str | None = None
    total_shares: int | None = None
    base_volume: int | None = None

    @property
    def is_deleted(self) -> bool:
        return not self.last_date


def parse_instrument_search(data: Any) -> list[InstrumentSearchResult]:
    return [
        InstrumentSearchResult(
            ins_code=str(row["insCode"]),
            symbol=row["lVal18AFC"],
            last_date=int(row["lastDate"] or 0),
            name=row.get("lVal30"),
            flow=to_optional_int(row.get("flow")),
            flow_title=row.get("flowTitle"),
            board_code=row.get("cgrValCot"),
            board_title=row.get("cgrValCotTitle"),
            retail_ins_code=to_optional_str(row.get("insCode2")),
            compensatory_ins_code=to_optional_str(row.get("insCode3")),
            block_ins_code=to_optional_str(row.get("insCode4")),
            source_id=to_optional_int(row.get("sourceID")),
            company_isin=row.get("cIsin"),
            isin=row.get("instrumentID"),
            c_com_val=row.get("cComVal"),
            total_shares=to_optional_int(row.get("zTitad")),
            base_volume=to_optional_int(row.get("baseVol")),
        )
        for row in data.get("instrumentSearch") or []
    ]


@dataclass(frozen=True, slots=True)
class InstrumentHistory:
    total_shares: int
    base_volume: int
    symbol: str | None = None
    name: str | None = None
    flow: int | None = None
    flow_title: str | None = None
    isin: str | None = None
    company_isin: str | None = None
    board_code: str | None = None
    board_title: str | None = None
    c_com_val: str | None = None
    ins_code: str | None = None
    last_date: int | None = None
    source_id: int | None = None


def parse_instrument_history(data: Any) -> InstrumentHistory:
    history = data["instrumentHistory"]
    return InstrumentHistory(
        total_shares=int(history["zTitad"]),
        base_volume=int(history["baseVol"]),
        symbol=history.get("lVal18AFC"),
        name=history.get("lVal30"),
        flow=to_optional_int(history.get("flow")),
        flow_title=history.get("flowTitle"),
        isin=history.get("instrumentID"),
        company_isin=history.get("cIsin"),
        board_code=history.get("cgrValCot"),
        board_title=history.get("cgrValCotTitle"),
        c_com_val=history.get("cComVal"),
        ins_code=to_optional_str(history.get("insCode")),
        last_date=to_optional_int(history.get("lastDate")),
        source_id=to_optional_int(history.get("sourceID")),
    )
