import datetime
import logging

import aiohttp
from pytse_client import config, tse_settings
from pytse_client.proxy.dto import InstrumentHistoryResponse, ShareholderData
from tenacity import retry
from tenacity.before_sleep import before_sleep_log
from tenacity.wait import wait_random

logger = logging.getLogger(config.LOGGER_NAME)


@retry(
    wait=wait_random(min=3, max=5),
    before_sleep=before_sleep_log(logger, logging.ERROR),
)
async def get_day_shareholders_history(
    ticker_index: str,
    date: datetime.date,
    session: aiohttp.ClientSession,
):
    formatted_date = date.strftime(tse_settings.DATE_FORMAT)
    async with session.get(
        tse_settings.SYMBOL_DAY_INFO_SHAREHOLDERS_DATA.format(
            index=ticker_index, date=formatted_date
        ),
    ) as response:
        response.raise_for_status()
        response_json = await response.json()
        logger.debug(
            "fetched shareholders data for%s date: %s",
            ticker_index,
            formatted_date,
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


@retry(
    # These numbers are not tested
    wait=wait_random(min=3, max=5),
    before_sleep=before_sleep_log(logger, logging.ERROR),
)
async def get_day_ticker_info_history(
    ticker_index: str,
    date: datetime.date,
    session: aiohttp.ClientSession,
) -> InstrumentHistoryResponse:
    """

    Args:
        ticker_index
        date
        session: aiohttp sesison to reuse session will be closed after usage

    Returns: InstrumentHistoryJson
    """
    formatted_date = date.strftime(tse_settings.DATE_FORMAT)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Connection": "keep-alive",
        "Referer": "http://cdn.tsetmc.com/History/71483646978964608/20220830",
        "Sec-GPC": "1",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 9) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.5112.102"
            "Safari/537.36"
        ),
    }
    async with session.get(
        tse_settings.SYMBOL_DAY_INSTRUMENT_INFO_URL.format(
            index=ticker_index, date=formatted_date
        ),
        headers=headers,
    ) as response:
        response.raise_for_status()
        response_json = await response.json()
        logger.debug(
            "fetched instrument info %s date: %s",
            ticker_index,
            formatted_date,
        )
        return InstrumentHistoryResponse(
            response_json["instrumentHistory"]["zTitad"],
            response_json["instrumentHistory"]["baseVol"],
        )
