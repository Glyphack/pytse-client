import shutil
import unittest
import datetime
from os.path import exists
from pathlib import Path
from datetime import date
from parameterized import parameterized
from pytse_client import get_orderbook
from pytse_client.orderbook.common import get_valid_dates
from pytse_client.ticker import Ticker


class TestOrderBook(unittest.TestCase):
    params = [
        ("خودرو",),
        ("وغدیر",),
    ]

    def setUp(self) -> None:
        self.write_csv_path = "test_dir"
        self.valid_start_date = date(2023, 2, 27)
        self.valid_end_date = date(2023, 2, 28)
        self.invalid_start_date = date(2023, 3, 8)
        self.invalid_end_date = date(2023, 3, 23)
        return super().setUp()

    def tearDown(self) -> None:
        try:
            shutil.rmtree(self.write_csv_path)
        except FileNotFoundError:
            pass
        return super().tearDown()

    @parameterized.expand(params)
    def test_diff_orderbook_async_data_exists(self, symbol_name: str):
        dict_df = get_orderbook(
            symbol_name=symbol_name,
            start_date=self.valid_start_date,
            end_date=self.valid_end_date,
            to_csv=True,
            base_path=self.write_csv_path,
            ignore_date_validation=False,
            diff_orderbook=True,
        )
        self.assertTrue(exists(Path(f"{self.write_csv_path}")))
        self.assertGreater(len(dict_df), 0)
        self.assertFalse(
            dict_df[self.valid_start_date.strftime("%Y-%m-%d")].empty
        )

    @parameterized.expand(params)
    def test_processed_orderbook_async_data_exists(self, symbol_name: str):
        dict_df = get_orderbook(
            symbol_name=symbol_name,
            start_date=self.valid_start_date,
            end_date=self.valid_end_date,
            to_csv=True,
            base_path=self.write_csv_path,
            ignore_date_validation=False,
            diff_orderbook=False,
        )
        self.assertTrue(exists(Path(f"{self.write_csv_path}")))
        self.assertGreater(len(dict_df), 0)
        self.assertFalse(
            dict_df[self.valid_start_date.strftime("%Y-%m-%d")].empty
        )

    @parameterized.expand(params)
    def test_diff_orderbook_sync_data_exists(self, symbol_name: str):
        dict_df = get_orderbook(
            symbol_name=symbol_name,
            start_date=self.valid_start_date,
            end_date=self.valid_end_date,
            to_csv=True,
            base_path=self.write_csv_path,
            ignore_date_validation=False,
            diff_orderbook=True,
            async_requests=False,
        )
        self.assertTrue(exists(Path(f"{self.write_csv_path}")))
        self.assertGreater(len(dict_df), 0)
        self.assertFalse(
            dict_df[self.valid_start_date.strftime("%Y-%m-%d")].empty
        )

    @parameterized.expand(params)
    def test_diff_orderbook_invalid_date(self, symbol_name: str):
        with self.assertRaises(Exception):
            get_orderbook(
                symbol_name=symbol_name,
                start_date=self.invalid_start_date,
            )

    def test_long_processed(self):
        number_valid_dates = 29
        symbol = "زر"
        ticker = Ticker(symbol)
        start_date = datetime.date(2023, 3, 1)
        end_date = datetime.date(2023, 4, 20)
        dict_df = get_orderbook(
            symbol_name=symbol,
            start_date=start_date,
            end_date=end_date,
            ignore_date_validation=True,
            diff_orderbook=False,
        )
        ls = list(dict_df.values())
        self.assertEqual(len(ls), number_valid_dates)
        self.assertEqual(len(ls), len(get_valid_dates(ticker, start_date, end_date)))

    def test_length_processed(self):
        symbol = "زر"
        start_date = datetime.date(2023, 3, 1)

        dict_df = get_orderbook(symbol, start_date=start_date)
        self.assertEqual(list(dict_df.values())[0].shape, tuple([3524, 30]))

    def test_length_diff(self):
        symbol = "زر"
        start_date = datetime.date(2023, 3, 1)

        dict_df = get_orderbook(symbol, start_date=start_date, diff_orderbook=True)
        self.assertEqual(list(dict_df.values())[0].shape, tuple([9331, 7]))


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderBook)
    unittest.TextTestRunner(verbosity=3).run(suite)
