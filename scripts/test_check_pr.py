#!/usr/bin/env python3
"""scripts/check_pr.py の check() を、GitHub に問い合わせずに確かめる。"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_pr import check  # noqa: E402

ISSUES = {
    15: {"labels": ["approved"], "is_pr": False},
    16: {"labels": ["proposal"], "is_pr": False},
    18: {"labels": [], "is_pr": True},
}


def get_issue(n):
    return ISSUES.get(n)


def body(closes="Closes #15", review="- [x] /code-review 済み\n- [x] scripts/check.sh グリーン"):
    return f"{closes}\n\n## Before\n前\n\n## After\n後\n\n## AIレビュー\n{review}\n\n🤖 Generated"


CASES = [
    ("ルールどおりの Ready PR", body(), False, 0),
    ("ドラフトなら未チェックでもよい", body(review="- [ ] /code-review 済み"), True, 0),
    ("Closes がない", body(closes=""), True, 1),
    ("コメントの中の Closes は数えない", body(closes="<!-- Closes #15 -->"), True, 1),
    ("採用前の Issue", body(closes="Closes #16"), True, 1),
    ("存在しない Issue", body(closes="Closes #99"), True, 1),
    ("PR を指している", body(closes="Closes #18"), True, 1),
    ("Ready なのに未チェック", body(review="- [ ] /code-review 済み\n- [x] scripts/check.sh グリーン"), False, 1),
    ("AIレビュー欄がない", "Closes #15\n\n## Before\n前", True, 1),
    ("fixes も使える", body(closes="fixes #15"), False, 0),
    ("本文が空", None, True, 2),
]

failed = 0
for name, b, draft, expected in CASES:
    errors = check(b, draft, get_issue)
    if len(errors) != expected:
        failed += 1
        print(f"FAIL {name}: 期待 {expected} 件、実際 {len(errors)} 件 {errors}")
if failed:
    sys.exit(1)
print(f"test_check_pr: {len(CASES)} 件 ok")
