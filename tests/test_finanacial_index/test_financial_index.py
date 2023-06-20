import shutil
import unittest
from os.path import exists
from pathlib import Path

from pytse_client import FinancialIndex


class TestFinancialIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_f_index = "شاخص قيمت 50 شركت"
        self.write_csv_path = "test_financial_index_dir"
        return super().setUp()

    def tearDown(self) -> None:
        if exists(self.write_csv_path):
            shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    def test_download_history(self):
        f_index_record = FinancialIndex(
            self.valid_f_index,
            base_path=self.write_csv_path,
            write_history=True,
        ).history
        self.assertTrue(
            exists(Path(f"{self.write_csv_path}/{self.valid_f_index}.csv"))
        )
        self.assertFalse(f_index_record.empty)
        expected_columns = [
            "jdate",
            "date",
            "close",
            "high",
            "low",
            "open",
            "volume",
        ]
        missing_columns = [
            col
            for col in expected_columns
            if col not in f_index_record.columns
        ]
        self.assertEqual(
            len(missing_columns), 0, f"Missing columns: {missing_columns}"
        )

    def test_fields(self):
        f_index_record = FinancialIndex(
            self.valid_f_index,
        )
        self.assertTrue(
            f_index_record.low
            and f_index_record.high
            and f_index_record.last_update
            and f_index_record.last_value
            and f_index_record.contributing_symbols
            and len(f_index_record.intraday_price)
        )


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFinancialIndex)
    unittest.TextTestRunner(verbosity=3).run(suite)
