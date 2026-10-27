---
name: dotmatrix40w-vil-trial
description: dotmatrix40W の Vial レイアウトファイル(.vil)が添付されたときに使う試験用の Skill。.vil をキーマップ JSON に変換して検証し、JSON をダウンロードできるファイルとして返す。
---

# dotmatrix40W の .vil を読む(試験用)

Claude のプロジェクトで、この Skill の中の Python スクリプトが動くかを確かめるための試験用です。キーマップを変える依頼には応えず、読み込みと検証だけを行います。

## 手順

以下で `SKILL_DIR` はこの `SKILL.md` があるフォルダの絶対パス、`OUT` は書き込めてダウンロードに使えるフォルダ(claude.ai では普通 `/mnt/user-data/outputs`)です。Skill のフォルダは読み取り専用のことがあるので、ファイルは `OUT` にだけ書きます。

1. 添付された `.vil` の絶対パスを確かめる(claude.ai では普通 `/mnt/user-data/uploads/` の下)。添付が無ければ、Vial で保存した `.vil` を添付してほしいと伝えて終える
2. Python が動くかと、そのバージョンを確かめる

   ```bash
   python3 --version
   ```

3. 次を実行する。変換に失敗したら `keymap.json` は作られない

   ```bash
   python3 "$SKILL_DIR/scripts/from_vil.py" "<添付された .vil>" > "$OUT/keymap.json.tmp" \
     && mv "$OUT/keymap.json.tmp" "$OUT/keymap.json"
   ```

   標準エラーに出た知らせ(読まなかった設定、uid の違い)は、そのまま使う人に伝える。止まった場合は `$OUT/keymap.json.tmp` を消し、エラーの文をそのまま伝えて終える
4. 次を実行して検証する。何も出ず終了コードが 0 なら合格

   ```bash
   python3 "$SKILL_DIR/scripts/validate_keymap.py" "$OUT/keymap.json"
   ```

5. 返答に次をまとめる
   - スクリプトが動いたか(手順 2 で出た Python のバージョンも書く)
   - 検証の結果
   - 5 つのレイヤーそれぞれの、1 行目のキー
6. `$OUT/keymap.json` を、使う人がダウンロードできるファイルとして返す

## 注意

- スクリプトとデータ(`data/rmk-keycodes.txt`、`docs/vil-format.md`)は書き換えない
- スクリプトが動かなかったときは、表を見て自分で変換せず、動かなかったことと理由を伝える(試したいのはスクリプトが動くかどうか)
