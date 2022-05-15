def get_index_to_symbol_map(dic: dict):
    """
    convert {<symbol>: {index:<index>,...}}
    to
    {<index>: {symbol:<symbol>,...}}
    """
    tmp_dic = {item[1]["index"]: {**item[1], "symbol": item[0]}
               for item in dic.items()}
    final_dic = {item[0]: {item2[0]: item2[1] for item2 in item[1].items(
    ) if item2[0] != "index"} for item in tmp_dic.items()}
    return final_dic


if __name__ == '__main__':
    d = {"s": {"index": 1, "dummy": 100}, "a": {
        "index": 2, "dummy": 100}, "j": {"index": 3, "dummy": 100}}
    print(get_index_to_symbol_map(d))
    # output >>
    # {
    # 1: {'dummy': 100, 'symbol': 's'},
    # 2: {'dummy': 100, 'symbol': 'a'},
    # 3: {'dummy': 100, 'symbol': 'j'}
    # }
