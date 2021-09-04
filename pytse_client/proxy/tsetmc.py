import datetime
import logging
from typing import Union

import aiohttp
import requests
from pytse_client import config, tse_settings
from pytse_client.proxy.dto import ShareholderData
from tenacity import retry, wait_random
from tenacity.before_sleep import before_sleep_log

logger = logging.getLogger(config.LOGGER_NAME)


@retry(
    wait=wait_random(min=3, max=5),
    before_sleep=before_sleep_log(logger, logging.ERROR)
)
async def get_day_shareholders_history(
    ticker_index: str,
    date: datetime.date,
    session: Union[requests.Session, aiohttp.ClientSession],
):
    formatted_date = date.strftime(tse_settings.DATE_FORMAT)
    async with session.get(
        tse_settings.SYMBOL_DAY_INFO_SHAREHOLDERS_DATA.format(
            index=ticker_index, date=formatted_date
        ),
    ) as response:
        response.raise_for_status()
        response_json = await response.json()
        logger.info(
            f"""fetched shareholders data for
             {ticker_index} date: {formatted_date}"""
        )
        result = []
        for shareholders_raw_data in response_json["shareShareholder"]:
            # api returns data for today and tomorrow so we skip tomorrow
            # sometimes when we request data for a day it returns it with
            # tomorrow date instead(bug) so we only check that the
            # date is greater than requested date
            if shareholders_raw_data["dEven"] > int(formatted_date):
                continue
            result.append(
                ShareholderData(
                    id=shareholders_raw_data["shareHolderID"],
                    name=shareholders_raw_data["shareHolderName"],
                    instrument_id=shareholders_raw_data["cIsin"],
                    shares=shareholders_raw_data["numberOfShares"],
                    percentage=shareholders_raw_data["perOfShares"],
                    change=shareholders_raw_data["change"],
                )
            )
        return result
