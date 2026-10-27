#!/usr/bin/env python3
"""評価例(docs/eval-cases.md)すべての結果を一覧にする。

使い方: python3 scripts/eval_report.py <フォルダ>
フォルダには、評価例ごとに Claude が作ったキーマップ JSON を「番号.json」(例: 1.json、M3.json)で置く。
キーの位置で判定できる評価例は scripts/check_eval.py と同じ判定をし、無いものは「未実行」と出す。
5、9、10 と「〜を説明する」の項目は、Claude の返答を読んで確かめる。
docs/plan.md の「その日の終わりに通る評価例」と比べるのに使う。不合格か未実行があれば終了コードは 1。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_eval import CASES, evaluate, load  # noqa: E402

RESULTS = ("合格", "不合格", "未実行", "返答を読む")


def order(case_id):
    """1〜10 を先に、M のつくものを後に、数の順に並べる。"""
    return (case_id.startswith("M"), int(case_id.lstrip("M")))


def case_ids(cases):
    by_script, by_reply = set(cases["cases"]), set(cases["by_reply"])
    if by_script & by_reply:
        raise ValueError(f"evals/cases.json で cases と by_reply の両方にある: {sorted(by_script & by_reply)}")
    return sorted(by_script | by_reply, key=order)


def report(folder, cases=None):
    """(番号, 結果, 理由と注意の一覧) を評価例の順に返す。結果は RESULTS のどれか。"""
    cases = cases or load(CASES)
    rows = []
    for cid in case_ids(cases):
        if cid in cases["by_reply"]:
            rows.append((cid, "返答を読む", []))
            continue
        path = Path(folder) / f"{cid}.json"
        if not path.is_file():
            rows.append((cid, "未実行", []))
            continue
        result, reasons = evaluate(cid, path, cases)
        case = cases["cases"][cid]
        if result != "合格" and case.get("note"):
            reasons = [*reasons, f"注意: {case['note']}"]
        if result == "合格" and case.get("explain"):
            reasons = ["必須の説明の項目は返答を読んで確かめる"]
        rows.append((cid, "合格" if result == "合格" else "不合格", reasons))
    return rows


def unknown_files(folder, cases):
    """評価例の番号になっていない .json ファイル(名前の間違いの見落とし防止)。"""
    names = {f"{cid}.json" for cid in cases["cases"]}
    return sorted(p.name for p in Path(folder).iterdir() if p.suffix.lower() == ".json" and p.name not in names)


def main(argv):
    if len(argv) != 2 or not Path(argv[1]).is_dir():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cases = load(CASES)
    rows = report(argv[1], cases)
    for cid, result, reasons in rows:
        print(f"{cid:>3}: {result}")
        for r in reasons:
            print(f"     {r}")
    for name in unknown_files(argv[1], cases):
        print(f"注意: {name} は評価例の番号ではないので読まなかった(名前は 1.json、M3.json のように付ける)")
    count = {k: sum(r == k for _, r, _ in rows) for k in RESULTS}
    print(f"全 {len(rows)} 件。キーの位置で判定: 合格 {count['合格']}、不合格 {count['不合格']}、未実行 {count['未実行']}。"
          f"返答だけで確かめるもの {count['返答を読む']} 件")
    return 1 if count["不合格"] or count["未実行"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
