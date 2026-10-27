#!/usr/bin/env python3
"""scripts/check_eval.py のテスト。出発点のままでは不合格、手で作った答えでは合格になるかを確かめる。"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_eval import CASES, ROOT, check, load  # noqa: E402
from validate_keymap import validate  # noqa: E402

results = []


def ok(name, cond):
    results.append((name, bool(cond)))


def put(km, layer, r, c, key):
    km["layers"][layer]["keys"][r - 1][c - 1] = key


def reach_user1(km):
    """fn の 1 行目 2 列目に MO(3) を置き、ベースの MO(1) からたどって user1 へ行けるようにする。"""
    put(km, 1, 1, 2, "MO(3)")


def answers(starts):
    """評価例ごとに、合格するはずの答えを出発点から作る。"""
    d, m = starts["default"], starts["mac"]
    a = {}

    km = copy.deepcopy(d)  # 1: user1 の左手側に Photoshop、ベース左下の Language2 を MO(3) に
    for c, k in enumerate(["WM(Z, LGui)", "B", "E", "V", "LeftBracket", "RightBracket"], 1):
        put(km, 3, 2, c, k)
    put(km, 0, 4, 4, "MO(3)")
    a["1"] = km

    km = copy.deepcopy(d)  # 2: user2 に P V A、ベースの Grave を TG(4) に
    for c, k in enumerate(["P", "V", "A"], 2):
        put(km, 4, 2, c, k)
    put(km, 0, 4, 10, "TG(4)")
    a["2"] = km

    for cid, start in (("3", d), ("M3", m)):  # テンキーの並びを user1 の右側に
        km = copy.deepcopy(start)
        for r, row in enumerate([["Kp7", "Kp8", "Kp9"], ["Kp4", "Kp5", "Kp6"], ["Kp1", "Kp2", "Kp3"]], 1):
            for c, k in enumerate(row, 8):
                put(km, 3, r, c, k)
        reach_user1(km)
        a[cid] = km

    km = copy.deepcopy(d)  # 4: user1 のエンコーダを左右に
    km["layers"][3]["encoder"] = {"cw": "Right", "ccw": "Left"}
    reach_user1(km)
    a["4"] = km

    for cid, start in (("6", d), ("M6", m)):  # fn の HJKL を矢印に
        km = copy.deepcopy(start)
        for c, k in zip(range(7, 11), ["Left", "Down", "Up", "Right"]):
            put(km, 1, 2, c, k)
        a[cid] = km

    for cid, start, mod in (("7", d, "LCtrl"), ("M7", m, "LGui")):  # fn の左下にコピーとペースト
        km = copy.deepcopy(start)
        put(km, 1, 3, 2, f"WM(C, {mod})")
        put(km, 1, 3, 3, f"WM(V, {mod})")
        a[cid] = km

    for cid, start, keys in (
        ("8", d, ["Enter", "Backspace", "Space", "Escape", "WM(Z, LCtrl)"]),
        ("M8", m, ["Enter", "Backspace", "Space", "WM(Z, LGui)"]),
    ):  # user1 の 2 行目左に寄せる
        km = copy.deepcopy(start)
        for c, k in enumerate(keys, 1):
            put(km, 3, 2, c, k)
        reach_user1(km)
        a[cid] = km
    return a


def main():
    cases = load(CASES)
    starts = {name: load(ROOT / path) for name, path in cases["starts"].items()}
    good = answers(starts)
    ok("答えの例がすべての評価例にある", set(good) == set(cases["cases"]))

    for cid, case in cases["cases"].items():
        start = starts[case["start"]]
        ok(f"{cid}: 出発点のままでは不合格", check(cid, start, cases))
        ok(f"{cid}: 答えの例は形式どおり", validate(good[cid]) == [])
        ok(f"{cid}: 答えの例は合格", check(cid, good[cid], cases) == [])

    # してはいけないことを1つ足すと不合格になる
    bad = copy.deepcopy(good["1"])
    put(bad, 0, 2, 2, "WM(Z, LGui)")
    ok("1: ベースの文字キーを置き換えると不合格", check("1", bad, cases))
    bad = copy.deepcopy(good["1"])
    put(bad, 0, 4, 4, "Language2")
    put(bad, 0, 4, 9, "MO(3)")
    ok("1: 切り替えが右手側だけなら不合格", check("1", bad, cases))
    bad = copy.deepcopy(good["2"])
    put(bad, 0, 4, 1, "No")
    ok("2: MO(1) を消すと不合格", check("2", bad, cases))
    bad = copy.deepcopy(good["3"])
    for r, row in enumerate([["Kp1", "Kp2", "Kp3"], ["Kp4", "Kp5", "Kp6"], ["Kp7", "Kp8", "Kp9"]], 1):
        for c, k in enumerate(row, 2):
            put(bad, 4, r, c, k)
    ok("3: 電話式の並びもあると不合格", check("3", bad, cases))
    bad = copy.deepcopy(good["4"])
    bad["layers"][0]["encoder"] = {"cw": "Right", "ccw": "Left"}
    ok("4: ベースのエンコーダを変えると不合格", check("4", bad, cases))
    bad = copy.deepcopy(good["M6"])
    put(bad, 0, 4, 9, "No")
    ok("M6: ベース右下の矢印を消すと不合格", check("M6", bad, cases))
    bad = copy.deepcopy(good["7"])
    put(bad, 4, 1, 1, "WM(C, LGui)")
    ok("7: Mac 向けを使うと不合格", check("7", bad, cases))
    bad = copy.deepcopy(good["M7"])
    put(bad, 1, 4, 6, "WM(C, LGui)")
    put(bad, 1, 3, 2, "No")
    ok("M7: 押せない位置に置いても合格にならない", check("M7", bad, cases))
    bad = copy.deepcopy(good["8"])
    put(bad, 0, 1, 8, "No")
    ok("8: ベースの右手側を No にすると不合格", check("8", bad, cases))
    bad = copy.deepcopy(good["M8"])
    put(bad, 1, 1, 1, "No")
    ok("M8: fn の Escape を消すと不合格", check("M8", bad, cases))

    # 行けないレイヤーに置いても合格にならない
    for cid in ("3", "4", "8", "M8"):
        bad = copy.deepcopy(good[cid])
        put(bad, 1, 1, 2, starts[cases["cases"][cid]["start"]]["layers"][1]["keys"][0][1])
        ok(f"{cid}: 切り替えキーが無いレイヤーに置くと不合格", check(cid, bad, cases))
    # fn からたどって行けるレイヤーも数える
    chain = copy.deepcopy(good["2"])
    put(chain, 0, 4, 10, "Grave")
    put(chain, 1, 1, 3, "TG(4)")
    ok("2: ベース → fn → user2 とたどれれば合格", check("2", chain, cases) == [])
    # 書き方の揺れをそろえる
    bad = copy.deepcopy(good["7"])
    put(bad, 4, 1, 1, "WM(C,LGui)")
    ok("7: 空白なしの WM(C,LGui) も Mac 向けと見なす", check("7", bad, cases))
    var = copy.deepcopy(good["M7"])
    put(var, 1, 3, 2, "WM(C,LGui)")
    ok("M7: 空白なしでも合格", check("M7", var, cases) == [])
    var = copy.deepcopy(good["8"])
    put(var, 3, 2, 5, "WM(Z,LCtrl)")
    ok("8: 空白なしでも合格", check("8", var, cases) == [])
    # 4 行目は 6 番目より右がマトリクスで 1 つずれる
    blk = copy.deepcopy(starts["default"])
    for r, row in ((2, ["Kp7", "Kp8", "Kp9"]), (3, ["Kp4", "Kp5", "Kp6"])):
        for c, k in enumerate(row, 9):
            put(blk, 3, r, c, k)
    for c, k in enumerate(["Kp1", "Kp2", "Kp3"], 8):
        put(blk, 3, 4, c, k)
    reach_user1(blk)
    ok("3: 4 行目にかかるテンキーの並びを、マトリクスの列でそろえて判定する", check("3", blk, cases) == [])
    skew = copy.deepcopy(blk)
    for c, k in enumerate(["Kp1", "Kp2", "Kp3"], 9):
        put(skew, 3, 4, c, k)
    put(skew, 3, 4, 8, "_")
    ok("3: 4 行目で 1 つずれた並びは不合格", check("3", skew, cases))
    # M8: fn の Escape は動かしても消していなければよい
    mv = copy.deepcopy(good["M8"])
    put(mv, 1, 1, 1, "No")
    put(mv, 1, 2, 1, "Escape")
    ok("M8: fn の中で Escape を動かすのはよい", check("M8", mv, cases) == [])

    failed = [name for name, passed in results if not passed]
    for name in failed:
        print(f"test_check_eval: 失敗: {name}")
    if not failed:
        print(f"test_check_eval: {len(results)} 件 ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
