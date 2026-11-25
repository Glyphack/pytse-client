import datetime
from dataclasses import dataclass
from typing import Any

from pytse_client.tsetmc_api._convert import to_date, to_optional_int


@dataclass(frozen=True, slots=True)
class ClientType:
    individual_buy_volume: int
    # the counts are numbers of buyers or sellers, not of trades
    individual_buy_count: int
    individual_sell_volume: int
    individual_sell_count: int
    corporate_buy_volume: int
    corporate_buy_count: int
    corporate_sell_volume: int
    corporate_sell_count: int
    # set only in the rows of GetClientTypeAll
    ins_code: str | None = None
    ddd_buy_volume: int | None = None
    ddd_buy_count: int | None = None


def _parse_client_type(row: Any, ins_code: str | None) -> ClientType:
    return ClientType(
        individual_buy_volume=int(row["buy_I_Volume"]),
        individual_buy_count=int(row["buy_CountI"]),
        individual_sell_volume=int(row["sell_I_Volume"]),
        individual_sell_count=int(row["sell_CountI"]),
        corporate_buy_volume=int(row["buy_N_Volume"]),
        corporate_buy_count=int(row["buy_CountN"]),
        corporate_sell_volume=int(row["sell_N_Volume"]),
        corporate_sell_count=int(row["sell_CountN"]),
        ins_code=ins_code,
        ddd_buy_volume=to_optional_int(row.get("buy_DDD_Volume")),
        ddd_buy_count=to_optional_int(row.get("buy_CountDDD")),
    )


def parse_client_type(data: Any) -> ClientType | None:
    client_type = data["clientType"]
    if not client_type:
        return None
    return _parse_client_type(client_type, client_type.get("insCode"))


def parse_client_type_all(data: Any) -> list[ClientType]:
    return [
        _parse_client_type(row, str(row["insCode"]))
        for row in data["clientTypeAllDto"] or []
    ]


@dataclass
class TradeSummary:
    buy_vol: float
    buy_count: float
    sell_vol: float
    sell_count: float


def individual_trade_summary(
    client_type: ClientType | None,
) -> TradeSummary | None:
    if client_type is None:
        return None
    return TradeSummary(
        buy_vol=float(client_type.individual_buy_volume),
        buy_count=float(client_type.individual_buy_count),
        sell_vol=float(client_type.individual_sell_volume),
        sell_count=float(client_type.individual_sell_count),
    )


def corporate_trade_summary(
    client_type: ClientType | None,
) -> TradeSummary | None:
    if client_type is None:
        return None
    return TradeSummary(
        buy_vol=float(client_type.corporate_buy_volume),
        buy_count=float(client_type.corporate_buy_count),
        sell_vol=float(client_type.corporate_sell_volume),
        sell_count=float(client_type.corporate_sell_count),
    )


@dataclass(frozen=True, slots=True)
class ClientTypeHistory:
    date: datetime.date
    individual_buy_count: int
    corporate_buy_count: int
    individual_sell_count: int
    corporate_sell_count: int
    individual_buy_volume: int
    corporate_buy_volume: int
    individual_sell_volume: int
    corporate_sell_volume: int
    individual_buy_value: int
    corporate_buy_value: int
    individual_sell_value: int
    corporate_sell_value: int
    ins_code: str | None = None


def parse_client_type_history(data: Any) -> list[ClientTypeHistory]:
    return [
        ClientTypeHistory(
            date=to_date(row["recDate"]),
            individual_buy_count=int(row["buy_I_Count"]),
            corporate_buy_count=int(row["buy_N_Count"]),
            individual_sell_count=int(row["sell_I_Count"]),
            corporate_sell_count=int(row["sell_N_Count"]),
            individual_buy_volume=int(row["buy_I_Volume"]),
            corporate_buy_volume=int(row["buy_N_Volume"]),
            individual_sell_volume=int(row["sell_I_Volume"]),
            corporate_sell_volume=int(row["sell_N_Volume"]),
            individual_buy_value=int(row["buy_I_Value"]),
            corporate_buy_value=int(row["buy_N_Value"]),
            individual_sell_value=int(row["sell_I_Value"]),
            corporate_sell_value=int(row["sell_N_Value"]),
            ins_code=row.get("insCode"),
        )
        for row in data["clientType"] or []
    ]
