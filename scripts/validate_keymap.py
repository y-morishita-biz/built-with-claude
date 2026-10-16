#!/usr/bin/env python3
"""docs/keymap-format.md の形式でキーマップ JSON を検証する。"""
import json
import re
import sys
from pathlib import Path

# 実機の matrix_map に合わせた各行のキー数。最下段は (3,6) がないので 11
ROW_LENGTHS = [12, 12, 12, 11]
N_LAYERS = 5
MODIFIERS = {"LCtrl", "LShift", "LAlt", "LGui", "RCtrl", "RShift", "RAlt", "RGui"}
KEYCODES = {
    line.strip()
    for line in (Path(__file__).resolve().parent.parent / "data" / "rmk-keycodes.txt")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip() and not line.startswith("#")
}
LAYER_FN = re.compile(r"(MO|TG|TO|OSL)\(([0-9])\)")
LT = re.compile(r"LT\(([0-9]), *([A-Za-z0-9]+)\)")
WM = re.compile(r"WM\(([A-Za-z0-9]+), *([A-Za-z| ]+)\)")
SHIFTED = re.compile(r"SHIFTED\(([A-Za-z0-9]+)\)")
LAYER_NAME = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*")


def check_layer(n, n_layers, key):
    return None if int(n) < n_layers else f"レイヤー番号が範囲外: {key}"


def check_plain(code, key):
    return None if code in KEYCODES else f"RMK にないキー名: {code!r} ({key})"


def check_key(key, n_layers, is_base, is_encoder=False):
    if not isinstance(key, str):
        return f"文字列ではない: {key!r}"
    if key == "_":
        return "ベースレイヤーでは _ を使えない" if is_base else None
    if key == "No":
        return None
    m = LAYER_FN.fullmatch(key)
    if m:
        if is_encoder:
            return f"エンコーダにはレイヤー切り替えを割り当てられない: {key}"
        return check_layer(m.group(2), n_layers, key)
    m = LT.fullmatch(key)
    if m:
        if is_encoder:
            return f"エンコーダにはレイヤー切り替えを割り当てられない: {key}"
        return check_layer(m.group(1), n_layers, key) or check_plain(m.group(2), key)
    m = WM.fullmatch(key)
    if m:
        mods = [x.strip() for x in m.group(2).split("|")]
        for mod in mods:
            if mod not in MODIFIERS:
                return f"修飾キーではない: {mod!r} ({key})"
        if len(set(mods)) != len(mods):
            return f"修飾キーが重複している: {key}"
        return check_plain(m.group(1), key)
    m = SHIFTED.fullmatch(key)
    if m:
        return check_plain(m.group(1), key)
    return check_plain(key, key)


def validate(data):
    if not isinstance(data, dict):
        return ["最上位が JSON オブジェクトではない"]
    errors = []
    if data.get("keyboard") != "dotmatrix40w":
        errors.append("keyboard は dotmatrix40w のみ対応")
    if type(data.get("version")) is not int or data.get("version") != 2:
        errors.append("version は 2 のみ対応")
    layers = data.get("layers")
    if not isinstance(layers, list) or len(layers) != N_LAYERS:
        return errors + [f"layers は {N_LAYERS} 個の配列でなければならない"]
    seen_names = set()
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            errors.append(f"layers[{i}]: オブジェクトではない")
            continue
        name = layer.get("name")
        where = f"layers[{i}]({name})"
        if not isinstance(name, str) or not LAYER_NAME.fullmatch(name):
            errors.append(f"{where}: name は英小文字、数字、ハイフンのみ")
        elif name in seen_names:
            errors.append(f"{where}: name が重複している")
        seen_names.add(name)
        keys = layer.get("keys")
        if (
            not isinstance(keys, list)
            or len(keys) != len(ROW_LENGTHS)
            or any(not isinstance(r, list) or len(r) != n for r, n in zip(keys, ROW_LENGTHS))
        ):
            errors.append(f"{where}: keys の各行のキー数が {ROW_LENGTHS} ではない")
        else:
            for r, row in enumerate(keys):
                for c, key in enumerate(row):
                    err = check_key(key, N_LAYERS, i == 0)
                    if err:
                        errors.append(f"{where} [{r}][{c}]: {err}")
        encoder = layer.get("encoder")
        if not isinstance(encoder, dict):
            errors.append(f"{where}: encoder がない")
            continue
        for d in ("cw", "ccw"):
            key = encoder.get(d)
            err = "未設定" if key is None else check_key(key, N_LAYERS, i == 0, is_encoder=True)
            if err:
                errors.append(f"{where} encoder.{d}: {err}")
    return errors


def main(paths):
    if not paths:
        print("使い方: validate_keymap.py FILE.json [...]", file=sys.stderr)
        return 2
    status = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                errors = validate(json.load(f))
        except (OSError, ValueError) as e:
            errors = [f"読み込めない: {e}"]
        for e in errors:
            print(f"{path}: {e}")
        status |= bool(errors)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
