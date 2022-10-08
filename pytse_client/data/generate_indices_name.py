import json
import re

import requests as req

if __name__ == "__main__":
    text = req.get(
        "http://www.tsetmc.com/Loader.aspx?Partree=151315&Flow=1"
    ).text

    market_indexes = re.findall(
        r'<tr><td><a target="_blank" href="Loader'
        r'\.aspx\?ParTree=15131J&i=\d*">.*</a></td>',
        text,
    )
    final_dict = {}

    for market_index in market_indexes:
        key = re.search('">(.*)</a></td>', market_index).group(1)
        index = re.search(
            '<tr><td><a target="_blank" href="Loader'
            r"\.aspx\?ParTree=15131J&i=(\d*)",
            market_index,
        ).group(1)
        section_number = re.search(r"(^\d+|\d+$)", key)
        section_number = (
            int(section_number.group(1)) if section_number is not None else ""
        )
        key = re.sub(r"^\d+|\d+$|-", "", key)
        final_dict[key] = {"index": index, "section_number": section_number}

    with open("indices_name.json", "w", encoding="utf8") as f:
        json.dump(final_dict, f, indent=2, ensure_ascii=False)
