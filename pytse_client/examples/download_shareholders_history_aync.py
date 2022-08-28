import asyncio
import datetime
import logging
from time import sleep

import aiohttp
from pytse_client import Ticker

# set logging level to info to see progress of getting data
logging.basicConfig(level=logging.INFO)


async def create_session(limit=3):
    """
    optional can change default session
    """
    conn = aiohttp.TCPConnector(limit=limit)
    session = aiohttp.ClientSession(connector=conn)
    return session


async def get_shareholders_history():
    symbols = [
        "شکبیر",
        "برکت",
    ]
    from_times = [
        datetime.timedelta(days=90),
        datetime.timedelta(days=150),
    ]
    for symbol in symbols:
        # limit is the number of parallel requests
        # can increase and decrease speed
        session = await create_session(limit=2)
        print(f"downloading {symbol}")
        shareholders_history = await Ticker(
            symbol
        ).get_shareholders_history_async(session=session)
        shareholders_history.to_csv(f"{str(symbol)}.csv")
        print(f"downloaded {symbol} complete")

        # sleep between to avoid getting blocked
        sleep(50)


asyncio.run(get_shareholders_history())
