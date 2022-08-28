import functools


def catch(*exception_args):
    def wrapper(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):

            try:
                return func(*args, **kwargs)

            except exception_args:
                return None

        return inner

    return wrapper
