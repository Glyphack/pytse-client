"""
This example is about downloading two sample financial indexes.
"""

from pytse_client.download import download_financial_indexes

download_financial_indexes(
    symbols=["شاخص قيمت 50 شركت", "فني مهندسي"],
    write_to_csv=True,
    include_jdate=True,
)
