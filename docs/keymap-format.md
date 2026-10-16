# キーマップ形式

Claude が dotmatrix40W のキーマップを読み、変更し、書き出すための共通の形式です。ファームウェア(ZMK / RMK)に依存しない中立な JSON にしておき、書き込み時に各ファームウェアの形式へ変換します。

サンプル: [examples/dotmatrix40w-default.json](../examples/dotmatrix40w-default.json)

## 全体

```json
{
  "keyboard": "dotmatrix40w",
  "version": 1,
  "rows": 4,
  "cols": 12,
  "layers": [
    {
      "name": "base",
      "keys": [["TAB", "Q", "..."], ["..."], ["..."], ["..."]],
      "encoder": { "cw": "VOLU", "ccw": "VOLD" }
    }
  ]
}
```

| 項目 | 内容 |
|---|---|
| `keyboard` | 対象キーボード。今は `dotmatrix40w` のみ |
| `version` | この形式の版。今は `1` |
| `rows` / `cols` | 行数と列数。dotmatrix40W は 4 × 12 で固定 |
| `layers` | レイヤーの配列。先頭がベースレイヤー(番号 0) |
| `layers[].name` | レイヤー名。英小文字、数字、ハイフン(先頭は英字)。重複不可 |
| `layers[].keys` | `rows` 行 × `cols` 列のキーの二次元配列。上の行から、各行は左から |
| `layers[].encoder` | ロータリーエンコーダの時計回り `cw` と反時計回り `ccw`。全レイヤーで必須。下のレイヤーと同じにするなら `TRANS`。レイヤー切り替えは割り当てられない |

## キーの書き方

各キーは文字列で書きます。

| 書き方 | 意味 | 例 |
|---|---|---|
| キー名 | そのキーを送る | `A`, `1`, `ENTER`, `F5` |
| 修飾キー + キー | 同時押しを送る | `LCTRL+Z`, `LCTRL+LSHIFT+S` |
| `MO(n)` | 押している間だけレイヤー n | `MO(1)` |
| `TG(n)` | 押すたびにレイヤー n を切り替え | `TG(2)` |
| `TRANS` | 下のレイヤーの設定をそのまま使う。ベースレイヤーでは使えない | |
| `NONE` | 何もしない | |

使えるキー名と修飾キーは [scripts/validate_keymap.py](../scripts/validate_keymap.py) の一覧が正です。
修飾キーは `LCTRL` `LSHIFT` `LALT` `LGUI` `RCTRL` `RSHIFT` `RALT` `RGUI` です(Mac の Command は `LGUI`)。

## 検証

```sh
python3 scripts/validate_keymap.py examples/*.json
```

行数と列数、キー名、修飾キーの重複、レイヤー番号の範囲、レイヤー名を確認します。`scripts/check.sh` からも呼ばれます。
