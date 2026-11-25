"""Tests of pytse_client.asks_bids: get_asks_and_bids on the saved market
watch of six instruments."""

from pathlib import Path

import pandas as pd

import pytse_client as tse

DIRAN = "69090868458637360"

COLUMNS = [
    "id",
    "row_number",
    "num_of_sellers",
    "number_of_buyers",
    "buy_price",
    "sell_price",
    "buy_volume",
    "sell_volume",
    "symbol",
]


def test_asks_and_bids_have_five_levels_per_instrument(fake_api):
    orders = tse.get_asks_and_bids()
    assert fake_api.calls == [("market_watch",)]
    assert list(orders.columns) == COLUMNS
    assert len(orders) == 30
    # symbols come from the symbols of the package, with the Persian ی
    # and ک; in the order of the market watch
    assert orders["symbol"].tolist() == [
        symbol
        for symbol in ("شستا", "زاگرس", "فولاد", "خودرو", "کاریس", "دیران")
        for _ in range(5)
    ]
    assert orders["row_number"].tolist() == [1, 2, 3, 4, 5] * 6
    assert orders.iloc[0].to_dict() == {
        "id": "2400322364771558",
        "row_number": 1,
        "num_of_sellers": 2,
        "number_of_buyers": 18,
        "buy_price": 3480.0,
        "sell_price": 3510.0,
        "buy_volume": 368215,
        "sell_volume": 10000,
        "symbol": "شستا",
    }
    # nothing is written unless asked
    assert list(Path.cwd().iterdir()) == []


def test_asks_and_bids_of_an_instrument():
    orders = tse.get_asks_and_bids()
    diran = orders[orders["symbol"] == "دیران"]
    assert diran.to_dict("list") == {
        "id": [DIRAN] * 5,
        "row_number": [1, 2, 3, 4, 5],
        "num_of_sellers": [1, 4, 0, 0, 0],
        "number_of_buyers": [419, 2, 8, 1, 2],
        "buy_price": [24020.0, 23860.0, 23330.0, 23000.0, 22660.0],
        # the levels without a seller have the price 0
        "sell_price": [24070.0, 24790.0, 0.0, 0.0, 0.0],
        "buy_volume": [31322288, 13430, 158553, 1334, 451],
        "sell_volume": [294, 6284, 0, 0, 0],
        "symbol": ["دیران"] * 5,
    }


def test_types_of_the_asks_and_bids_columns():
    orders = tse.get_asks_and_bids()
    counts_and_volumes = [
        "row_number",
        "num_of_sellers",
        "number_of_buyers",
        "buy_volume",
        "sell_volume",
    ]
    assert (orders.dtypes[counts_and_volumes] == "int64").all()
    assert (orders.dtypes[["buy_price", "sell_price"]] == "float64").all()
    assert all(isinstance(code, str) for code in orders["id"])


def test_instruments_the_package_does_not_know_are_left_out(fake_api, sample):
    market_watch = sample("market_watch")
    unknown = dict(market_watch["marketwatch"][0], insCode="1", lva="ناموجود")
    market_watch["marketwatch"].append(unknown)
    fake_api.responses["market_watch"] = market_watch
    orders = tse.get_asks_and_bids()
    assert len(orders) == 30
    assert "1" not in set(orders["id"])


def test_asks_and_bids_are_written_to_a_csv_file(tmp_path):
    orders = tse.get_asks_and_bids(to_csv=True)
    saved = pd.read_csv("asks_bids_data/bids_asks.csv", dtype={"id": str})
    pd.testing.assert_frame_equal(
        saved, orders.reset_index(drop=True), check_dtype=False
    )

    folder = tmp_path / "some" / "orders"
    tse.get_asks_and_bids(to_csv=True, base_path=str(folder))
    assert [path.name for path in folder.iterdir()] == ["bids_asks.csv"]


def test_empty_market_watch_gives_no_orders(fake_api):
    fake_api.responses["market_watch"] = {"marketwatch": []}
    orders = tse.get_asks_and_bids()
    assert list(orders.columns) == COLUMNS
    assert orders.empty
