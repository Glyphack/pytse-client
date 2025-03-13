import json
import re
import ast
from typing import Dict, List, Optional, Set, Union

from pytse_client import config, utils, tse_settings
from pytse_client.scraper.symbol_scraper import MarketSymbol
from pytse_client.stats import _get_market_watch, _get_dict_of_market_watch

ticker_name_to_index_mapping = None
financial_index_name_to_index_mapping = None


def financial_indexes_information() -> Dict[str, Dict]:
    global financial_index_name_to_index_mapping
    if financial_index_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/indices_name.json", "r", encoding="utf8"
        ) as symbols_name:
            financial_index_name_to_index_mapping = json.load(symbols_name)
    return financial_index_name_to_index_mapping


def symbols_information() -> Dict[str, Dict]:
    global ticker_name_to_index_mapping
    if ticker_name_to_index_mapping is None:
        with open(
            f"{config.pytse_dir}/data/symbols_name.json", "r", encoding="utf8"
        ) as symbols_name:
            ticker_name_to_index_mapping = json.load(symbols_name)
    return ticker_name_to_index_mapping


def get_financial_index(financial_index_name: str):
    return (
        financial_indexes_information()
        .get(financial_index_name, {})
        .get("index")
    )


def get_ticker_index(ticker_symbol: str) -> Optional[str]:
    return symbols_information().get(ticker_symbol, {}).get("index")


def get_ticker_old_index(ticker_symbol: str) -> List[str]:
    """
    Returns list of deactivated ticket indexes with this symbol.
    Deactivated symbols contain historical data but not real time.
    Args:
        ticker_symbol: symbol name in persian

    Returns: index of old(deactivated) tickers with this symbol


    """
    return symbols_information().get(ticker_symbol, {}).get("old", []).copy()


def all_symbols() -> Set:
    return set(symbols_information().keys())


def all_financial_index() -> Set:
    return set(financial_indexes_information().keys())


def append_symbol_to_file(
    market_symbol: MarketSymbol,
):
    global ticker_name_to_index_mapping
    new_symbol = {
        market_symbol.symbol: {
            "index": market_symbol.index,
            "code": market_symbol.code,
            "name": market_symbol.name,
            "old": market_symbol.old,
        }
    }
    if ticker_name_to_index_mapping is not None:
        ticker_name_to_index_mapping.update(new_symbol)
    with open(
        f"{config.pytse_dir}/data/symbols_name.json", "r+", encoding="utf8"
    ) as file:
        data = json.load(file)
        data.update(new_symbol)
        file.seek(0)
        json.dump(data, file, ensure_ascii=False, indent=2)


def all_groups() -> set:
    session = utils.requests_retry_session()
    try:
        response = session.get(tse_settings.GROUPS_URL)
    except Exception as e:
        raise Exception(f"Failed to get market watch: {e}")
    finally:
        session.close()
    data = response.text
    match = re.search(r'var Sectors=\[\[(.*?)\]\]', data, re.DOTALL)

    if match:
        sectors_data = match.group(1)
        # Safely parse the string into a list of lists using ast.literal_eval
        try:
            sectors_list = ast.literal_eval(f'[[{sectors_data}]]')
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Error parsing sectors data: {e}")
            sectors_list = []

        # Step 3: Convert the list of lists into a dictionary
        groups = {sector[0]: utils.persian.replace_arabic(
            sector[1]) for sector in sectors_list}
    return groups


def filter_symbols(
        types: Union[List, str] = [],
        groups: Union[List, str] = [],
        market=None,
) -> Set:
    """
    Filters symbols based on type, group, and market.

    Args:
        types (Union[List, str]): A list or string of types to filter by.
        Valid values are 'housingFacilities', 'saham', 'payeFarabourse',
        'haghTaghaddom', 'oraghMosharekat', 'ati', 'sandoogh',
        'ekhtiarForoush' or 'kala',
        groups (Union[List, str]): A list or string of groups names to-
        filter by.
        market (str, optional): The market to filter by. Valid values are
        'bourse' or 'farabourse'.

    Returns:
        Set: A set of symbols that match the filter criteria.

    """
    if isinstance(types, str):
        types = [types]
    if isinstance(groups, str):
        groups = [groups]
    if len(groups) > 0:
        groups_list = all_groups()
        groups_numbers = [key for key,
                          value in groups_list.items() if value in groups]
    if market not in ["bourse", "farabourse", None]:
        raise ValueError(
            "Invalid market: valid values are 'bourse' and 'farabourse'."
        )
    valid_types = [
        "housingFacilities",
        "saham",
        "payeFarabourse",
        "haghTaghaddom",
        "oraghMosharekat",
        "ati",
        "sandoogh",
        "ekhtiarForoush",
        "kala",
    ]
    valid_types_lower = [x.lower() for x in valid_types]
    invalid_types = list(filter(lambda item: item.lower().replace(
        " ", "") not in valid_types_lower, types))
    if invalid_types:
        raise ValueError(
            f"These types are not valid: {invalid_types}\n" +
            "Valid types: {valid_types}")
    types_lower = [x.lower().replace(" ", "") for x in types]
    selected_symbols = []

    session = utils.requests_retry_session()
    raw_market_watch = _get_market_watch(session).text
    market_watch_dict = _get_dict_of_market_watch(raw_market_watch)
    for key in market_watch_dict:
        flow = market_watch_dict[key]["flow"]
        yval = market_watch_dict[key]["yval"]
        symbol = market_watch_dict[key]["symbol"]
        group_number = market_watch_dict[key]["group_number"]

        if (market == "bourse" and (flow != "1" and flow != "3")):
            continue
        if (market == "farabourse" and (
                flow == "1" or (
                    flow == "3" and yval not in ["320", "321", "602", "603"])
        )):
            continue

        if (len(groups) > 0 and group_number not in groups_numbers):
            continue

        if (len(types_lower) > 0):
            if ("housingfacilities" not in types_lower
                    and (
                        symbol.startswith("تسه") is True
                        or symbol.startswith("تملي") is True
                    )):
                continue
            if ("saham" not in types_lower and yval in ["300", "303", "313"]
                    and symbol.startswith("تسه") is False):
                continue
            if ("payefarabourse" not in types_lower and yval == "309"):
                continue
            if 'haghtaghaddom' not in types_lower and yval in [
                '400', '403', '404'
            ]:
                continue
            if 'oraghmosharekat' not in types_lower and yval in [
                '306', '301', '706', '208', '206', '200', '801', '802', '803',
                '804', '805', '901', '902',
            ]:
                continue
            if 'ati' not in types_lower and yval in ['263', '304']:
                continue
            if 'sandoogh' not in types_lower and yval in ['305', '380']:
                continue
            if 'ekhtiarforoush' not in types_lower and yval in [
                '600', '602', '605', '603', '311', '312', '320', '321',
            ]:
                continue
            if ("kala" not in types_lower and yval in ["308", "701"]):
                continue
        selected_symbols.append(utils.persian.replace_arabic(symbol))
    return set(selected_symbols)
