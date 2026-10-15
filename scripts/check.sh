#!/usr/bin/env bash
# CI とローカルで共通のチェック。コードが増えたらテストやリンターをここに足す。
set -euo pipefail
for f in README.md CLAUDE.md docs/project.md docs/loop.md docs/ideas.md; do
  test -f "$f" || { echo "missing: $f"; exit 1; }
done
# Markdown 内の相対リンク先が存在するか確認する
status=0
while IFS= read -r md; do
  dir=$(dirname "$md")
  while IFS= read -r link; do
    link=${link%% \"*}
    test -e "$dir/$link" || { echo "broken link in $md: $link"; status=1; }
  done < <(grep -oE '\]\([^)#:]+\)' "$md" | sed -E 's/^\]\((.*)\)$/\1/' || true)
done < <(git ls-files '*.md')
[ "$status" -eq 0 ] && echo "check: ok"
exit $status
