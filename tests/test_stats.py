"""Tests of pytse_client.stats: get_stats on the saved key statistics,
client types and market watch of six instruments."""

import math
from pathlib import Path

import pandas as pd
import pytest
import requests

import pytse_client as tse

DIRAN = "69090868458637360"

# the columns after the 89 key statistics: the instrument code, the client
# types of the day and the market watch row
OTHER_COLUMNS = [
    "index",
    "numof_individual_buy",
    "numof_corporate_buy",
    "vol_individual_buy",
    "vol_corporate_buy",
    "numof_individual_sell",
    "numof_corporate_sell",
    "vol_individual_sell",
    "vol_corporate_sell",
    "code",
    "symbol",
    "name",
    "last_changed",
    "open_price",
    "adj_closing_price",
    "last_price",
    "number_of_trans",
    "volume_of_trans",
    "value_of_trans",
    "min_price",
    "max_price",
    "yesterday_price",
    "EPS",
    "base_volume",
    "visit_count",
    "flow",
    "group_number",
    "max_price_allowed",
    "min_price_allowed",
    "number_of_stocks",
    "yval",
]


def row_of(stats: pd.DataFrame, symbol: str) -> pd.Series:
    [position] = stats.index[stats["symbol"] == symbol]
    return stats.loc[position]


def test_stats_has_a_row_per_instrument_and_a_column_per_statistic(fake_api):
    stats = tse.get_stats()
    assert fake_api.calls == [
        ("key_stats",),
        ("client_type_all",),
        ("market_watch",),
    ]
    assert stats.shape == (6, 120)
    statistics = list(stats.columns[:89])
    assert statistics == sorted(statistics)
    assert statistics[0] == "ave_numof_buyer_last_12_month"
    assert statistics[-1] == "w_ave_price_last_day_normal"
    assert list(stats.columns[89:]) == OTHER_COLUMNS
    # symbols and names come from the symbols of the package, with the
    # Persian ی and ک
    assert stats[["index", "symbol", "name"]].to_dict("list") == {
        "index": [
            "2400322364771558",
            "13235547361447092",
            "46348559193224090",
            "65883838195688438",
            "69067576215760005",
            DIRAN,
        ],
        "symbol": ["شستا", "زاگرس", "فولاد", "خودرو", "کاریس", "دیران"],
        "name": [
            "سرمایه گذاری تامین اجتماعی",
            "پتروشیمی زاگرس",
            "فولاد مبارکه اصفهان",
            "ایران خودرو",
            "صندوق س.سپند کاریزما-س",
            "ایراندارو",
        ],
    }
    assert stats.index.tolist() == [0, 1, 2, 3, 4, 5]
    # nothing is written unless asked
    assert list(Path.cwd().iterdir()) == []


def test_key_statistics_of_an_instrument():
    diran = row_of(tse.get_stats(), "دیران")
    assert diran[
        [
            "ave_val_trans_last_3_month",
            "ave_val_trans_last_12_month",
            "rank_val_trans_last_3_month",
            "ave_vol_individual_buy_last_3_month",
            "w_ave_price_last_day_normal",
            "val_trans_last_day",
            "vol_trans_last_day",
            "numof_trans_last_day",
            "percent_neg_days_last_3_month",
            "val_company_last_day",
            "percent_open_days_last_3_month",
            "rank_numof_seller_last_12_month",
        ]
    ].to_dict() == {
        "ave_val_trans_last_3_month": 383392645316,
        "ave_val_trans_last_12_month": 138024605322,
        "rank_val_trans_last_3_month": 326,
        "ave_vol_individual_buy_last_3_month": 18055472.030769,
        "w_ave_price_last_day_normal": 24020.0,
        "val_trans_last_day": 20679754780.0,
        "vol_trans_last_day": 860939,
        "numof_trans_last_day": 99,
        "percent_neg_days_last_3_month": 34.0,
        "val_company_last_day": 42755600000000.0,
        "percent_open_days_last_3_month": 96.97,
        "rank_numof_seller_last_12_month": 433,
    }
    # the api did not send this statistic for دیران
    assert math.isnan(diran["percent_pos_days_last_3_month"])


def test_client_types_and_market_watch_of_an_instrument():
    diran = row_of(tse.get_stats(), "دیران")
    assert diran[OTHER_COLUMNS[1:9]].to_dict() == {
        "numof_individual_buy": 13,
        "numof_corporate_buy": 0,
        "vol_individual_buy": 860939.0,
        "vol_corporate_buy": 0.0,
        "numof_individual_sell": 75,
        "numof_corporate_sell": 1,
        "vol_individual_sell": 703139.0,
        "vol_corporate_sell": 157800.0,
    }
    assert diran[OTHER_COLUMNS[12:]].to_dict() == {
        # 12:29:52
        "last_changed": 122952,
        "open_price": 24020.0,
        "adj_closing_price": 24020.0,
        "last_price": 24020.0,
        "number_of_trans": 99.0,
        "volume_of_trans": 860939.0,
        "value_of_trans": 20679754780.0,
        "min_price": 24020.0,
        "max_price": 24020.0,
        "yesterday_price": 23330.0,
        "EPS": 3064.0,
        "base_volume": 1.0,
        "visit_count": 13299,
        "flow": 1,
        "group_number": 43,
        "max_price_allowed": 24020.0,
        "min_price_allowed": 22640,
        "number_of_stocks": 1780000000.0,
        "yval": 300,
    }
    shasta = row_of(tse.get_stats(), "شستا")
    assert shasta["last_price"] == 3490.0
    assert shasta["numof_individual_buy"] == 4618
    assert shasta["number_of_stocks"] == 1636013456000.0


