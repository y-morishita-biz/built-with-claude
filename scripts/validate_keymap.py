#!/usr/bin/env python3
"""docs/keymap-format.md の形式でキーマップ JSON を検証する。"""
import json
import re
import sys

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
LAYER_FN = re.compile(r"^(MO|TG)\((\d+)\)$")


def check_key(key, n_layers):
    if not isinstance(key, str):
        return f"文字列ではない: {key!r}"
    if key in ("TRANS", "NONE"):
        return None
    m = LAYER_FN.match(key)
    if m:
        n = int(m.group(2))
        return None if 0 <= n < n_layers else f"レイヤー番号が範囲外: {key}"
    *mods, base = key.split("+")
    for mod in mods:
        if mod not in MODIFIERS:
            return f"修飾キーではない: {mod} ({key})"
    return None if base in KEYS else f"未知のキー名: {base} ({key})"


def validate(data):
    errors = []
    rows, cols = data.get("rows"), data.get("cols")
    layers = data.get("layers") or []
    if data.get("keyboard") != "dotmatrix40w":
        errors.append("keyboard は dotmatrix40w のみ対応")
    if not layers:
        errors.append("layers が空")
    for i, layer in enumerate(layers):
        where = f"layers[{i}]({layer.get('name')})"
        keys = layer.get("keys") or []
        if len(keys) != rows or any(len(r) != cols for r in keys):
            errors.append(f"{where}: keys が {rows}行×{cols}列ではない")
        for r, row in enumerate(keys):
            for c, key in enumerate(row):
                err = check_key(key, len(layers))
                if err:
                    errors.append(f"{where} [{r}][{c}]: {err}")
        for d in ("cw", "ccw"):
            key = (layer.get("encoder") or {}).get(d)
            err = "未設定" if key is None else check_key(key, len(layers))
            if err:
                errors.append(f"{where} encoder.{d}: {err}")
    return errors


def main(paths):
    status = 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            errors = validate(json.load(f))
        for e in errors:
            print(f"{path}: {e}")
        status |= bool(errors)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
