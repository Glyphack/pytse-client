import unittest

from pytse_client import Ticker
from pytse_client.ticker.export import (
    export_ticker_history_as_csv,
    ticker_real_time_data_to_csv,
)


class TestTickerExport(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_export_ticker_realtime_data_to_csv(self):
        ticker = Ticker("وبملت")
        df = ticker_real_time_data_to_csv(ticker)
        self.assertTrue(df.empty is False)

    def test_export_ticker_history_to_csv(self):
        ticker = Ticker("وبملت")
        df = export_ticker_history_as_csv(ticker)
        df.to_csv("test.csv")
        self.assertTrue(df.empty is False)


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestTickerExport("test_ticker_export"))
    return test_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
