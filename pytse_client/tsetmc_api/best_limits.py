import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import to_optional_date, to_time


@dataclass(frozen=True, slots=True)
class BestLimit:
    # 1 to 5, 1 is the best price
    level: int
    # number of orders
    buy_count: int
    buy_volume: int
    buy_price: int
    sell_price: int
    sell_volume: int
    sell_count: int
    title: str | None = None
    ins_code: str | None = None


def parse_best_limits(data: Any) -> list[BestLimit]:
    return [
        BestLimit(
            level=int(row["number"]),
            buy_count=int(row["zOrdMeDem"]),
            buy_volume=int(row["qTitMeDem"]),
            buy_price=int(row["pMeDem"]),
            sell_price=int(row["pMeOf"]),
            sell_volume=int(row["qTitMeOf"]),
            sell_count=int(row["zOrdMeOf"]),
            title=row.get("title"),
            ins_code=row.get("insCode"),
        )
        for row in data["bestLimits"] or []
    ]


@dataclass
class Order:
    count: int
    volume: int
    price: int


@dataclass(frozen=True, slots=True)
class BestLimitHistory:
    time: datetime.time
    # increases with time
    ref_id: int
    # 1 to 5, 1 is the best price
    level: int
    buy_count: int
    buy_volume: int
    buy_price: int
    sell_price: int
    sell_volume: int
    sell_count: int
    idn: int | None = None
    date: datetime.date | None = None
    title: str | None = None
    ins_code: str | None = None


def parse_best_limits_history(data: Any) -> list[BestLimitHistory]:
    return [
        BestLimitHistory(
            time=to_time(row["hEven"]),
            ref_id=int(row["refID"]),
            level=int(row["number"]),
            buy_count=int(row["zOrdMeDem"]),
            buy_volume=int(row["qTitMeDem"]),
            buy_price=int(row["pMeDem"]),
            sell_price=int(row["pMeOf"]),
            sell_volume=int(row["qTitMeOf"]),
            sell_count=int(row["zOrdMeOf"]),
            idn=row.get("idn"),
            date=to_optional_date(row.get("dEven")),
            title=row.get("title"),
            ins_code=row.get("insCode"),
        )
        for row in data["bestLimitsHistory"] or []
    ]
