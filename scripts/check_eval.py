#!/usr/bin/env python3
"""評価例(docs/eval-cases.md)のうち、キーの位置で判定できる条件を確かめる。

使い方: python3 scripts/check_eval.py <評価例の番号> <キーマップ JSON>
例:     python3 scripts/check_eval.py M3 out.json

条件は evals/cases.json にある。「〜を説明する」の項目は対象外で、Claude の返答を読んで確かめる。
「どれかのレイヤーで」の条件は、ベースから切り替えキーをたどって行けるレイヤーだけを数える。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_keymap import LAYER_FN, LT, MODIFIERS, WM, validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases.json"
# エンコーダの下に重なって押せない位置(4 行目 6 列目)
UNPRESSABLE = (4, 6)
LETTER = re.compile(r"[A-Z]")
MOD_ORDER = sorted(MODIFIERS)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def norm(key):
    """書き方の揺れ(空白、修飾キーの順番)をそろえる。"""
    m = WM.fullmatch(key)
    if m:
        mods = sorted((x.strip() for x in m.group(2).split("|")), key=lambda x: MOD_ORDER.index(x) if x in MOD_ORDER else len(MOD_ORDER))
        return f"WM({m.group(1)}, {' | '.join(mods)})"
    m = LT.fullmatch(key)
    if m:
        return f"LT({m.group(1)}, {m.group(2)})"
    return key


def normalized(keymap):
    """全部のキーとエンコーダの書き方をそろえた写しを返す。"""
    return {
        **keymap,
        "layers": [
            {
                **layer,
                "keys": [[norm(k) for k in row] for row in layer["keys"]],
                "encoder": {d: norm(k) for d, k in layer["encoder"].items()},
            }
            for layer in keymap["layers"]
        ],
    }


def normalized_cond(cond):
    """条件に書かれたキーの書き方をそろえた写しを返す。"""
    out = dict(cond)
    if "keys" in out:
        out["keys"] = [norm(k) for k in out["keys"]]
    if "rows" in out and out["type"] in ("block", "no_block"):
        out["rows"] = [[norm(k) for k in row] for row in out["rows"]]
    for d in ("cw", "ccw"):
        if d in out:
            out[d] = norm(out[d])
    return out


def physical_col(r, c):
    """行と列(1 から)を、マトリクスの列(1 から)にする。4 行目は 6 番目より右が 1 つずれる。"""
    return c + 1 if r == 4 and c > 6 else c


def cells(keymap, layer, rows=None, cols=None):
    """(行, 列, キー) を返す。行と列は 1 から。押せない位置は除く。"""
    for r, row in enumerate(keymap["layers"][layer]["keys"], 1):
        if rows and r not in rows:
            continue
        for c, key in enumerate(row, 1):
            if (r, c) == UNPRESSABLE:
                continue
            if cols and not cols[0] <= c <= cols[1]:
                continue
            yield r, c, key


def key_at(keymap, layer, r, c):
    return keymap["layers"][layer]["keys"][r - 1][c - 1]


def switch_target(key):
    m = LAYER_FN.fullmatch(key) or LT.fullmatch(key)
    if not m:
        return None
    return int(m.group(2) if LAYER_FN.fullmatch(key) else m.group(1))


def reachable(keymap):
    """ベースから切り替えキーをたどって行けるレイヤー。"""
    seen, todo = {0}, [0]
    while todo:
        layer = todo.pop()
        for _, _, k in cells(keymap, layer):
            t = switch_target(k)
            if t is not None and t < len(keymap["layers"]) and t not in seen:
                seen.add(t)
                todo.append(t)
    return seen


def has_keys(keymap, layer, cond):
    found = {k for _, _, k in cells(keymap, layer, cond.get("rows"), cond.get("cols"))}
    return set(cond["keys"]) <= found


def block_at(grid, r0, c0, rows):
    return all(
        grid.get((r0 + dr, c0 + dc)) == key
        for dr, want in enumerate(rows)
        for dc, key in enumerate(want)
    )


def find_block(keymap, rows, layers):
    """rows の並びがそのまま(マトリクスの列でそろって)あるレイヤーを返す。"""
    for layer in layers:
        grid = {(r, physical_col(r, c)): k for r, c, k in cells(keymap, layer)}
        if any(block_at(grid, r, c, rows) for r, c in grid):
            return layer
    return None


def holds(cond, keymap, start, reach):
    """条件が成り立てば True。キーマップと条件は書き方をそろえてから渡す。reach は行けるレイヤー。"""
    t = cond["type"]
    candidates = [i for i in cond.get("layers", range(len(keymap["layers"]))) if i in reach]
    if t == "layer_with_keys":
        return any(has_keys(keymap, i, cond) for i in candidates)
    if t == "layer_with_switch":
        # キーがそろったレイヤーへの切り替えキーが、行けるレイヤーの決まった列にあること
        targets = {i for i in candidates if has_keys(keymap, i, cond)}
        switches = {
            switch_target(k) for i in reach for _, _, k in cells(keymap, i, cols=cond.get("switch_cols"))
        }
        return bool(targets & switches)
    if t == "each_key_somewhere":
        found = {k for i in candidates for _, _, k in cells(keymap, i, cond.get("rows"), cond.get("cols"))}
        return set(cond["keys"]) <= found
    if t == "block":
        return find_block(keymap, cond["rows"], candidates) is not None
    if t == "no_block":
        return find_block(keymap, cond["rows"], range(len(keymap["layers"]))) is None
    if t == "positions":
        return any([key_at(keymap, i, cond["row"], c) for c in cond["cols"]] == cond["keys"] for i in candidates)
    if t == "encoder":
        want = {"cw": cond["cw"], "ccw": cond["ccw"]}
        return any(keymap["layers"][i]["encoder"] == want for i in candidates if i not in cond.get("not_layers", []))
    if t == "encoder_unchanged":
        return keymap["layers"][cond["layer"]]["encoder"] == start["layers"][cond["layer"]]["encoder"]
    if t == "unchanged":
        layer = cond["layer"]
        if cond["what"] == "letters":
            where = [(r, c) for r, c, k in cells(start, layer) if LETTER.fullmatch(k)]
        else:
            where = [tuple(p) for p in cond["what"]]
        return all(key_at(keymap, layer, r, c) == key_at(start, layer, r, c) for r, c in where)
    if t == "keys_kept":
        found = {k for _, _, k in cells(keymap, cond["layer"])}
        return set(cond["keys"]) <= found
    if t == "absent":
        found = {k for i in range(len(keymap["layers"])) for _, _, k in cells(keymap, i)}
        return not set(cond["keys"]) & found
    if t == "no_more_no":
        def count(km):
            return sum(k == "No" for _, _, k in cells(km, cond["layer"], cols=cond["cols"]))
        return count(keymap) <= count(start)
    raise ValueError(f"知らない条件の種類: {t}")


def check(case_id, keymap, cases=None):
    """満たさなかった条件の説明の一覧を返す。空なら合格。"""
    cases = cases or load(CASES)
    case = cases["cases"][case_id]
    start = normalized(load(ROOT / cases["starts"][case["start"]]))
    keymap = normalized(keymap)
    reach = reachable(keymap)
    failed = []
    for cond in case["conditions"]:
        if not holds(normalized_cond(cond), keymap, start, reach):
            label = "必須を満たさない" if cond["kind"] == "must" else "してはいけない"
            failed.append(f"{label}: {cond['text']}")
    return failed


def evaluate(case_id, path, cases):
    """ファイルを読んで判定する。(結果, 理由の一覧) を返す。結果は 合格 / 不合格 / 読めない。"""
    try:
        keymap = load(path)
    except (OSError, ValueError) as e:
        return "読めない", [f"読み込めない: {e}"]
    errors = validate(keymap)
    if errors:
        return "読めない", [f"形式が正しくない: {e}" for e in errors]
    failed = check(case_id, keymap, cases)
    return ("不合格" if failed else "合格"), failed


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cases = load(CASES)
    if argv[1] not in cases["cases"]:
        print(f"評価例 {argv[1]} はスクリプトで判定できない(対象: {', '.join(cases['cases'])})", file=sys.stderr)
        return 2
    result, reasons = evaluate(argv[1], argv[2], cases)
    if result == "読めない":
        for r in reasons:
            print(f"{argv[2]}: {r}", file=sys.stderr)
        return 2
    for r in reasons:
        print(f"評価例 {argv[1]}: {r}")
    note = cases["cases"][argv[1]].get("note")
    if note:
        print(f"評価例 {argv[1]}: 注意: {note}")
    print(f"評価例 {argv[1]}: {result}(説明の項目は返答を読んで確かめる)")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