def test_types_of_the_stats_columns():
    stats = tse.get_stats()
    whole_numbers = [
        "ave_val_trans_last_3_month",
        "rank_val_trans_last_3_month",
        "vol_trans_last_day",
        "numof_individual_buy",
        "numof_corporate_sell",
        "last_changed",
        "visit_count",
        "flow",
        "group_number",
        "min_price_allowed",
        "yval",
    ]
    fractions = [
        "ave_vol_individual_buy_last_3_month",
        "percent_open_days_last_3_month",
        "vol_individual_buy",
        "vol_corporate_sell",
        "open_price",
        "last_price",
        "number_of_trans",
        "EPS",
        "max_price_allowed",
        "number_of_stocks",
    ]
    assert (stats.dtypes[whole_numbers] == "int64").all()
    assert (stats.dtypes[fractions] == "float64").all()
    assert all(isinstance(code, str) for code in stats["index"])


def test_stats_are_written_to_a_csv_file(tmp_path, capsys):
    stats = tse.get_stats(to_csv=True)
    path = Path("stats_data/key_stats.csv")
    assert path.exists()
    # the path of the file is printed
    assert capsys.readouterr().out.strip() == str(path)
    saved = pd.read_csv(path, dtype={"index": str})
    assert list(saved.columns) == list(stats.columns)
    assert saved["symbol"].tolist() == stats["symbol"].tolist()
    assert saved["index"].tolist() == stats["index"].tolist()
    assert saved["last_price"].tolist() == stats["last_price"].tolist()

    folder = tmp_path / "some" / "stats"
    tse.get_stats(base_path=str(folder), to_csv=True)
    assert [path.name for path in folder.iterdir()] == ["key_stats.csv"]


def test_instruments_and_statistics_the_package_does_not_know_are_left_out(
    fake_api, sample
):
    key_stats = sample("key_stats")
    key_stats["instValueAllInstAllParam"] += [
        # an instrument that is not in the symbols of the package
        {"insCode": "1", "dataType": 1, "dEven": 20261123, "dataValue": "5"},
        # a statistic without a name in the package
        {
            "insCode": DIRAN,
            "dataType": 999,
            "dEven": 20261123,
            "dataValue": "5",
        },
    ]
    fake_api.responses["key_stats"] = key_stats
    stats = tse.get_stats()
    assert stats.shape == (6, 120)
    assert "1" not in set(stats["index"])


def test_instrument_without_client_types_and_market_watch_row(
    fake_api, sample
):
    # the market watch leaves out suspended instruments, and the client
    # types the ones that were not traded today
    market_watch = sample("market_watch")
    assert market_watch["marketwatch"].pop()["insCode"] == DIRAN
    client_types = sample("client_type_all")
    assert client_types["clientTypeAllDto"].pop()["insCode"] == DIRAN
    fake_api.responses["market_watch"] = market_watch
    fake_api.responses["client_type_all"] = client_types

    stats = tse.get_stats()
    assert stats.shape == (6, 120)
    diran = row_of(stats, "دیران")
    assert diran["index"] == DIRAN
    assert diran["name"] == "ایراندارو"
    assert diran["ave_val_trans_last_3_month"] == 383392645316
    for column in ("last_price", "flow", "numof_individual_buy"):
        assert math.isnan(diran[column]), column
    assert row_of(stats, "شستا")["last_price"] == 3490.0


def test_last_change_before_ten_is_a_five_digit_number(fake_api, sample):
    market_watch = sample("market_watch")
    for row in market_watch["marketwatch"]:
        row["hEven"] = 90017
    fake_api.responses["market_watch"] = market_watch
    assert row_of(tse.get_stats(), "دیران")["last_changed"] == 90017


def test_no_statistics_gives_an_empty_frame(fake_api):
    fake_api.responses["key_stats"] = {"instValueAllInstAllParam": []}
    assert tse.get_stats().empty


@pytest.mark.parametrize(
    "endpoint, message",
    [
        ("key_stats", "Failed to get key stats: no answer"),
        ("client_type_all", "Failed to get client types: no answer"),
        ("market_watch", "Failed to get market watch: no answer"),
    ],
)
def test_error_names_the_part_that_failed(fake_api, endpoint, message):
    fake_api.errors[endpoint] = requests.ConnectionError("no answer")
    with pytest.raises(Exception, match=message):
        tse.get_stats()
