#!/usr/bin/env bash
# claude.ai に入れる Skill のフォルダと zip を作る。
# 使い方: scripts/build_skill.sh [出力先のフォルダ](省略すると build/)
# 出力: <出力先>/dotmatrix40w-vil-trial/ と <出力先>/dotmatrix40w-vil-trial.zip
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$(mkdir -p "${1:-$root/build}" && cd "${1:-$root/build}" && pwd)"
name=dotmatrix40w-vil-trial
dir="$out/$name"
# 前に作ったものだけを消す。同じ名前の別のフォルダがあれば止まる
if [ -e "$dir" ] && ! grep -q "^name: $name\$" "$dir/SKILL.md" 2>/dev/null; then
  echo "build_skill: $dir は前に作った Skill ではないので消さない" >&2
  exit 1
fi
rm -rf "$dir" "$out/$name.zip"
mkdir -p "$dir/scripts" "$dir/data" "$dir/docs"
# スクリプトは 1 つ上のフォルダの data/ と docs/ を読むので、同じ並びで写す
cp "$root/skill-trial/SKILL.md" "$dir/"
cp "$root/scripts/from_vil.py" "$root/scripts/validate_keymap.py" "$dir/scripts/"
cp "$root/data/rmk-keycodes.txt" "$dir/data/"
cp "$root/docs/vil-format.md" "$dir/docs/"
cp "$root/LICENSE" "$dir/"
(cd "$out" && python3 -m zipfile -c "$name.zip" "$name")
echo "$out/$name.zip"
