def safe_run(func):

    def func_wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)

        except Exception:
            return None

    return func_wrapper
