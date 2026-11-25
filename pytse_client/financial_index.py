import functools

import pandas as pd

from pytse_client import config, symbols_data
from pytse_client.download import download_financial_indexes
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.index import (
    IndexIntraday,
    parse_index_companies,
    parse_index_intraday,
)
from pytse_client.utils import persian


class FinancialIndex:
    def __init__(
        self,
        symbol: str,
        index: str | None = None,
        base_path: str = config.FINANCIAL_INDEX_BASE_PATH,
        write_history: bool = False,
    ):
        # Names in indices_name.json use the Arabic letters (ي, ك)
        symbol = persian.replace_persian(symbol)
        determined_index = index or symbols_data.get_financial_index(symbol)
        if determined_index is None:
            raise ValueError(
                f"Financial index {symbol} not found. Give one of the names "
                "in pytse_client/data/indices_name.json, or the code of the "
                'index: FinancialIndex(symbol="", index="32097828799138957")'
            )
        self._index: str = determined_index
        self.symbol: str = symbol if index is None else self._index
        self._base_path = base_path
        self._write_history = write_history

    @property
    def last_update(self) -> str:
        """Time of the last published value as HH:MM."""
        return self._last_intraday_row.time.strftime("%H:%M")

    @property
    def last_value(self) -> float:
        return self._last_intraday_row.value

    @property
    def high(self) -> float:
        return self._last_intraday_row.high

    @property
    def low(self) -> float:
        return self._last_intraday_row.low

    @functools.cached_property
    def history(self):
        return download_financial_indexes(
            self.symbol,
            write_to_csv=self._write_history,
            include_jdate=True,
            base_path=self._base_path,
        )[self.symbol]

    @functools.cached_property
    def contributing_symbols(self) -> list[dict[str, str]]:
        """Companies of the index as dicts with "symbol" and "index"."""
        companies = parse_index_companies(
            client.api.call_index_companies(self._index)
        ).companies
        return [
            {
                "symbol": persian.replace_arabic(company.instrument.symbol),
                "index": company.ins_code,
            }
            for company in companies
        ]

    @property
    def intraday_price(self) -> pd.DataFrame:
        """Values of the last trading day.

        Columns: value, change_percentage, low, high, indexed by time.
        """
        df = pd.DataFrame(
            [
                [
                    row.time,
                    row.value,
                    row.change_percent,
                    row.low,
                    row.high,
                ]
                for row in self._intraday_rows
            ],
            columns=["time", "value", "change_percentage", "low", "high"],
        )
        df = df.astype(
            {
                "value": float,
                "change_percentage": float,
                "low": float,
                "high": float,
            },
            errors="raise",
        )
        return df.set_index("time")

    @property
    def _intraday_rows(self) -> list[IndexIntraday]:
        rows = parse_index_intraday(
            client.api.call_index_intraday(self._index)
        )
        return sorted(rows, key=lambda row: row.time)

    @property
    def _last_intraday_row(self) -> IndexIntraday:
        rows = self._intraday_rows
        if not rows:
            raise RuntimeError(
                f"no intraday data for financial index {self.symbol}"
            )
        return rows[-1]
