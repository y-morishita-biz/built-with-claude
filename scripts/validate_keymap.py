#!/usr/bin/env python3
"""docs/keymap-format.md の形式でキーマップ JSON を検証する。"""
import json
import re
import sys

ROWS, COLS = 4, 12
MODIFIERS = {"LCTRL", "LSHIFT", "LALT", "LGUI", "RCTRL", "RSHIFT", "RALT", "RGUI"}
KEYS = (
    {chr(c) for c in range(ord("A"), ord("Z") + 1)}
    | {str(n) for n in range(10)}
    | {f"F{n}" for n in range(1, 13)}
    | MODIFIERS
    | {
        "ESC", "TAB", "SPACE", "ENTER", "BSPC", "DEL", "INS",
        "LEFT", "RIGHT", "UP", "DOWN", "HOME", "END", "PGUP", "PGDN",
        "MINUS", "EQUAL", "LBKT", "RBKT", "BSLH", "SEMI", "QUOTE", "GRAVE",
        "COMMA", "DOT", "SLASH", "CAPS", "PSCRN",
        "LANG1", "LANG2", "VOLU", "VOLD", "MUTE", "PLAY", "NEXT", "PREV",
    }
)
LAYER_FN = re.compile(r"(MO|TG)\((\d+)\)")
LAYER_NAME = re.compile(r"[a-z][a-z-]*")


def check_key(key, n_layers, is_base):
    if not isinstance(key, str):
        return f"文字列ではない: {key!r}"
    if key == "TRANS":
        return "ベースレイヤーでは TRANS を使えない" if is_base else None
    if key == "NONE":
        return None
    m = LAYER_FN.fullmatch(key)
    if m:
        n = int(m.group(2))
        return None if 0 <= n < n_layers else f"レイヤー番号が範囲外: {key}"
    *mods, base = key.split("+")
    for mod in mods:
        if mod not in MODIFIERS:
            return f"修飾キーではない: {mod!r} ({key})"
    if len(set(mods)) != len(mods):
        return f"修飾キーが重複している: {key}"
    return None if base in KEYS else f"未知のキー名: {base!r} ({key})"


def validate(data):
    if not isinstance(data, dict):
        return ["最上位が JSON オブジェクトではない"]
    errors = []
    if data.get("keyboard") != "dotmatrix40w":
        errors.append("keyboard は dotmatrix40w のみ対応")
    if data.get("version") != 1:
        errors.append("version は 1 のみ対応")
    if data.get("rows") != ROWS or data.get("cols") != COLS:
        errors.append(f"rows / cols は {ROWS} / {COLS} でなければならない")
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + ["layers が空、または配列ではない"]
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            errors.append(f"layers[{i}]: オブジェクトではない")
            continue
        name = layer.get("name")
        where = f"layers[{i}]({name})"
        if not isinstance(name, str) or not LAYER_NAME.fullmatch(name):
            errors.append(f"{where}: name は英小文字とハイフンのみ")
        keys = layer.get("keys")
        if (
            not isinstance(keys, list)
            or len(keys) != ROWS
            or any(not isinstance(r, list) or len(r) != COLS for r in keys)
        ):
            errors.append(f"{where}: keys が {ROWS}行×{COLS}列の配列ではない")
        else:
            for r, row in enumerate(keys):
                for c, key in enumerate(row):
                    err = check_key(key, len(layers), i == 0)
                    if err:
                        errors.append(f"{where} [{r}][{c}]: {err}")
        encoder = layer.get("encoder")
        if not isinstance(encoder, dict):
            errors.append(f"{where}: encoder がない")
            continue
        for d in ("cw", "ccw"):
            key = encoder.get(d)
            err = "未設定" if key is None else check_key(key, len(layers), i == 0)
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
