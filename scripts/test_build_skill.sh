#!/usr/bin/env bash
# scripts/build_skill.sh で作った zip を、リポジトリの外のフォルダで展開して動かせるか確かめる。
# claude.ai に合わせ、Skill のフォルダは読み取り専用にし、出力は別のフォルダに書き、別のフォルダから実行する。
# 変換の中身の正しさは scripts/test_from_vil.py で確かめているので、ここでは動くことと検証を通ることだけを見る。
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'chmod -R u+w "$tmp"; rm -rf "$tmp"' EXIT
zip="$("$root/scripts/build_skill.sh" "$tmp/build" | tail -1)"
mkdir "$tmp/skills" "$tmp/uploads" "$tmp/outputs" "$tmp/cwd"
python3 -m zipfile -e "$zip" "$tmp/skills"
skill="$tmp/skills/dotmatrix40w-vil-trial"
test -f "$skill/SKILL.md" || { echo "test_build_skill: zip に SKILL.md が無い"; exit 1; }
grep -q '^name: dotmatrix40w-vil-trial$' "$skill/SKILL.md" || { echo "test_build_skill: SKILL.md の name が違う"; exit 1; }
chmod -R a-w "$skill"
# 添付されたファイルに見立てて、.vil を uploads に置く。SKILL.md の手順 3、4 と同じコマンドを動かす
cp "$root/examples/dotmatrix40w-mac.vil" "$tmp/uploads/attached.vil"
SKILL_DIR="$skill" OUT="$tmp/outputs"
(cd "$tmp/cwd" \
  && python3 -I "$SKILL_DIR/scripts/from_vil.py" "$tmp/uploads/attached.vil" > "$OUT/keymap.json.tmp" 2> "$tmp/notes.txt" \
  && mv "$OUT/keymap.json.tmp" "$OUT/keymap.json" \
  && python3 -I "$SKILL_DIR/scripts/validate_keymap.py" "$OUT/keymap.json") \
  || { echo "test_build_skill: Skill の中でスクリプトが動かない"; cat "$tmp/notes.txt"; exit 1; }
# 壊れた .vil では keymap.json が作られない
echo '{}' > "$tmp/uploads/broken.vil"
rm "$OUT/keymap.json"
if python3 -I "$SKILL_DIR/scripts/from_vil.py" "$tmp/uploads/broken.vil" > "$OUT/keymap.json.tmp" 2> /dev/null \
  && mv "$OUT/keymap.json.tmp" "$OUT/keymap.json"; then
  echo "test_build_skill: 壊れた .vil で止まらない"; exit 1
fi
test ! -e "$OUT/keymap.json" || { echo "test_build_skill: 失敗しても keymap.json ができる"; exit 1; }
echo "test_build_skill: ok"
