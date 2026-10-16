#!/usr/bin/env python3
"""PR が CLAUDE.md のルールどおりかを確かめる(CI の pr-rules ジョブ用)。

- 本文に `Closes #番号` があり、その Issue に `approved` ラベルが付いている
- その Issue が開いていて、`rejected` ラベルが付いていない
- 1つの PR が閉じる Issue は1つだけ(1 Issue = 1 PR)
- Ready の PR は、本文の「AIレビュー」欄の必須項目がすべてチェックされている

使い方: python3 scripts/check_pr.py <GitHub のイベント JSON>
Issue のラベルは GitHub API で調べる(環境変数 GITHUB_TOKEN と GITHUB_REPOSITORY)。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

CLOSES = re.compile(r"(?<![A-Za-z])(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?[ \t]+#(\d+)(?!\d)", re.IGNORECASE)
# GitHub が Issue に紐づけないところ(HTML コメント、コードブロック、インラインコード)
IGNORED = re.compile(r"<!--.*?-->|^[ \t]*```.*?^[ \t]*```|`[^`\n]*`", re.DOTALL | re.MULTILINE)
REVIEW_HEADING = re.compile(r"^##[ \t]*AIレビュー[ \t]*$", re.MULTILINE)
TASK = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+\[([ xX])\][ \t]*(.*)$", re.MULTILINE)
# AIレビュー欄で必ずチェックが要る項目(PR テンプレートと同じ)
REQUIRED_ITEMS = ["/code-review", "scripts/check.sh"]


def review_section(body):
    m = REVIEW_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = re.search(r"^#{1,2}\s", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def check(body, draft, get_issue):
    """ルール違反の理由を日本語で返す(違反がなければ空のリスト)。

    get_issue(番号) は {"labels": [...], "is_pr": bool, "open": bool} か、見つからなければ None を返す。
    """
    errors = []
    body = IGNORED.sub("", body or "")
    numbers = sorted({int(n) for n in CLOSES.findall(body)})
    if not numbers:
        errors.append("PR 本文に `Closes #番号` がありません。採用済みの Issue を1つ書いてください。")
    elif len(numbers) > 1:
        refs = "、".join(f"#{n}" for n in numbers)
        errors.append(f"1つの PR で複数の Issue({refs})を閉じようとしています。1 Issue = 1 PR にしてください。")
    for n in numbers:
        issue = get_issue(n)
        if issue is None:
            errors.append(f"#{n} が見つかりません。")
        elif issue["is_pr"]:
            errors.append(f"#{n} は Issue ではなく PR です。")
        elif "approved" not in issue["labels"]:
            errors.append(f"#{n} に approved ラベルがありません。採用前の Issue は実装しません。")
        elif "rejected" in issue["labels"]:
            errors.append(f"#{n} は却下(rejected)されています。")
        elif not issue["open"]:
            errors.append(f"#{n} はすでに閉じています。")
    section = review_section(body)
    if section is None:
        errors.append("PR 本文に「## AIレビュー」欄がありません。")
    elif not draft:
        tasks = TASK.findall(section)
        for mark, item in tasks:
            if mark == " ":
                errors.append(f"Ready の PR なのに、AIレビュー欄が未チェックです: {item.strip()}")
        for required in REQUIRED_ITEMS:
            if not any(required in item for _, item in tasks):
                errors.append(f"AIレビュー欄に「{required}」の項目がありません。")
    return errors


class ApiError(Exception):
    """ルール違反ではなく、GitHub API に問い合わせられなかったとき。"""


def github_issue_getter(repo, token):
    def get_issue(n):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/issues/{n}",
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.load(res)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
            raise ApiError(f"#{n} を GitHub API で調べられませんでした(HTTP {e.code})。") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise ApiError(f"#{n} を GitHub API で調べられませんでした({e})。") from e
        return {
            "labels": [label["name"] for label in data.get("labels", [])],
            "is_pr": "pull_request" in data,
            "open": data.get("state") == "open",
        }

    return get_issue


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        pr = json.load(f)["pull_request"]
    get_issue = github_issue_getter(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    try:
        errors = check(pr.get("body"), pr.get("draft", False), get_issue)
    except ApiError as e:
        print(f"::error::{e} ルール違反ではありません。しばらくしてから Actions の画面で再実行してください。")
        return 1
    for e in errors:
        print(f"::error::{e}")
    if not errors:
        print("pr-rules: ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
