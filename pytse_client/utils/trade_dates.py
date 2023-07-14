import datetime
from pytse_client.ticker.ticker import Ticker


def get_valid_dates(
    ticker: Ticker,
    start_date: datetime.date,
    end_date: datetime.date,
):
    all_valid_dates = []
    for n in range((end_date - start_date).days + 1):
        date = start_date + datetime.timedelta(n)
        if date in ticker.trade_dates:
            all_valid_dates.append(date)
    return all_valid_dates
