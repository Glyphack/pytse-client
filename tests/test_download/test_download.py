import shutil
import unittest
from os.path import exists
from pathlib import Path

from pytse_client import download, download_client_types_records


class TestDownloadSymbolHistory(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_symbols = ["وبملت", "ذوب"]
        self.valid_symbol = "فولاد"
        self.write_csv_path = "test_symbol_records_dir"
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    def test_download_a_single_symbol_history(self):
        symbol_record = download(
            symbols=self.valid_symbol,
            write_to_csv=True,
            base_path=self.write_csv_path
        )[self.valid_symbol]
        self.assertTrue(
            exists(Path(f"{self.write_csv_path}/{self.valid_symbol}.csv"))
        )
        self.assertFalse(symbol_record.empty)

    def test_download_multiple_symbols(self):
        symbols_records = download(
            symbols=self.valid_symbols,
            write_to_csv=True,
            base_path=self.write_csv_path
        )
        for symbol, symbol_record in symbols_records.items():
            self.assertTrue(
                exists(Path(f"{self.write_csv_path}/{symbol}.csv"))
            )
            self.assertFalse(symbol_record.empty)


class TestDownloadClientTypes(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_symbols = ["وبملت", "ذوب"]
        self.valid_symbol = "فولاد"
        self.write_csv_path = "test_client_type_data_dir"
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    def test_download_a_single_symbol_client_types_records(self):
        symbol_record = download_client_types_records(
            symbols=self.valid_symbol,
            write_to_csv=True,
            base_path=self.write_csv_path
        )[self.valid_symbol]
        self.assertTrue(
            exists(Path(f"{self.write_csv_path}/{self.valid_symbol}.csv"))
        )
        self.assertFalse(symbol_record.empty)

    def test_download_multiple_symbols_client_types_records(self):
        symbols_records = download_client_types_records(
            symbols=self.valid_symbols,
            write_to_csv=True,
            base_path=self.write_csv_path
        )
        for symbol, symbol_record in symbols_records.items():
            self.assertTrue(
                exists(Path(f"{self.write_csv_path}/{symbol}.csv"))
            )
            self.assertFalse(symbol_record.empty)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDownloadSymbolHistory("test_download_symbol_history"))
    suite.addTest(TestDownloadClientTypes("test_download_client_types"))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
