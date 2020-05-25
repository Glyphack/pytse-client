"""
This example is about downloading all tickers csv data.
"""

from pytse_client.download import download

download(symbols="all", write_to_csv=True, base_path="hey")
