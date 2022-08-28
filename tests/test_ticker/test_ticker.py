import unittest

from pytse_client import Ticker


class TestTicker(unittest.TestCase):
    def setUp(self) -> None:
        # This can break the test if symbol changes state
        self.deactivated_symbol = "رتکو"
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_real_time_info_will_not_fail_with_deactivated_symbol(self):
        self.assertRaises(
            RuntimeError,
            Ticker(self.deactivated_symbol).get_ticker_real_time_info_response,
        )


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestTicker("test_download_symbol_history"))
    return test_suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
