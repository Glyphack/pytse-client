import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from pathlib import Path

import aiohttp
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from pytse_client import config
from pytse_client.symbols_data import (
    MarketSymbol,
    clean_name,
    clean_symbol,
    match_search_results,
    unique_ids,
)
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.closing_price import (
    parse_closing_price_daily_all_inst,
)
from pytse_client.tsetmc_api.instrument import (
    InstrumentInfo,
    InstrumentSearchResult,
    parse_instrument_info,
    parse_instrument_search,
)
from pytse_client.tsetmc_api.market import (
    MarketWatchInstrument,
    parse_market_watch,
)

logger = logging.getLogger(config.LOGGER_NAME)

DEFAULT_CONCURRENCY = 5
SYMBOLS_FILE_NAME = "symbols_name.json"
_PERSIAN_ALPHABET = "آاأإءبپتثجچحخدذرزژسشصضطظعغفقکگلمنوؤهةیئ"
_PERSIAN_ORDER = {char: i for i, char in enumerate(_PERSIAN_ALPHABET)}


def _alphabet_order(symbol: MarketSymbol) -> tuple:
    letters = tuple(
        (1, _PERSIAN_ORDER[char]) if char in _PERSIAN_ORDER else (0, ord(char))
        for char in symbol.symbol
        if char not in " \u200c"
    )
    return letters, symbol.symbol


def _market_symbol(
    row: MarketWatchInstrument | InstrumentInfo, index: str
) -> MarketSymbol | None:
    symbol = clean_symbol(row.symbol or "")
    # bonds, options and futures end with a number
    if not symbol or re.search(r"\d+$", symbol):
        return None
    return MarketSymbol(
        code=(row.isin or "").strip(),
        symbol=symbol,
        name=clean_name(row.name or ""),
        index=index,
        old=[],
    )


def _is_retryable(ex: BaseException) -> bool:
    if isinstance(ex, aiohttp.ClientResponseError):
        return ex.status == 429 or ex.status >= 500
    return isinstance(
        ex, (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError)
    )


_retry_request = retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, max=30) + wait_random(0, 1),
    reraise=True,
)


@dataclass
class AsyncApi:
    session: aiohttp.ClientSession
    semaphore: asyncio.Semaphore

    @classmethod
    @asynccontextmanager
    async def open(cls) -> AsyncGenerator["AsyncApi", None]:
        async with client.open_session(limit=DEFAULT_CONCURRENCY) as session:
            yield cls(session, asyncio.Semaphore(DEFAULT_CONCURRENCY))

    @_retry_request
    async def search(self, symbol_name: str) -> list[InstrumentSearchResult]:
        async with self.semaphore:
            data = await client.api.call_instrument_search_async(
                symbol_name, self.session
            )
        return parse_instrument_search(data)

    @_retry_request
    async def instrument_info(self, ins_code: str) -> InstrumentInfo:
        async with self.semaphore:
            data = await client.api.call_instrument_info_async(
                ins_code, self.session
            )
        return parse_instrument_info(data)


