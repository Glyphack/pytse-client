# utilities to extract data from APIs related to Ticker module

from collections import namedtuple
from typing import List, Tuple

Order = namedtuple('order', ['count', 'volume', 'price'])


def get_orders(orders_raw_text: str) -> Tuple[List[Order], List[Order]]:
    if not orders_raw_text:
        return [], []
    buy_orders_set = []
    sell_orders_set = []
    orders = orders_raw_text.split(',')
    orders.pop()  # last item is empty string
    for order_text in orders:
        order_numbers = order_text.split("@")
        print(order_numbers)
        buy_orders_set.append(
            Order(
                order_numbers[0],  # count
                order_numbers[1],  # vol
                order_numbers[2],  # price
            )
        )
        sell_orders_set.append(
            Order(
                order_numbers[5],  # count
                order_numbers[4],  # vol
                order_numbers[3],  # price
            )
        )
    return buy_orders_set, sell_orders_set
