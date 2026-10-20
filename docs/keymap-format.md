# キーマップ形式

Claude が dotmatrix40W のキーマップを読み、変更し、書き出すための共通の形式です。キーの書き方は実機のファームウェア [dotmatrix40W-RMK-Firmware](https://github.com/y-morishita-biz/dotmatrix40W-RMK-Firmware) の `keyboard.toml`(RMK)にそろえてあり、そのまま `keyboard.toml` や Vial の `.vil` に変換できるようにしています。

サンプル:

- [examples/dotmatrix40w-rmk-default.json](../examples/dotmatrix40w-rmk-default.json): 実機の `keyboard.toml` から `scripts/from_keyboard_toml.py` で作ったもの(ファームの初期配列)
- [examples/dotmatrix40w-mac.json](../examples/dotmatrix40w-mac.json): メンテナーが普段使っている Vial の配列 [examples/dotmatrix40w-mac.vil](../examples/dotmatrix40w-mac.vil) から `scripts/from_vil.py` で作ったもの(QWERTY、Mac 向け)

## 全体

```json
{
  "keyboard": "dotmatrix40w",
  "version": 2,
  "layers": [
    {
      "name": "base",
      "keys": [["Escape", "Kc1", "..."], ["..."], ["..."], ["..."]],
      "encoder": { "cw": "AudioVolUp", "ccw": "AudioVolDown" }
    }
  ]
}
```

| 項目 | 内容 |
|---|---|
| `keyboard` | 対象キーボード。今は `dotmatrix40w` のみ |
| `version` | この形式の版。今は `2` |
| `layers` | 5 個のレイヤー。実機と同じく base / fn / media / user1 / user2 の順 |
| `layers[].name` | レイヤー名。英小文字、数字、ハイフン(先頭は英字)。重複不可 |
| `layers[].keys` | 4 行のキー。上の行から、各行は左から |
| `layers[].encoder` | ロータリーエンコーダの時計回り `cw` と反時計回り `ccw`。全レイヤーで必須 |

## キーの位置

dotmatrix40W は 47 キーです。上 3 行は 12 キー、最下段は 11 キーです。最下段ではマトリクス位置 (3,6) が使われていません(実機の `keyboard.toml` の `matrix_map` のとおり)。

| 行 | キー数 | マトリクス上の列 |
|---|---|---|
| 1〜3 行目 | 12 | 0〜11 |
| 4 行目 | 11 | 0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11 |

4 行目の 6 番目(マトリクス (3,5))はエンコーダの下に重なる予備のスイッチ位置で、エンコーダを付けた標準構成では押せません。

## キーの書き方

RMK の `keyboard.toml` と同じ書き方です。

| 書き方 | 意味 | 例 |
|---|---|---|
| キー名 | そのキーを送る | `A`, `Kc1`, `Enter`, `F5`, `Language2`(英数), `Language1`(かな) |
| `WM(キー, 修飾キー)` | 修飾キーと同時に送る。修飾キーは `\|` でつなぐ | `WM(Z, LCtrl)`, `WM(Z, LCtrl \| LShift)` |
| `SHIFTED(キー)` | Shift と同時に送る | `SHIFTED(Kc1)`(!) |
| `MO(n)` | 押している間だけレイヤー n | `MO(1)` |
| `TG(n)` / `TO(n)` | レイヤー n を切り替え / 移動 | `TG(2)` |
| `OSL(n)` | 次の 1 キーだけレイヤー n | `OSL(3)` |
| `LT(n, キー)` | 長押しでレイヤー n、短く押すとキー | `LT(2, Right)` |
| `_` | 下のレイヤーの設定をそのまま使う。ベースレイヤーでは使えない | |
| `No` | 何もしない | |

- キー名は RMK の `KeyCode` の名前です。一覧は [data/rmk-keycodes.txt](../data/rmk-keycodes.txt)(rmk-types 0.2.2 から抜き出したもの)
- 修飾キーは `LCtrl` `LShift` `LAlt` `LGui` `RCtrl` `RShift` `RAlt` `RGui` です(Mac の Command は `LGui`)
- `keyboard.toml` の `@copy` のような別名は、展開した形(`WM(C, LCtrl)`)で書きます
- エンコーダにはレイヤー切り替えを割り当てられません

## 検証と変換

```sh
python3 scripts/validate_keymap.py examples/*.json
python3 scripts/from_keyboard_toml.py path/to/keyboard.toml > out.json
python3 scripts/from_vil.py path/to/layout.vil > out.json
```

検証では、レイヤー数、各行のキー数、キー名、修飾キーの重複、レイヤー番号の範囲、レイヤー名を確認します。`scripts/check.sh` からも呼ばれます。
