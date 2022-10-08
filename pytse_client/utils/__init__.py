from pytse_client.utils.date import datetime_range
from pytse_client.utils.request_session import requests_retry_session
from pytse_client.utils.scrape import (
    get_html_table_header_and_rows,
    get_shareholders_html_table_as_csv,
)
from pytse_client.utils.string import convert_to_number_if_number
from pytse_client.utils.symbols import map_index_to_symbols
