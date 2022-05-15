from .request_session import requests_retry_session


def get_raw_text(url: str, timeout=10):
    raw_text = requests_retry_session()\
        .get(url, timeout=timeout).text
    return raw_text
