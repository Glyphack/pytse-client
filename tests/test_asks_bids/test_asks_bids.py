import shutil
import unittest
from os.path import exists
from pathlib import Path

from pytse_client import get_asks_and_bids


class TestKeyStats(unittest.TestCase):
    def setUp(self) -> None:
        self.write_csv_path = "test_asks_bids_dir"
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.write_csv_path)
        return super().tearDown()

    def test_key_stats(self):
        df = get_asks_and_bids(base_path=self.write_csv_path, to_csv=True)
        self.assertTrue(exists(Path(f"{self.write_csv_path}/bids_asks.csv")))
        self.assertFalse(df.empty)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKeyStats)
    unittest.TextTestRunner(verbosity=3).run(suite)
