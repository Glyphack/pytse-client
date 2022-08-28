import shutil
import unittest
from os.path import exists
from pathlib import Path

from pytse_client import symbols_data
from pytse_client.scraper.symbol_scraper import (
    get_market_symbols_from_symbols_list_page,
)
from pytse_client.scripts.update_symbols_json import write_symbols_to_json


class TestDownloadSymbolHistory(unittest.TestCase):
    def setUp(self) -> None:
        self.write_path = "test_symbol_data_dir"
        return super().setUp()

    def tearDown(self) -> None:
        if exists(self.write_path):
            shutil.rmtree(self.write_path)
        return super().tearDown()

    def test_update_symbols_json_file(self):
        write_symbols_to_json(
            get_market_symbols_from_symbols_list_page(),
            "symbols_name.json",
            self.write_path,
        )
        self.assertTrue(exists(Path(f"{self.write_path}/symbols_name.json")))

    def test_get_ticker_index(self) -> None:
        symbol = "وبملت"
        expected_index = "778253364357513"
        self.assertEqual(symbols_data.get_ticker_index(symbol), expected_index)
