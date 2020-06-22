import pandas as pd
import numpy as np
import os
import sys
import datetime
sys.path.append('../pytse_client')
import utils
from pytse_client.tse_settings import TSE_CLIENT_TYPE_DATA_URL

symbols = [
    '33887145736684266', #آگاس
    '778253364357513',   #وبملت
    '63704201144621295', #حبندر
    '9536587154100457',  #وپاسار
    '40262275031537922', #دروز
    '22811176775480091', #اخابر
    '13235547361447092', #زاگرس
]

responses = []

for symbol in symbols:
    responses.append(utils.requests_retry_session().get(TSE_CLIENT_TYPE_DATA_URL.format(symbol), timeout=5))

date_now = str(datetime.datetime.now())

for ind, symbol in enumerate(symbols):
    with open('samples/{}_{}'.format(date_now, symbol), 'w') as f:
        f.write(responses[ind].text)