#!/usr/bin/env python3
"""scripts/check_pr.py の check() を、GitHub に問い合わせずに確かめる。"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_pr import check  # noqa: E402

ISSUES = {
    15: {"labels": ["approved"], "is_pr": False, "open": True},
    16: {"labels": ["proposal"], "is_pr": False, "open": True},
    17: {"labels": ["approved"], "is_pr": False, "open": True},
    18: {"labels": [], "is_pr": True, "open": True},
    19: {"labels": ["approved", "rejected"], "is_pr": False, "open": True},
    20: {"labels": ["approved"], "is_pr": False, "open": False},
}

FULL = "- [x] /code-review 済み\n- [x] scripts/check.sh グリーン"


def get_issue(n):
    return ISSUES.get(n)


def body(closes="Closes #15", review=FULL):
    return f"{closes}\n\n## Before\n前\n\n## After\n後\n\n## AIレビュー\n{review}\n\n🤖 Generated"


# (名前, 本文, ドラフトか, 出るはずのエラーに含まれる文字列のリスト)
CASES = [
    ("ルールどおりの Ready PR", body(), False, []),
    ("ドラフトなら未チェックでもよい", body(review="- [ ] /code-review 済み"), True, []),
    ("Closes がない", body(closes=""), True, ["Closes #番号"]),
    ("コメントの中の Closes は数えない", body(closes="<!-- Closes #15 -->"), True, ["Closes #番号"]),
    ("インラインコードの中は数えない", body(closes="本文に `Closes #15` を書く"), True, ["Closes #番号"]),
    ("コードブロックの中は数えない", body(closes="```\nCloses #15\n```"), True, ["Closes #番号"]),
    ("採用前の Issue", body(closes="Closes #16"), True, ["approved ラベルがありません"]),
    ("存在しない Issue", body(closes="Closes #99"), True, ["見つかりません"]),
    ("PR を指している", body(closes="Closes #18"), True, ["PR です"]),
    ("却下された Issue", body(closes="Closes #19"), True, ["却下"]),
    ("閉じた Issue", body(closes="Closes #20"), True, ["閉じています"]),
    ("複数の Issue", body(closes="Closes #15\nCloses #17"), True, ["複数の Issue"]),
    ("Ready なのに未チェック", body(review="- [ ] /code-review 済み\n- [x] scripts/check.sh グリーン"), False, ["未チェック"]),
    ("+ の箇条書きも見る", body(review="+ [ ] /code-review 済み\n+ [x] scripts/check.sh グリーン"), False, ["未チェック"]),
    ("番号付きも見る", body(review="1. [x] /code-review 済み\n2. [ ] scripts/check.sh グリーン"), False, ["未チェック"]),
    ("Ready なのに項目が空", body(review=""), False, ["/code-review", "scripts/check.sh"]),
    ("AIレビュー欄がない", "Closes #15\n\n## Before\n前", True, ["AIレビュー」欄がありません"]),
    ("fixes も使える", body(closes="fixes #15"), False, []),
    ("コロン付きも使える", body(closes="Closes: #15"), False, []),
    ("日本語の直後でも使える", body(closes="対応Closes #15"), False, []),
    ("本文が空", None, True, ["Closes #番号", "AIレビュー」欄がありません"]),
]

failed = 0
for name, b, draft, expected in CASES:
    errors = check(b, draft, get_issue)
    ok = len(errors) == len(expected) and all(any(e in err for err in errors) for e in expected)
    if not ok:
        failed += 1
        print(f"FAIL {name}: 期待 {expected}、実際 {errors}")
if failed:
    sys.exit(1)
print(f"test_check_pr: {len(CASES)} 件 ok")
