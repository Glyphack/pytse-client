from datetime import datetime, timedelta
from typing import Generator


def datetime_range(
    start=None, end=None
) -> Generator[datetime.date, None, None]:
    span = end - start
    for i in range(span.days + 1):
        yield start + timedelta(days=i)
