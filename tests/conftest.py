"""Shared setup of the tests.

Every test that is not marked e2e runs offline: the library gets a
FakeTsetmcApi that answers with the saved responses of tests/data, the
current folder is a temporary one and opening a network connection fails
the test.
"""

import asyncio
import datetime
import ipaddress
import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
import pytest

from pytse_client import config, symbols_data
from pytse_client.tsetmc_api import client
from pytse_client.tsetmc_api.client import TsetmcApi

DATA_DIR = Path(__file__).parent / "data"

# content of the symbols_name.json of the symbols_file fixture
FEW_SYMBOLS = {
    "فولاد": {
        "index": "46348559193224090",
        "code": "IRO1FOLD0001",
        "name": "فولاد مبارکه اصفهان",
        "old": [],
    }
}


def load_sample(endpoint: str) -> Any:
    """The saved response of an endpoint, data/<endpoint>.json, where
    endpoint is the name of its TsetmcApi method without call_."""
    path = DATA_DIR / f"{endpoint}.json"
    return json.loads(path.read_text(encoding="utf8"))


@dataclass
class FakeTsetmcApi:
    """TsetmcApi that answers with the saved responses of tests/data.

    call_<name> and call_<name>_async return the content of
    data/<name>.json, whatever their arguments are.

    responses: answers to give in place of the saved ones, by endpoint
    errors: exceptions to raise in place of an answer, by endpoint
    calls: the calls made so far in order, each one a tuple of the
        endpoint and the arguments of the call (without the session)
    """

    responses: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, Exception] = field(default_factory=dict)
    calls: list[tuple] = field(default_factory=list)

    def _answer(self, endpoint: str, *args: Any) -> Any:
        self.calls.append((endpoint, *args))
        if endpoint in self.errors:
            raise self.errors[endpoint]
        if endpoint in self.responses:
            return self.responses[endpoint]
        return load_sample(endpoint)

    def call_market_overview(self) -> Any:
        return self._answer("market_overview")

    def call_market_watch(self) -> Any:
        return self._answer("market_watch")

    def call_key_stats(self) -> Any:
        return self._answer("key_stats")

    def call_closing_price_info(self, ins_code: str) -> Any:
        return self._answer("closing_price_info", ins_code)

    def call_closing_price_daily_list(self, ins_code: str) -> Any:
        return self._answer("closing_price_daily_list", ins_code)

    def call_recent_closing_price_daily_list(self, ins_code: str) -> Any:
        return self._answer("recent_closing_price_daily_list", ins_code)

    def call_closing_price_daily_all_inst(self) -> Any:
        return self._answer("closing_price_daily_all_inst")

    def call_best_limits(self, ins_code: str) -> Any:
        return self._answer("best_limits", ins_code)

    def call_best_limits_history(
        self, ins_code: str, date: datetime.date
    ) -> Any:
        return self._answer("best_limits_history", ins_code, date)

    def call_client_type(self, ins_code: str) -> Any:
        return self._answer("client_type", ins_code)

    def call_client_type_all(self) -> Any:
        return self._answer("client_type_all")

    def call_client_type_history(self, ins_code: str) -> Any:
        return self._answer("client_type_history", ins_code)

    def call_trades(self, ins_code: str) -> Any:
        return self._answer("trades", ins_code)

    def call_shareholders(self, ins_code: str) -> Any:
        return self._answer("shareholders", ins_code)

    def call_instrument_info(self, ins_code: str) -> Any:
        return self._answer("instrument_info", ins_code)

    def call_instrument_search(self, text: str) -> Any:
        return self._answer("instrument_search", text)

    def call_index_history(self, ins_code: str) -> Any:
        return self._answer("index_history", ins_code)

    def call_index_intraday(self, ins_code: str) -> Any:
        return self._answer("index_intraday", ins_code)

    def call_indices(self, flow: int) -> Any:
        return self._answer("indices", flow)

    def call_index_companies(self, ins_code: str) -> Any:
        return self._answer("index_companies", ins_code)

    def call_etf(self, ins_code: str) -> Any:
        return self._answer("etf", ins_code)

    def call_codal_publisher(self, symbol: str) -> Any:
        return self._answer("codal_publisher", symbol)

    async def call_best_limits_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return self._answer("best_limits_history", ins_code, date)

    async def call_trade_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return self._answer("trade_history", ins_code, date)

    async def call_day_shareholders_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return self._answer("day_shareholders", ins_code, date)

    async def call_instrument_info_async(
        self, ins_code: str, session: aiohttp.ClientSession
    ) -> Any:
        return self._answer("instrument_info", ins_code)

    async def call_instrument_search_async(
        self, text: str, session: aiohttp.ClientSession
    ) -> Any:
        return self._answer("instrument_search", text)

    async def call_instrument_history_async(
        self,
        ins_code: str,
        date: datetime.date,
        session: aiohttp.ClientSession,
    ) -> Any:
        return self._answer("instrument_history", ins_code, date)


def _is_loopback(address: Any) -> bool:
    """True for an address of this machine, like ("127.0.0.1", 8000)."""
    if not isinstance(address, tuple) or not address:
        return False
    try:
        return ipaddress.ip_address(address[0]).is_loopback
    except ValueError:
        return False


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test when it looks a host up or connects to another
    machine. Sockets inside this machine, which asyncio and
    multiprocessing use, keep working."""
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    internet = (socket.AF_INET, socket.AF_INET6)

    def refuse(target: Any) -> None:
        pytest.fail(f"a test that must run offline tried to reach {target}")

    def guarded_connect(self: socket.socket, address: Any) -> None:
        if self.family in internet and not _is_loopback(address):
            refuse(address)
        connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: Any) -> int:
        if self.family in internet and not _is_loopback(address):
            refuse(address)
        return connect_ex(self, address)

    def guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> None:
        refuse(host)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeTsetmcApi:
    """Puts a FakeTsetmcApi in client.api, where the library reads its
    TsetmcApi from, and returns it. A test asks for it to change the
    answers or to see the calls."""
    fake = FakeTsetmcApi()
    # the annotation makes the type checker compare the fake with the
    # protocol
    api: TsetmcApi = fake
    monkeypatch.setattr(client, "api", api)
    return fake


@pytest.fixture
def sample():
    """load_sample, to read the saved response of an endpoint."""
    return load_sample


@pytest.fixture
def symbols_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    """Makes the library read and write a symbols_name.json in a temporary
    folder in place of the one of the package, and returns its path. The
    file has only the symbol فولاد."""
    package_dir = tmp_path_factory.mktemp("package")
    path = package_dir / "data" / "symbols_name.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(FEW_SYMBOLS, ensure_ascii=False, indent=2), encoding="utf8"
    )
    monkeypatch.setattr(config, "pytse_dir", str(package_dir))
    # the library reads the file again
    monkeypatch.setattr(symbols_data, "ticker_name_to_index_mapping", None)
    return path


@pytest.fixture
def no_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    """Makes the pauses between two tries of a request take no time."""

    async def sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", sleep)


@pytest.fixture(autouse=True)
def offline(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Runs every test that is not marked e2e with the fake api, in a
    temporary folder (the files the library writes land there) and with
    the network blocked."""
    if request.node.get_closest_marker("e2e") is not None:
        return
    request.getfixturevalue("fake_api")
    monkeypatch.chdir(tmp_path)
    _block_network(monkeypatch)
