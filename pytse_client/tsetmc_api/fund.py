import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import (
    to_optional_date,
    to_optional_int,
    to_optional_time,
)


@dataclass(frozen=True, slots=True)
class Etf:
    redemption_nav: int | None
    # date and time: when the NAV was published
    date: datetime.date | None
    time: datetime.time | None
    subscription_nav: int | None = None
    ins_code: str | None = None
    i_close: int | None = None


def parse_etf(data: Any) -> Etf | None:
    etf = data.get("etf")
    if not etf:
        return None
    return Etf(
        redemption_nav=to_optional_int(etf["pRedTran"]),
        date=to_optional_date(etf["deven"]),
        time=to_optional_time(etf["hEven"]),
        subscription_nav=to_optional_int(etf.get("pSubTran")),
        ins_code=etf.get("insCode"),
        i_close=etf.get("iClose"),
    )
