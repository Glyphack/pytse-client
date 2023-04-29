import shutil
import unittest
from os.path import exists
from pathlib import Path
from datetime import date
from parameterized import parameterized
from pytse_client import get_orderbook


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
        shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    @parameterized.expand(params)
    def test_orderbook_data_exists(self, symbol_name: str):
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
        self.assertTrue(len(dict_df) > 0)
        self.assertTrue(
            dict_df[self.valid_start_date.strftime("%Y-%m-%d")].empty
        )


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderBook)
    unittest.TextTestRunner(verbosity=3).run(suite)
