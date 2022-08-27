def get_index_to_symbol_map(dic: dict):
    """
    convert {<symbol>: {index:<index>,...}}
    to
    {<index>: {symbol:<symbol>,...}}
    """
    tmp_dic = {
        item[1]["index"]: {**item[1], "symbol": item[0]}
        for item in dic.items()
    }
    final_dic = {
        item[0]: {
            item2[0]: item2[1]
            for item2 in item[1].items()
            if item2[0] != "index"
        }
        for item in tmp_dic.items()
    }
    return final_dic


def get_keys_of_market_watch():
    """
    [
        '71957984642204570', # id
        'IRO7APTP0001', # code
        'شپترو', # symbol
        'پتروشيمي آبادان', # name
        '122931', # last changed
        '2470', # open price
        '2438', # adj_closing price
        '2436', # last price
        '861', # number of trans
        '29225934', # volume of trans
        '71250969784', # value of trans
        '2436', # min price
        '2500', # max price
        '2511', # yesterday price
        '-43', # EPS
        '4000000', # base voulume
        '3423', # ?
        '4', # ?
        '44', # group number
        '2586.00', # max allowed
        '2436.00', # min allowed
        '10000000000', # number of stocks
        '309' # ?
    ]
    """
    keys = [
        "index",
        "code",
        "symbol",
        "name",
        "last_changed",
        "open_price",
        "adj_closing_price",
        "last_price",
        "number_of_trans",
        "volume_of_trans",
        "value_of_trans",
        "min_price",
        "max_year",
        "yesterday_price",
        "EPS",
        "base_volume",
        "NOT_VALID_KEY",
        "NOT_VALID_KEY",
        "group_number",
        "max_price_allowed",
        "min_price_allowed",
        "number_of_stocks",
        "NOT_VALID_KEY",
    ]
    return keys


def get_keys_of_asks_bids():
    """
    [
        '4507558419857064', # id
        '2', # row_number (starting from 1)
        '1', # num_of_sellers
        '1', # number_of_buyers
        '10820', # buy_price
        '10870', # sell_price
        '700', # buy_volume
        '3000' # sell_volume
    ]
    """
    keys = [
        "id",
        "row_number",
        "num_of_sellers",
        "number_of_buyers",
        "buy_price",
        "sell_price",
        "buy_volume",
        "sell_volume",
    ]
    return keys


def get_keys_of_client_types():
    """
    [
        '5054819322815158', # id
        '406', # num_of_individual_buyers
        '5', # num_of_corporate_buyers
        '4979247', # volume_of_individual_buyers
        '528270', # volume_of_corporate_buyers
        '554', # num_of_individual_sellers
        '2', # num_of_corporate_sellers
        '5302517', # volume_of_individual_sellers
        '205000' # volume_of_corporate_sellers
    ]
    """
    keys = [
        "index",
        "numof_individual_buy",
        "numof_corporate_buy",
        "vol_individual_buy",
        "vol_corporate_buy",
        "numof_individual_sell",
        "numof_corporate_sell",
        "vol_individual_sell",
        "vol_corporate_sell",
    ]
    return keys


if __name__ == "__main__":
    d = {
        "s": {"index": 1, "dummy": 100},
        "a": {"index": 2, "dummy": 100},
        "j": {"index": 3, "dummy": 100},
    }
    print(get_index_to_symbol_map(d))
    # output >>
    # {
    # 1: {'dummy': 100, 'symbol': 's'},
    # 2: {'dummy': 100, 'symbol': 'a'},
    # 3: {'dummy': 100, 'symbol': 'j'}
    # }
