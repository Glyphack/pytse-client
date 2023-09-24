import unittest

from pytse_client import Ticker


class TestTicker(unittest.TestCase):
    def setUp(self) -> None:
        self.activate_symbol = "ذوب"
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_option_trading(self):
        ticker = Ticker("", "816070469779688")
        ticker.title
        ticker.fulltitle

    def test_real_time_info_will_not_fail_with_deactivated_symbol(self):
        ticker = Ticker("", index="3823243780502959")
        self.assertRaises(
            RuntimeError,
            ticker.get_ticker_real_time_info_response,
        )

    def test_get_total_shares_history_on_activate_symbol(self):
        import asyncio

        # This should run without error
        res = asyncio.run(
            Ticker(self.activate_symbol).get_total_shares_history_async()
        )


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestTicker("test_download_symbol_history"))
    return test_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
