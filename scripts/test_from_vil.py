#!/usr/bin/env python3
"""scripts/from_vil.py のテスト。サンプルの .vil と JSON が全キー一致するかも確かめる。"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from from_vil import LAYER_BASES, MOD_BITS, RIGHT, SKIPPED, VilError, convert, load_table, vil_value  # noqa: E402
from validate_keymap import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VIL = ROOT / "examples" / "dotmatrix40w-mac.vil"
JSON = ROOT / "examples" / "dotmatrix40w-mac.json"
WM = re.compile(r"WM\((\w+), (.+)\)")
LT = re.compile(r"LT\(([0-9]+), (\w+)\)")
LAYER_FN = re.compile(r"(MO|TG|TO|OSL)\(([0-9]+)\)")
results = []


def check(name, cond):
    results.append((name, bool(cond)))


def rmk_value(key, table):
    """RMK 名を 16 ビット値に戻す。表に無いものは docs/vil-format.md の規則で計算する。"""
    if key in table.rmk_to_value:
        return table.rmk_to_value[key]
    m = WM.fullmatch(key)
    if m:
        bits = 0
        for mod in m.group(2).split(" | "):
            bits |= dict(MOD_BITS)["L" + mod[1:]] | (RIGHT if mod[0] == "R" else 0)
        return bits << 8 | table.rmk_to_value[m.group(1)]
    m = LT.fullmatch(key)
    if m:
        return 0x4000 | int(m.group(1)) << 8 | table.rmk_to_value[m.group(2)]
    m = LAYER_FN.fullmatch(key)
    return LAYER_BASES[m.group(1)] + int(m.group(2))


def raises(vil, table, text=""):
    try:
        convert(vil, table)
    except VilError as e:
        return text in str(e)
    return False


def with_key(vil, key, layer=0, row=0, col=0):
    v = copy.deepcopy(vil)
    v["layout"][layer][row][col] = key
    return v


def first_key(vil, table, key, layer=0):
    return convert(with_key(vil, key, layer), table)[0]["layers"][layer]["keys"][0][0]


def main():
    vil = json.loads(VIL.read_text(encoding="utf-8"))
    table = load_table()
    keymap, notes = convert(vil, table)

    # サンプルの JSON はこの .vil から作ったものと同じで、検証を通る
    check("サンプル JSON が変換結果と一致", keymap == json.loads(JSON.read_text(encoding="utf-8")))
    check("検証を通る", validate(keymap) == [])
    check("combo を読まなかったと知らせる", any(n.startswith("combo ") for n in notes))
    check("settings を読まなかったと知らせる", any(n.startswith("settings ") for n in notes))
    check("空の macro は知らせない", not any(n.startswith("macro ") for n in notes))
    check("uid が一致していれば知らせない", not any("uid" in n for n in notes))

    # 全キーを 16 ビット値に戻し、元の .vil と比べる
    for i, layer in enumerate(keymap["layers"]):
        for r, row in enumerate(vil["layout"][i]):
            cols = [c for c in range(12) if (r, c) != SKIPPED]
            check(f"layout[{i}][{r}] の列数", len(cols) == len(layer["keys"][r]))
            for c, key in zip(cols, layer["keys"][r]):
                check(f"layout[{i}][{r}][{c}]", rmk_value(key, table) == vil_value(row[c], table))
        ccw, cw = vil["encoder_layout"][i][0]
        check(f"encoder[{i}] cw", rmk_value(layer["encoder"]["cw"], table) == vil_value(cw, table))
        check(f"encoder[{i}] ccw", rmk_value(layer["encoder"]["ccw"], table) == vil_value(ccw, table))

    # 個別の規則
    base = keymap["layers"][0]
    check("エンコーダは反時計回りが先", base["encoder"] == {"cw": "MouseWheelDown", "ccw": "MouseWheelUp"})
    check("4 行目は列 6 を飛ばして 11 キー", base["keys"][3][5:7] == ["No", "Enter"])
    check("16 進の文字列を読む", keymap["layers"][1]["keys"][2][5] == "WM(Kc4, LCtrl | LShift | LGui)")
    check("整数のキーを読む", first_key(vil, table, 0x0004) == "A")
    check("表に無い右修飾つきを組み立てる", first_key(vil, table, "0x1205") == "WM(B, RShift)")
    check("表に無い Vial の修飾名を読む", first_key(vil, table, "MEH(KC_A)") == "WM(A, LCtrl | LShift | LAlt)")
    check("表に無いレイヤー操作を読む", first_key(vil, table, "TG(4)") == "TG(4)")
    check("表に無い LT を読む", first_key(vil, table, "LT3(KC_SPACE)") == "LT(3, Space)")
    check("LT を値から組み立てる", first_key(vil, table, 0x412C) == "LT(1, Space)")

    # 止まるべきもの
    check("表に無いキーで止まる", raises(with_key(vil, "KC_NOT_A_KEY"), table, "layout[0][0][0]"))
    check("右側の印だけの修飾で止まる", raises(with_key(vil, "0x1004"), table, "0x1004"))
    check("基本のキー以外への修飾で止まる", raises(with_key(vil, "0x1a8"), table, "0x1a8"))
    check("ベースレイヤーの透過で止まる", raises(with_key(vil, "KC_TRNS"), table, "検証を通らない"))
    check("範囲外のレイヤーで止まる", raises(with_key(vil, "MO(7)"), table, "検証を通らない"))
    check("最上位が配列なら止まる", raises([], table))
    v = copy.deepcopy(vil)
    v["encoder_layout"] = v["encoder_layout"][:4]
    check("エンコーダのレイヤー数の違いで止まる", raises(v, table, "encoder_layout"))

    # 知らせるもの
    v = copy.deepcopy(vil)
    v["uid"] = 1
    check("uid の違いを知らせる", any("uid" in n for n in convert(v, table)[1]))
    v = copy.deepcopy(vil)
    v["macro"] = None
    check("形の崩れた macro も落ちずに知らせる", any(n.startswith("macro ") for n in convert(v, table)[1]))

    failed = [name for name, ok in results if not ok]
    for name in failed:
        print(f"test_from_vil: 失敗: {name}")
    if not failed:
        print(f"test_from_vil: {len(results)} 件 ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
