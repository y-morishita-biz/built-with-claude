#!/usr/bin/env python3
"""PR が CLAUDE.md のルールどおりかを確かめる(CI の pr-rules ジョブ用)。

- 本文に `Closes #番号` があり、その Issue に `approved` ラベルが付いている
- Ready の PR は、本文の「AIレビュー」欄のチェックがすべて埋まっている

使い方: python3 scripts/check_pr.py <GitHub のイベント JSON>
Issue のラベルは GitHub API で調べる(環境変数 GITHUB_TOKEN と GITHUB_REPOSITORY)。
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

CLOSES = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b", re.IGNORECASE)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
REVIEW_HEADING = re.compile(r"^##\s*AIレビュー\s*$", re.MULTILINE)
UNCHECKED = re.compile(r"^\s*[-*]\s+\[ \]\s*(.*)$", re.MULTILINE)


def review_section(body):
    m = REVIEW_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = re.search(r"^#{1,2}\s", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def check(body, draft, get_issue):
    """ルール違反の理由を日本語で返す(違反がなければ空のリスト)。

    get_issue(番号) は {"labels": [...], "is_pr": bool} か、見つからなければ None を返す。
    """
    errors = []
    body = COMMENT.sub("", body or "")
    numbers = sorted({int(n) for n in CLOSES.findall(body)})
    if not numbers:
        errors.append("PR 本文に `Closes #番号` がありません。採用済みの Issue を1つ書いてください。")
    for n in numbers:
        issue = get_issue(n)
        if issue is None:
            errors.append(f"#{n} が見つかりません。")
        elif issue["is_pr"]:
            errors.append(f"#{n} は Issue ではなく PR です。")
        elif "approved" not in issue["labels"]:
            errors.append(f"#{n} に approved ラベルがありません。採用前の Issue は実装しません。")
    section = review_section(body)
    if section is None:
        errors.append("PR 本文に「## AIレビュー」欄がありません。")
    elif not draft:
        for item in UNCHECKED.findall(section):
            errors.append(f"Ready の PR なのに、AIレビュー欄が未チェックです: {item.strip()}")
    return errors


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
            raise
        return {"labels": [label["name"] for label in data.get("labels", [])], "is_pr": "pull_request" in data}

    return get_issue


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        pr = json.load(f)["pull_request"]
    get_issue = github_issue_getter(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    errors = check(pr.get("body"), pr.get("draft", False), get_issue)
    for e in errors:
        print(f"::error::{e}")
    if not errors:
        print("pr-rules: ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
