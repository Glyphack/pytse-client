import re

import requests
from key_stats import filter_key_value

try:
    response = requests.get(
        "http://redirectcdn.tsetmc.com" "/Site.aspx?ParTree=151713"
    )
except Exception as e:
    print("--- Could not retrieve key stats documentation ---")
    raise e
text = response.text
key_stats_ls = [
    line for line in text.split("\n") if re.search(r"is[0-9]+", line)
]
nums_and_disc = []
for line in key_stats_ls:
    number, disc = re.split(r"\]|\[|\&", line)[1:3]
    number = int(number[2:])
    disc = re.split(r"\<\/div\>", disc)[0]
    nums_and_disc.append((number, disc))
with open("README.md", "w", encoding="utf8") as f2:
    f2.write(
        "در این بخش آمار کلیدی را در قالب" " یک نگاشت سه عضوی مشاهده می‌کنید."
    )
    f2.write("\n\n\n| شماره | توضیحات | سمبل |\n")
    f2.write("| --- | --- | --- |\n")
    for number, persian_explanation in nums_and_disc:
        symbol = filter_key_value[number]
        f2.write(f"| {number} | {persian_explanation} | {symbol} |\n")
