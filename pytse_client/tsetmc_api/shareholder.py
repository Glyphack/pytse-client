import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import to_optional_date


@dataclass(frozen=True, slots=True)
class Shareholder:
    share_id: int
    name: str
    company_isin: str
    # None in the latest list. The list of a past day also holds the list
    # of the next trading day.
    date: datetime.date | None
    shares: int
    percentage: float
    # 2 more shares, 3 fewer shares, 1 no change
    change: int
    change_amount: int
    shareholder_id: int | None = None


def _parse_shareholders(rows: Any) -> list[Shareholder]:
    return [
        Shareholder(
            share_id=int(row["shareHolderShareID"]),
            name=row["shareHolderName"],
            company_isin=row["cIsin"],
            date=to_optional_date(row["dEven"]),
            shares=int(row["numberOfShares"]),
            percentage=float(row["perOfShares"]),
            change=int(row["change"]),
            change_amount=int(row["changeAmount"]),
            shareholder_id=row.get("shareHolderID"),
        )
        for row in rows or []
    ]


def parse_shareholders(data: Any) -> list[Shareholder]:
    return _parse_shareholders(data["shareHolder"])


def parse_day_shareholders(data: Any) -> list[Shareholder]:
    return _parse_shareholders(data["shareShareholder"])
