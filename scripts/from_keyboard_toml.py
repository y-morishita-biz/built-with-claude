#!/usr/bin/env python3
"""RMK の keyboard.toml から docs/keymap-format.md 形式のキーマップ JSON を作る。

使い方: from_keyboard_toml.py path/to/keyboard.toml > out.json
"""
import json
import re
import sys
import tomllib


def expand_aliases(token, aliases):
    def repl(m):
        name = m.group(1)
        if name not in aliases:
            sys.exit(f"未定義の別名: @{name}")
        return aliases[name]

    return re.sub(r"@([A-Za-z0-9_]+)", repl, token)


def split_keys(line):
    """空白区切り。ただし括弧の中の空白とカンマでは区切らない。"""
    tokens, depth, cur = [], 0, ""
    for ch in line:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur:
                tokens.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        tokens.append(cur)
    return tokens


def main(path):
    with open(path, "rb") as f:
        conf = tomllib.load(f)
    aliases = conf.get("aliases", {})
    layers = []
    for layer in conf["layer"]:
        rows = [
            [expand_aliases(k, aliases) for k in split_keys(line)]
            for line in layer["keys"].strip().splitlines()
        ]
        # エンコーダの設定がないレイヤーは何もしない扱いにする
        cw, ccw = (layer.get("encoders") or [["No", "No"]])[0]
        layers.append({"name": layer["name"], "keys": rows, "encoder": {"cw": cw, "ccw": ccw}})
    out = {"keyboard": "dotmatrix40w", "version": 2, "layers": layers}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main(sys.argv[1])
