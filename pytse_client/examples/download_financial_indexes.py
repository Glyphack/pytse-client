"""
This example is about downloading all financial indexes csv data.
"""

from pytse_client.download import download_financial_indexes

download_financial_indexes(symbols="all", write_to_csv=True, base_path="hello")