@dataclass
class SymbolResolver:
    api: AsyncApi
    # symbol to index of the market watch, kept even when the search does
    # not list it as active
    active_symbols: dict[str, str]
    # symbols of the current symbols_name.json
    previous: dict[str, MarketSymbol]

    def is_active(self, symbol: MarketSymbol) -> bool:
        return self.active_symbols.get(symbol.symbol) == symbol.index

    def previous_ids(self, symbol_name: str) -> list[str]:
        previous_symbol = self.previous.get(symbol_name)
        if previous_symbol is None:
            return []
        return previous_symbol.old + [previous_symbol.index]

    async def resolve(self, symbol: MarketSymbol) -> MarketSymbol | None:
        try:
            return await self._resolve(symbol)
        except Exception as ex:
            logger.warning("cannot look %s up: %r", symbol.symbol, ex)
        if not self.is_active(symbol):
            return self.previous.get(symbol.symbol)
        if symbol.symbol not in self.previous:
            return symbol
        old = unique_ids(symbol.old + self.previous_ids(symbol.symbol))
        return replace(symbol, old=[i for i in old if i != symbol.index])

    async def _resolve(self, symbol: MarketSymbol) -> MarketSymbol | None:
        results = await self.api.search(symbol.symbol)
        active, old_ids = match_search_results(
            results, symbol.symbol, preferred_index=symbol.index
        )
        old = unique_ids(old_ids + self.previous_ids(symbol.symbol))
        if self.is_active(symbol):
            index = symbol.index
            name = symbol.name
            if active is None or active.ins_code != index:
                logger.info(
                    "search does not list %s (%s) as active, the market "
                    "watch does",
                    symbol.symbol,
                    index,
                )
        elif active is not None:
            index = active.ins_code
            name = clean_name(active.name or "") or symbol.name
        else:
            logger.debug("%s is deleted", symbol.symbol)
            previous_symbol = self.previous.get(symbol.symbol)
            if previous_symbol is None:
                return None
            # Ticker treats a symbol whose index is in its old list as
            # deleted.
            return replace(previous_symbol, old=old)

        code = symbol.code if index == symbol.index else ""
        if not code:
            try:
                info = await self.api.instrument_info(index)
                code = (info.isin or "").strip()
            except Exception as ex:
                logger.warning(
                    "cannot read the ISIN of %s (%s): %r",
                    symbol.symbol,
                    index,
                    ex,
                )
        return MarketSymbol(
            code=code,
            symbol=symbol.symbol,
            name=name,
            index=index,
            old=[i for i in old if i != index],
        )


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    json_path = Path(config.pytse_dir) / "data" / SYMBOLS_FILE_NAME

    previous: list[MarketSymbol] = []
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf8"))
        previous = [
            MarketSymbol(
                code=value.get("code") or "",
                symbol=symbol,
                name=value.get("name") or "",
                index=str(value.get("index") or ""),
                old=[str(old) for old in value.get("old") or []],
            )
            for symbol, value in data.items()
        ]
    print(f"symbols in the current {SYMBOLS_FILE_NAME}: {len(previous)}")

    market_watch_rows = parse_market_watch(client.api.call_market_watch())
    market_watch_codes = {row.ins_code for row in market_watch_rows}
    market_watch_symbols = [
        symbol
        for symbol in (
            _market_symbol(row, row.ins_code) for row in market_watch_rows
        )
        if symbol is not None
    ]
    print(
        f"market watch: {len(market_watch_rows)} instruments, "
        f"{len(market_watch_symbols)} symbols"
    )

    # has suspended instruments the market watch does not show
    history_rows = parse_closing_price_daily_all_inst(
        client.api.call_closing_price_daily_all_inst()
    )
    history_codes = {row.ins_code for row in history_rows if row.ins_code}
    missing_codes = history_codes - market_watch_codes
    async with AsyncApi.open() as api:

        async def get_one(ins_code: str) -> MarketSymbol | None:
            try:
                info = await api.instrument_info(ins_code)
            except Exception as ex:
                logger.warning(
                    "cannot read instrument info of %s: %r", ins_code, ex
                )
                return None
            return _market_symbol(info, ins_code)

        history_results = await asyncio.gather(
            *(get_one(code) for code in sorted(missing_codes))
        )
    history_symbols = [
        symbol for symbol in history_results if symbol is not None
    ]
    print(
        f"closing price history: {len(history_codes)} instruments, "
        f"{len(missing_codes)} not in the market watch, "
        f"{len(history_symbols)} symbols"
    )

    # the first source of a symbol wins
    unique: dict[str, MarketSymbol] = {}
    for symbol in market_watch_symbols + history_symbols + previous:
        unique.setdefault(symbol.symbol, symbol)
    print(f"Total deduplicated symbols: {len(unique)}")

    done = 0
    async with AsyncApi.open() as api:
        resolver = SymbolResolver(
            api,
            active_symbols={s.symbol: s.index for s in market_watch_symbols},
            previous={symbol.symbol: symbol for symbol in previous},
        )

        async def resolve(symbol: MarketSymbol) -> MarketSymbol | None:
            nonlocal done
            result = await resolver.resolve(symbol)
            done += 1
            if done % 200 == 0:
                logger.info("looked up %d/%d symbols", done, len(unique))
            return result

        results = await asyncio.gather(*(resolve(s) for s in unique.values()))
    resolved = [symbol for symbol in results if symbol is not None]

    # a renamed instrument keeps its index under its new symbol
    active = {
        symbol.index: symbol.symbol
        for symbol in resolved
        if symbol.index not in symbol.old
    }
    market_symbols: list[MarketSymbol] = []
    for symbol in resolved:
        old = [
            index
            for index in symbol.old
            if active.get(index, symbol.symbol) == symbol.symbol
        ]
        if old != symbol.old:
            logger.info(
                "%s: removed old indexes active under another symbol: %s",
                symbol.symbol,
                [index for index in symbol.old if index not in old],
            )
            symbol = replace(symbol, old=old)
        market_symbols.append(symbol)
    print(f"finished fetching old indexes, symbols: {len(market_symbols)}")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        symbol.symbol: symbol.json_value()
        for symbol in sorted(market_symbols, key=_alphabet_order)
    }
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8"
    )


if __name__ == "__main__":
    asyncio.run(main())
