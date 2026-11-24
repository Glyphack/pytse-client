import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import (
    to_optional_date,
    to_optional_int,
    to_time,
)


@dataclass(frozen=True, slots=True)
class Trade:
    # number of the trade in the day; the API can send a trade twice
    number: int
    time: datetime.time
    volume: int
    price: int
    canceled: bool
    ins_code: str | None = None
    date: datetime.date | None = None
    q_tit_ng_j: int | None = None
    i_sens_var_p: str | None = None
    p_ph_sea_cot_j: int | None = None
    p_pb_sea_cot_j: int | None = None
    i_anu_tran: int | None = None
    xq_var_pj_dr_p_rf: float | None = None


def _parse_trades(rows: Any) -> list[Trade]:
    return [
        Trade(
            number=int(row["nTran"]),
            time=to_time(row["hEven"]),
            volume=int(row["qTitTran"]),
            price=int(row["pTran"]),
            canceled=bool(row["canceled"]),
            ins_code=row.get("insCode"),
            date=to_optional_date(row.get("dEven")),
            q_tit_ng_j=to_optional_int(row.get("qTitNgJ")),
            i_sens_var_p=row.get("iSensVarP"),
            p_ph_sea_cot_j=to_optional_int(row.get("pPhSeaCotJ")),
            p_pb_sea_cot_j=to_optional_int(row.get("pPbSeaCotJ")),
            i_anu_tran=to_optional_int(row.get("iAnuTran")),
            xq_var_pj_dr_p_rf=row.get("xqVarPJDrPRf"),
        )
        for row in rows or []
    ]


def parse_trades(data: Any) -> list[Trade]:
    return _parse_trades(data["trade"])


def parse_trade_history(data: Any) -> list[Trade]:
    return _parse_trades(data["tradeHistory"])


def unique_trades(trades: list[Trade]) -> list[Trade]:
    by_number = {}
    for trade in trades:
        if not trade.canceled:
            by_number[trade.number] = trade
    return list(by_number.values())
