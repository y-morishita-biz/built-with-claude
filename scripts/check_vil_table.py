#!/usr/bin/env python3
"""docs/vil-format.md の対応表に、サンプルのキーマップのキーが漏れなく載っているか確かめる。

使い方: python3 scripts/check_vil_table.py <キーマップ JSON> ...
"""
import json
import re
import sys

TABLE = "docs/vil-format.md"
ROW = re.compile(r"^\| `(.+?)` \| `(.+?)` \| `0x[0-9A-F]{4}` \|$", re.MULTILINE)


def table_keys(path):
    with open(path, encoding="utf-8") as f:
        return {m.group(1).replace("\\|", "|") for m in ROW.finditer(f.read())}


def keymap_keys(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    keys = set()
    for layer in data["layers"]:
        for row in layer["keys"]:
            keys.update(row)
        keys.update([layer["encoder"]["cw"], layer["encoder"]["ccw"]])
    return keys


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    known = table_keys(TABLE)
    status = 0
    for path in argv[1:]:
        missing = sorted(keymap_keys(path) - known)
        if missing:
            status = 1
            print(f"{path}: {TABLE} の対応表に無いキー: {', '.join(missing)}")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
