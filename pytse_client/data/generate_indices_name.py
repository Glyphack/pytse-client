import requests as req
import re
import json


if __name__ == '__main__':
    text = req.get(
        "http://www.tsetmc.com/Loader.aspx?Partree=151315&Flow=1").text

    ls = re.findall(
        r'<tr><td><a target="_blank" href="Loader\.aspx\?ParTree=15131J&i=\d*">.*</a></td>', text)

    final_list = []

    for toBeIndex in ls:
        key = re.search(
            '">(.*)</a></td>', toBeIndex).group(1)
        index = re.search(
            '<tr><td><a target="_blank" href="Loader\.aspx\?ParTree=15131J&i=(\d*)', toBeIndex).group(1)
        section_number = re.search(r'(^\d+|\d+$)', key)
        section_number = int(section_number.group(
            1)) if section_number != None else ""
        key = re.sub(r'^\d+|\d+$|-', '', key)
        final_list.append(
            {key: {"index": index, "section_number": section_number}})

    with open("indices_name.json", "w") as f:
        jsp = json.dump(final_list, f, indent=2, ensure_ascii=False)
