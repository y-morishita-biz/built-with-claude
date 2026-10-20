#!/usr/bin/env python3
"""Vial のレイアウトファイル(.vil)を読み、キーマップ JSON(version 2)を出す。

使い方: python3 scripts/from_vil.py path/to/layout.vil > out.json

キーの対応は docs/vil-format.md の表から引き、レイヤーと修飾つきのキーは同じ文書の規則で値から組み立てる。
読めないキーがあったり、結果が scripts/validate_keymap.py の検証を通らなかったりすると止まる。
キーマップ JSON に入らない設定(combo、tap_dance、macro、settings など)は読まず、標準エラーに知らせる。
"""
import json
import re
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_keymap import N_LAYERS, ROW_LENGTHS, validate  # noqa: E402

TABLE = Path(__file__).resolve().parent.parent / "docs" / "vil-format.md"
ROW = re.compile(r"^\| `(.+?)` \| `(.+?)` \| `(0x[0-9A-F]{4})` \|$", re.MULTILINE)
HEX = re.compile(r"0x[0-9a-fA-F]{1,4}")
LAYER_NAMES = ["base", "fn", "media", "user1", "user2"]
UID = 72128238669483254
# .vil は 4 行 × 12 列。キーマップ JSON の 4 行目は列 6 を飛ばした 11 キー
VIL_ROWS, VIL_COLS = 4, 12
SKIPPED = (3, 6)
assert len(LAYER_NAMES) == N_LAYERS
assert ROW_LENGTHS == [VIL_COLS - (r == SKIPPED[0]) for r in range(VIL_ROWS)]
# 修飾のビット。WM の書き方の順番もこの順にする。右側はこれに 0x10 を足す
MOD_BITS = [("LCtrl", 0x01), ("LShift", 0x02), ("LAlt", 0x04), ("LGui", 0x08)]
RIGHT = 0x10
# Vial が修飾つきのキーに使う名前(通信の版 6)。上位 8 ビットの値
WRAPPERS = {
    "LCTL": 0x01, "LSFT": 0x02, "C_S": 0x03, "LCS": 0x03, "LALT": 0x04, "LCA": 0x05,
    "LSA": 0x06, "MEH": 0x07, "LGUI": 0x08, "LCG": 0x09, "SGUI": 0x0A, "LSG": 0x0A,
    "LAG": 0x0C, "LCAG": 0x0D, "HYPR": 0x0F,
    "RCTL": 0x11, "RSFT": 0x12, "RALT": 0x14, "RGUI": 0x18, "RCG": 0x19,
}
WRAPPED = re.compile(r"([A-Z_]+)\((KC_\w+)\)")
LAYER_FN = re.compile(r"(MO|TG|TO|OSL)\(([0-9]+)\)")
LAYER_TAP = re.compile(r"LT([0-9]+)\((KC_\w+)\)")
# 値からレイヤー操作を組み立てる規則(docs/vil-format.md)
LAYER_BASES = {"TO": 0x5200, "MO": 0x5220, "TG": 0x5260, "OSL": 0x5280}
# 修飾や LT と組み合わせられる基本のキー(文字・記号・テンキーなどと修飾キー)
BASIC = set(range(0x04, 0xA5)) | set(range(0xE0, 0xE8))
# キーマップ JSON に入らないので読まない項目と、何も設定していないかどうかの判定
NOT_READ = {
    "macro": lambda v: isinstance(v, list) and all(not m for m in v),
    "tap_dance": lambda v: isinstance(v, list)
    and all(isinstance(t, list) and all(k == "KC_NO" for k in t[:4]) for t in v),
    "combo": lambda v: isinstance(v, list)
    and all(isinstance(c, list) and all(k == "KC_NO" for k in c) for c in v),
    "key_override": lambda v: v == [],
    "alt_repeat_key": lambda v: v == [],
    "settings": lambda v: v == {},
}

Table = namedtuple("Table", "vil_to_rmk value_to_rmk rmk_to_value vil_to_value")


class VilError(Exception):
    pass


def load_table(path=TABLE):
    """表を読み、.vil の文字列・16 ビット値・RMK 名のあいだの対応を返す。"""
    t = Table({}, {}, {}, {})
    for m in ROW.finditer(path.read_text(encoding="utf-8")):
        rmk, vil, value = m.group(1).replace("\\|", "|"), m.group(2), int(m.group(3), 16)
        t.vil_to_rmk.setdefault(vil, rmk)
        t.value_to_rmk.setdefault(value, rmk)
        t.rmk_to_value.setdefault(rmk, value)
        t.vil_to_value.setdefault(vil, value)
    return t


def mods_name(bits):
    side = "R" if bits & RIGHT else "L"
    mods = [side + name[1:] for name, bit in MOD_BITS if bits & bit]
    return " | ".join(mods) if mods else None


