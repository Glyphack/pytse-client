import shutil
import unittest
from os.path import exists
from pathlib import Path
from datetime import date
from parameterized import parameterized
from pytse_client import get_trade_details
from pytse_client.historical_intraday.trade_details import (
    valid_time_frames_mapping,
)


class TestTradeDetails(unittest.TestCase):
    params = [
        ("خودرو", (6374, 2)),
        ("وغدیر", (1915, 2)),
    ]
    single_ticker = "اهرم"
    valid_timeframes = [
        (timeframe,) for timeframe in valid_time_frames_mapping.keys()
    ]

    def setUp(self) -> None:
        self.write_csv_path = "test_dir"
        self.valid_start_date = date(2023, 2, 27)
        self.valid_end_date = date(2023, 2, 28)
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    @parameterized.expand(params)
    def test_diff_trade_details(self, symbol_name: str, shape: tuple):
        dict_df = get_trade_details(
            symbol_name=symbol_name,
            start_date=self.valid_start_date,
            end_date=self.valid_end_date,
            to_csv=True,
            base_path=self.write_csv_path,
        )
        self.assertTrue(exists(Path(f"{self.write_csv_path}")))
        self.assertGreater(len(dict_df), 0)
        self.assertEqual(dict_df[self.valid_start_date].shape, shape)

    @parameterized.expand(valid_timeframes)
    def test_timeframes_aggregate(self, timeframe: str):
        dict_df = get_trade_details(
            symbol_name=self.single_ticker,
            start_date=self.valid_start_date,
            end_date=self.valid_end_date,
            to_csv=True,
            base_path=self.write_csv_path,
            timeframe=timeframe,
            aggregate=True,
        )
        self.assertTrue(exists(Path(f"{self.write_csv_path}")))
        self.assertFalse(dict_df["aggregate"].empty)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderBook)
    unittest.TextTestRunner(verbosity=3).run(suite)
