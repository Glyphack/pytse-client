import json
import re
from pathlib import Path

from pytse_client.tsetmc_api import client, index

# On a name clash the index of the earlier flow wins.
INDICES_FLOWS = (1, 2)

INDICES_FILE = Path(__file__).parent / "indices_name.json"


def main():
    indices: dict[str, dict] = {}
    for flow in INDICES_FLOWS:
        flow_indices: dict[str, dict] = {}
        for row in index.parse_indices(client.api.call_indices(flow)):
            section_number = re.search(r"(^\d+|\d+$)", row.name)
            name = re.sub(r"^\d+|\d+$|-", "", row.name).strip()
            flow_indices[name] = {
                "index": row.ins_code,
                "section_number": (
                    int(section_number.group(1)) if section_number else ""
                ),
            }
        for name, value in flow_indices.items():
            indices.setdefault(name, value)
    with open(INDICES_FILE, "w", encoding="utf8") as file:
        json.dump(indices, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