def decode_value(value, table):
    """16 ビット値を RMK 名にする。表に無いものは規則で組み立てる。組み立てられなければ None。"""
    if value in table.value_to_rmk:
        return table.value_to_rmk[value]
    low = value & 0xFF
    basic = table.value_to_rmk.get(low) if low in BASIC else None
    if 0x0100 <= value <= 0x1FFF and basic:
        mods = mods_name(value >> 8)
        return f"WM({basic}, {mods})" if mods else None
    if 0x4000 <= value <= 0x4FFF and basic:
        return f"LT({(value >> 8) & 0xF}, {basic})"
    for fn, base in LAYER_BASES.items():
        if base <= value < base + 0x10:
            return f"{fn}({value - base})"
    return None


def vil_value(key, table):
    """.vil の 1 キーを 16 ビット値にする。読めなければ None。"""
    if isinstance(key, int) and not isinstance(key, bool):
        return key
    if not isinstance(key, str):
        return None
    if key in table.vil_to_value:
        return table.vil_to_value[key]
    if HEX.fullmatch(key):
        # Vial は名前のないキーを "0xb21" のような 16 進の文字列で保存する
        return int(key, 16)
    m = WRAPPED.fullmatch(key)
    if m and m.group(1) in WRAPPERS and m.group(2) in table.vil_to_value:
        return WRAPPERS[m.group(1)] << 8 | table.vil_to_value[m.group(2)]
    m = LAYER_FN.fullmatch(key)
    if m and int(m.group(2)) < 16:
        return LAYER_BASES[m.group(1)] + int(m.group(2))
    m = LAYER_TAP.fullmatch(key)
    if m and int(m.group(1)) < 16 and m.group(2) in table.vil_to_value:
        return 0x4000 | int(m.group(1)) << 8 | table.vil_to_value[m.group(2)]
    return None


def decode_key(key, table, where):
    if isinstance(key, str) and key in table.vil_to_rmk:
        return table.vil_to_rmk[key]
    value = vil_value(key, table)
    rmk = None if value is None else decode_value(value, table)
    if rmk is None:
        raise VilError(f"{where}: 読めないキー(docs/vil-format.md の表と規則に無い): {key!r}")
    return rmk


def is_grid(x, rows, cols):
    return isinstance(x, list) and len(x) == rows and all(isinstance(r, list) and len(r) == cols for r in x)


def convert(vil, table=None):
    """.vil の中身からキーマップ JSON(dict)と、知らせることの一覧を返す。"""
    table = table or load_table()
    if not isinstance(vil, dict):
        raise VilError("最上位が JSON オブジェクトではない")
    notes = []
    if vil.get("uid") != UID:
        notes.append(f"uid が dotmatrix40W のもの({UID})ではない: {vil.get('uid')!r}")
    layout, encoders = vil.get("layout"), vil.get("encoder_layout")
    if not isinstance(layout, list) or len(layout) != N_LAYERS:
        raise VilError(f"layout は {N_LAYERS} レイヤーでなければならない")
    if not isinstance(encoders, list) or len(encoders) != N_LAYERS:
        raise VilError(f"encoder_layout は {N_LAYERS} レイヤーでなければならない")
    layers = []
    for i, (name, rows, enc) in enumerate(zip(LAYER_NAMES, layout, encoders)):
        if not is_grid(rows, VIL_ROWS, VIL_COLS):
            raise VilError(f"layout[{i}] は {VIL_ROWS} 行 × {VIL_COLS} 列でなければならない")
        keys = [
            [decode_key(k, table, f"layout[{i}][{r}][{c}]") for c, k in enumerate(row) if (r, c) != SKIPPED]
            for r, row in enumerate(rows)
        ]
        if not is_grid(enc, 1, 2):
            raise VilError(f"encoder_layout[{i}] は 1 × 2 でなければならない")
        # .vil は [反時計回り, 時計回り] の順
        ccw, cw = (decode_key(k, table, f"encoder_layout[{i}][0][{j}]") for j, k in enumerate(enc[0]))
        layers.append({"name": name, "keys": keys, "encoder": {"cw": cw, "ccw": ccw}})
    keymap = {"keyboard": "dotmatrix40w", "version": 2, "layers": layers}
    errors = validate(keymap)
    if errors:
        raise VilError("読み込んだ結果が検証を通らない: " + "; ".join(errors))
    for key, is_empty in NOT_READ.items():
        if key in vil and not is_empty(vil[key]):
            notes.append(f"{key} はキーマップ JSON に入らないので読まなかった")
    return keymap, notes


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as f:
            keymap, notes = convert(json.load(f))
    except (OSError, ValueError, VilError) as e:
        print(f"{argv[1]}: {e}", file=sys.stderr)
        return 1
    for note in notes:
        print(f"{argv[1]}: {note}", file=sys.stderr)
    json.dump(keymap, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
