import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import (
    number_text_to_float,
    to_date,
    to_optional_bool,
    to_optional_date,
    to_optional_float,
    to_optional_int,
    to_optional_time,
    to_time,
)


@dataclass(frozen=True, slots=True)
class MarketOverview:
    last_trade_date: datetime.date
    last_trade_time: datetime.time | None = None
    # the main index of the exchange
    index_value: float | None = None
    index_change: float | None = None
    equal_weighted_index_value: float | None = None
    equal_weighted_index_change: float | None = None
    trade_count: int | None = None
    trade_volume: int | None = None
    trade_value: int | None = None
    market_value: int | None = None
    # set for fara bourse (flow 2) only, 0 for flow 1
    base_market_value: int | None = None
    # e.g. "F" when the market is closed
    state: str | None = None
    state_title: str | None = None
    last_data_date: datetime.date | None = None
    last_data_time: datetime.time | None = None


def parse_market_overview(data: Any) -> MarketOverview:
    overview = data["marketOverview"]
    return MarketOverview(
        last_trade_date=to_date(overview["marketActivityDEven"]),
        last_trade_time=to_optional_time(overview.get("marketActivityHEven")),
        index_value=to_optional_float(overview.get("indexLastValue")),
        index_change=to_optional_float(overview.get("indexChange")),
        equal_weighted_index_value=to_optional_float(
            overview.get("indexEqualWeightedLastValue")
        ),
        equal_weighted_index_change=to_optional_float(
            overview.get("indexEqualWeightedChange")
        ),
        trade_count=to_optional_int(overview.get("marketActivityZTotTran")),
        trade_volume=to_optional_int(overview.get("marketActivityQTotTran")),
        trade_value=to_optional_int(overview.get("marketActivityQTotCap")),
        market_value=to_optional_int(overview.get("marketValue")),
        base_market_value=to_optional_int(overview.get("marketValueBase")),
        state=overview.get("marketState"),
        state_title=overview.get("marketStateTitle"),
        last_data_date=to_optional_date(overview.get("lastDataDEven")),
        last_data_time=to_optional_time(overview.get("lastDataHEven")),
    )


@dataclass(frozen=True, slots=True)
class MarketWatchBestLimit:
    # 1 is the best price
    level: int
    # number of orders
    buy_count: int
    buy_volume: int
    buy_price: int
    sell_price: int
    sell_volume: int
    sell_count: int
    # id of the last change of this level
    ref_id: int | None = None


@dataclass(frozen=True, slots=True)
class MarketWatchInstrument:
    ins_code: str
    isin: str | None
    # symbol and name use the Arabic ي and ك
    symbol: str | None
    name: str | None
    # time of the last change of the row
    time: datetime.time
    first_price: int
    closing_price: int
    last_price: int
    trade_count: int
    volume: int
    value: int
    low_price: int
    high_price: int
    yesterday_price: int
    eps: float
    base_volume: int
    # visits of the symbol page
    visit_count: int
    # 1 بازار بورس, 2 بازار فرابورس, 3 بازار مشتقه
    flow: int
    # padded with a space, e.g. "27 "
    sector_code: str
    # allowed price range of the day
    max_allowed_price: int
    min_allowed_price: int
    total_shares: int
    # 300 for a share
    instrument_type: int
    # the best 5 levels of the order book
    best_limits: list[MarketWatchBestLimit]
    pe: float | None = None
    best_buy_price: int | None = None
    best_sell_price: int | None = None
    last_price_change: int | None = None
    closing_price_change: int | None = None
    board_code: str | None = None
    market_code: str | None = None
    # redemption NAV of funds, 0 for others
    nav: int | None = None
    # options and futures only
    open_positions: int | None = None
    id: int | None = None
    date: datetime.date | None = None
    p_closing: int | None = None
    i_close: bool | None = None
    y_close: bool | None = None
    p_dr_cot_val: int | None = None
    z_tot_tran: int | None = None
    q_tot_tran5_j: int | None = None
    q_tot_cap: int | None = None


def parse_market_watch(data: Any) -> list[MarketWatchInstrument]:
    return [
        MarketWatchInstrument(
            ins_code=str(row["insCode"]),
            isin=row["insID"],
            symbol=row["lva"],
            name=row["lvc"],
            time=to_time(row["hEven"]),
            first_price=int(row["pf"]),
            closing_price=int(row["pcl"]),
            last_price=int(row["pdv"]),
            trade_count=int(row["ztt"]),
            volume=int(row["qtj"]),
            value=int(row["qtc"]),
            low_price=int(row["pmn"]),
            high_price=int(row["pmx"]),
            yesterday_price=int(row["py"]),
            eps=float(row["eps"]),
            base_volume=int(row["bv"]),
            visit_count=int(row["vc"]),
            flow=int(row["flow"]),
            sector_code=row["csv"],
            max_allowed_price=int(row["pMax"]),
            min_allowed_price=int(row["pMin"]),
            total_shares=int(row["ztd"]),
            instrument_type=int(row["yVal"]),
            best_limits=[
                MarketWatchBestLimit(
                    level=int(level["n"]),
                    buy_count=int(level["zmd"]),
                    buy_volume=int(level["qmd"]),
                    buy_price=int(level["pmd"]),
                    sell_price=int(level["pmo"]),
                    sell_volume=int(level["qmo"]),
                    sell_count=int(level["zmo"]),
                    ref_id=level.get("rid"),
                )
                for level in row["blDs"] or []
            ],
            pe=number_text_to_float(row.get("pe")),
            best_buy_price=to_optional_int(row.get("pmd")),
            best_sell_price=to_optional_int(row.get("pmo")),
            last_price_change=to_optional_int(row.get("pc")),
            closing_price_change=to_optional_int(row.get("pcpc")),
            board_code=row.get("cGrValCot"),
            market_code=row.get("yMarNSC"),
            nav=to_optional_int(row.get("pRedTran")),
            open_positions=to_optional_int(row.get("buyOP")),
            id=row.get("id"),
            date=to_optional_date(row.get("dEven")),
            p_closing=to_optional_int(row.get("pClosing")),
            i_close=to_optional_bool(row.get("iClose")),
            y_close=to_optional_bool(row.get("yClose")),
            p_dr_cot_val=to_optional_int(row.get("pDrCotVal")),
            z_tot_tran=to_optional_int(row.get("zTotTran")),
            q_tot_tran5_j=to_optional_int(row.get("qTotTran5J")),
            q_tot_cap=to_optional_int(row.get("qTotCap")),
        )
        for row in data["marketwatch"] or []
    ]


@dataclass(frozen=True, slots=True)
class InstrumentStatistic:
    ins_code: str
    stat_id: int
    value: int | float
    date: datetime.date | None = None


def parse_key_stats(data: Any) -> list[InstrumentStatistic]:
    stats = []
    for row in data["instValueAllInstAllParam"] or []:
        text = row["dataValue"]
        is_float = "." in text or "e" in text or "E" in text
        stats.append(
            InstrumentStatistic(
                ins_code=str(row["insCode"]),
                stat_id=int(row["dataType"]),
                value=float(text) if is_float else int(text),
                date=to_optional_date(row.get("dEven")),
            )
        )
    return stats
