import shutil
import unittest
from os.path import exists
from pathlib import Path
from datetime import date
from parameterized import parameterized
from pytse_client import get_trade_details


class TestTradeDetails(unittest.TestCase):
    params = [
        ("خودرو", (6374, 2)),
        ("وغدیر", (1915, 2)),
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


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderBook)
    unittest.TextTestRunner(verbosity=3).run(suite)
