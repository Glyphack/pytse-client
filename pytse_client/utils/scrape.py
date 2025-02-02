# from .requests import requests_retry_session
from typing import List, Tuple

import re
import bs4
import pandas as pd

from .string import convert_to_number_if_number


def get_html_table_header_and_rows_and_ids(
    table: bs4.PageElement,
) -> Tuple[List, List]:
    """
    return header and rows from a html table as a list
    """
    header = ["id"]
    rows = []
    ids = []
    table_header = table.find("tr")
    table_rows = table.find_all("tr")[1:]
    for items in table_header:
        header.append(items.get_text())

    for table_row in table_rows:
        row = []
        ids.append(re.search(r'\d+', table_row["onclick"]).group())
        for cell in table_row.findAll(["th", "td"]):
            row.append(cell)
        rows.append(row)

    return header, rows, ids


def get_shareholders_html_table_as_csv(table) -> pd.DataFrame:
    """
    given table element from shareholders page returns DatFrame
    Containing the table
    """
    header, rows, ids = get_html_table_header_and_rows_and_ids(table)
    df_rows = []

    i = 0
    for row in rows:
        df_row = [ids[i]]
        i = i + 1
        for cell in row:
            cell_div = cell.find("div")
            if cell_div and cell_div.get_text() != "":
                df_row.append(convert_to_number_if_number(cell_div["title"]))
            else:
                df_row.append(
                    convert_to_number_if_number(cell.get_text().strip())
                )
        df_rows.append(df_row)
    return pd.DataFrame(data=df_rows, columns=header)
