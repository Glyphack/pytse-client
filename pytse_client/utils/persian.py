def replace_arabic(string: str):
    return string.replace("ك", "ک").replace("ي", "ی").strip(" \u200c")


def replace_persian(string: str):
    return string.replace("ک", "ك").replace("ی", "ي").strip(" \u200c")
