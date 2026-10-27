#!/usr/bin/env python3
"""scripts/eval_report.py のテスト。答えの例を一時フォルダに置いて一覧にする。"""
import contextlib
import copy
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_eval import CASES, ROOT, load  # noqa: E402
import re  # noqa: E402

from eval_report import case_ids, main as report_main, report, unknown_files  # noqa: E402
from test_check_eval import answers  # noqa: E402

results = []


def ok(name, cond):
    results.append((name, bool(cond)))


def run_main(folder):
    """一覧の表示は捨て、終了コードだけを返す。"""
    with contextlib.redirect_stdout(io.StringIO()):
        return report_main(["", folder])


def write(folder, name, data):
    (Path(folder) / name).write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def main():
    cases = load(CASES)
    starts = {name: load(ROOT / path) for name, path in cases["starts"].items()}
    good = answers(starts)
    with tempfile.TemporaryDirectory() as d:
        rows = report(d, cases)
        ids = [cid for cid, _, _ in rows]
        ok("14 件を順に並べる", ids == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "M3", "M6", "M7", "M8"])
        doc = (ROOT / "docs" / "eval-cases.md").read_text(encoding="utf-8")
        ok("docs/eval-cases.md の見出しと同じ評価例", ids == sorted(re.findall(r"^#{2,3} (M?[0-9]+)\. ", doc, re.MULTILINE), key=lambda c: (c.startswith("M"), int(c.lstrip("M")))))
        ok("空のフォルダは終了コード 1", run_main(d) == 1)
        ok("空のフォルダは未実行と返答を読むだけ", {r for _, r, _ in rows} == {"未実行", "返答を読む"})
        ok("5、9、10 は返答を読む", [cid for cid, r, _ in rows if r == "返答を読む"] == ["5", "9", "10"])

        for cid, km in good.items():
            write(d, f"{cid}.json", km)
        rows = report(d, cases)
        ok("答えの例はすべて合格", all(r == "合格" for cid, r, _ in rows if cid not in cases["by_reply"]))
        ok("すべて合格なら終了コード 0", run_main(d) == 0)
        reasons = {cid: rs for cid, _, rs in rows}
        ok("必須の説明がある評価例は、合格でも返答を読むよう書く", reasons["1"] and not reasons["2"])
        write(d, "m3.json", good["M3"])
        ok("番号でない名前のファイルを知らせる", unknown_files(d, cases) == ["m3.json"])
        (Path(d) / "m3.json").unlink()
        both = copy.deepcopy(cases)
        both["by_reply"].append("7")
        try:
            case_ids(both)
            ok("cases と by_reply の重なりで止まる", False)
        except ValueError:
            ok("cases と by_reply の重なりで止まる", True)

        write(d, "3.json", starts["default"])
        write(d, "4.json", "{ 壊れた JSON")
        bad = copy.deepcopy(good["M3"])
        bad["layers"].pop()
        write(d, "M3.json", bad)
        result = {cid: (r, reasons) for cid, r, reasons in report(d, cases)}
        ok("出発点のままは不合格で理由が出る", result["3"][0] == "不合格" and result["3"][1])
        ok("読めない JSON は不合格", result["4"][0] == "不合格" and "読み込めない" in result["4"][1][0])
        ok("形式の違う JSON は不合格", result["M3"][0] == "不合格" and "形式" in result["M3"][1][0])
        ok("ほかの評価例はそのまま合格", result["1"][0] == "合格")
        write(d, "7.json", starts["default"])
        ok("不合格には評価例の注意も添える", any(r.startswith("注意") for r in report(d, cases)[6][2]))

    failed = [name for name, cond in results if not cond]
    for name in failed:
        print(f"test_eval_report: 失敗: {name}")
    if not failed:
        print(f"test_eval_report: {len(results)} 件 ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
