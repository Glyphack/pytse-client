import argparse
import asyncio
import datetime
import json
from pathlib import Path
from typing import Any

from pytse_client import symbols_data
from pytse_client.tsetmc_api import client
from pytse_client.utils import persian

SYMBOL = "دیران"
FUND = "کاریس"
INDEX = "شاخص کل"
MARKET_SYMBOLS = [SYMBOL, FUND, "فولاد", "خودرو", "شستا", "زاگرس"]
DAY = datetime.date(2026, 11, 22)
# the days kept from a history, the way the api writes a date
FIRST_DAY = 20260901
LAST_DAY = 20261123
DATA_DIR = Path(__file__).parent / "data"


def save(name: str, answer: Any) -> None:
    text = json.dumps(answer, ensure_ascii=False, indent=1) + "\n"
    (DATA_DIR / f"{name}.json").write_text(text, encoding="utf8")
    print(f"saved {name}")


def kept_days(answer: dict, rows_key: str, date_key: str) -> dict:
    rows = [
        row
        for row in answer[rows_key]
        if FIRST_DAY <= row[date_key] <= LAST_DAY
    ]
    return {**answer, rows_key: rows}


def market_symbols(answer: dict) -> dict:
    symbols = symbols_data.symbols_information()
    codes = {symbols[symbol]["index"] for symbol in MARKET_SYMBOLS}
    return {
        key: [row for row in rows if str(row["insCode"]) in codes]
        for key, rows in answer.items()
    }


async def main(volatile: bool) -> None:
    api = client.api
    stock = symbols_data.symbols_information()[SYMBOL]["index"]
    fund = symbols_data.symbols_information()[FUND]["index"]
    index = symbols_data.financial_indexes_information()[
        persian.replace_persian(INDEX)
    ]["index"]

    async with client.open_session(limit=3) as session:
        save(
            "trade_history",
            await api.call_trade_history_async(stock, DAY, session),
        )
        save(
            "day_shareholders",
            await api.call_day_shareholders_async(stock, DAY, session),
        )
        save(
            "instrument_history",
            await api.call_instrument_history_async(stock, DAY, session),
        )
    best_limits = api.call_best_limits_history(stock, DAY)
    # the whole day is too long, the rows before 09:05:00 are enough
    best_limits["bestLimitsHistory"] = [
        row for row in best_limits["bestLimitsHistory"] if row["hEven"] < 90500
    ]
    save("best_limits_history", best_limits)
    save(
        "closing_price_daily_list",
        kept_days(
            api.call_closing_price_daily_list(stock),
            "closingPriceDaily",
            "dEven",
        ),
    )
    save(
        "client_type_history",
        kept_days(
            api.call_client_type_history(stock), "clientType", "recDate"
        ),
    )
    save(
        "index_history",
        kept_days(api.call_index_history(index), "indexB2", "dEven"),
    )
    save("instrument_search", api.call_instrument_search(SYMBOL))
    codal = api.call_codal_publisher(persian.replace_persian(SYMBOL))
    # no names, phone numbers or email of real people in the saved file
    codal["codalPublisher"].update(
        executiveManager="نام مدیر عامل",
        financialManager="نام مدیر مالی",
        telNo="02100000000",
        faxNo="02100000000",
        email="info@example.com",
    )
    save("codal_publisher", codal)

    if not volatile:
        return
    print("the next answers change every day, their files get new numbers")
    save("market_overview", api.call_market_overview())
    save("closing_price_info", api.call_closing_price_info(stock))
    save(
        "recent_closing_price_daily_list",
        api.call_recent_closing_price_daily_list(stock),
    )
    save("best_limits", api.call_best_limits(stock))
    save("client_type", api.call_client_type(stock))
    save("trades", api.call_trades(stock))
    save("shareholders", api.call_shareholders(stock))
    save("instrument_info", api.call_instrument_info(stock))
    save("etf", api.call_etf(fund))
    save("index_intraday", api.call_index_intraday(index))
    save("indices", api.call_indices(1))
    save("index_companies", market_symbols(api.call_index_companies(index)))
    save("market_watch", market_symbols(api.call_market_watch()))
    save("client_type_all", market_symbols(api.call_client_type_all()))
    save("key_stats", market_symbols(api.call_key_stats()))
    all_days = market_symbols(api.call_closing_price_daily_all_inst())
    rows = all_days["closingPriceDailyAllInst"]
    newest_days = sorted({row["dEven"] for row in rows})[-5:]
    # the newest five days of each symbol are enough
    all_days["closingPriceDailyAllInst"] = [
        row for row in rows if row["dEven"] in newest_days
    ]
    save("closing_price_daily_all_inst", all_days)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Save the answers of the TSETMC api that the tests read "
        "from tests/data."
    )
    parser.add_argument(
        "--volatile",
        action="store_true",
        help="also save the answers that have no date. They change every "
        "day, so this writes new numbers into their files and the tests "
        "that check those numbers need to be updated.",
    )
    asyncio.run(main(parser.parse_args().volatile))
