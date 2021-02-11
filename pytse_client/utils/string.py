def convert_to_number_if_number(s: str):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return s
