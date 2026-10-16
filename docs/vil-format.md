# Vial のレイアウトファイル(.vil)

キーマップ JSON(version 2)を Vial で読み込める `.vil` に変換するための調べものです。変換スクリプトは開催期間中に作ります。ここに書いた内容は、次のソースを読んで確かめました(2026-10-17)。

- Vial の GUI: [vial-kb/vial-gui](https://github.com/vial-kb/vial-gui) の `protocol/keyboard_comm.py`(`save_layout` / `restore_layout`)と `keycodes/`(コミット `aef8222`)。Web 版 Vial も同じ Python コードから作られています
- 実機ファーム: [dotmatrix40W-RMK-Firmware](https://github.com/y-morishita-biz/dotmatrix40W-RMK-Firmware) の `vial.json`、`build.rs`、`vendor/rmk-0.8.2/src/host/via/keycode_convert.rs` と `vial.rs`
- RMK のキー名と番号: rmk-types 0.2.2 の `keycode.rs`

## ファイルの中身

`.vil` は1つの JSON です。Vial が保存するときは次のキーを書きます。

| キー | 中身 | dotmatrix40W での値 |
|---|---|---|
| `version` | 形式の版 | `1` |
| `uid` | キーボード ID(8 バイトをリトルエンディアンで読んだ整数) | `72128238669483254` |
| `layout` | `[レイヤー][行][列]` のキー | 5 × 4 × 12 |
| `encoder_layout` | `[レイヤー][エンコーダ]` ごとに `[反時計回り, 時計回り]` | 5 × 1 × 2 |
| `layout_options` | レイアウトの選択肢 | `-1`(選択肢なし) |
| `macro` | マクロ | 変換では書かない(下の注意を参照) |
| `tap_dance`、`combo`、`key_override`、`alt_repeat_key` | 各機能の設定 | 変換では空のリスト `[]` |
| `settings` | QMK 設定 | 変換では `{}` |
| `vial_protocol`、`via_protocol` | 保存したときの通信の版 | `6`、`9` |

- `uid` は `build.rs` の `VIAL_KEYBOARD_ID`(`F6 4C 2B 3C 40 40 00 01`)から計算した値です。違っていても読み込みは止まらず、「別のキーボードの保存データです」という確認が出ます
- 読み込み時に必須なのは `layout`、`encoder_layout`、`layout_options` の3つです。ほかは無くても読み込めます
- `macro` は、キーが無ければ今のマクロをそのまま残します。空のリスト `[]` を入れると全マクロが空で上書きされ、ロック解除を求められることがあります。キーマップの変換では `macro` を書きません
- `tap_dance`、`combo` などは、リストにある分だけを上書きします。空のリストなら今の設定が残ります
- `layout` は、キーボードが持つ位置だけが書き込まれます。キーがない (3,6) の値は無視されるので、Vial と同じく `-1` を入れます
- `encoder_layout` は位置を確かめずに書き込まれます。数が合わないと読み込みが途中で止まる(キーマップだけ書き込まれ、残りが反映されない)ので、必ず 5 × 1 × 2 にします
- キーは文字列(`"KC_A"`)でも 16 ビットの整数でも読み込めます。Vial が保存するのは文字列です
- Vial が知らない文字列は、エラーにならず `KC_NO`(何もしないキー)として読み込まれます。変換では下の表にある文字列だけを使い、表に無いキーは変換を止めます

## 気をつける点

- **エンコーダの順番。** `encoder_layout` の各組は `[反時計回り, 時計回り]` の順です。vial-gui の保存処理は変数名が `cw` / `ccw` で逆に見えますが、実際の中身はファームから受け取った順(反時計回りが先)で、RMK の `vial.rs` も反時計回りを先に返します。キーマップ JSON の `encoder` は `cw` / `ccw` の名前付きなので、変換で入れ替えを間違えないようにします
- **4 行目の列のずれ。** キーマップ JSON の 4 行目は 11 キーですが、`.vil` の 4 行目は 12 列です。JSON の 1〜6 番目を列 0〜5 に、7〜11 番目を列 7〜11 に入れ、列 6 は `-1` にします([keymap-format.md](keymap-format.md) と同じ対応)。そのまま詰めると、6 番目より右のキーが1つずつずれます
- **押せない位置。** 4 行目 6 番目(matrix (3,5))は `vial.json` に含まれていて、`.vil` でも普通のキーとして書き込まれます。押せないだけなので、値はそのまま残します
- **キーの文字列は Vial の書き方に合わせる。** 通信の版が 6 のとき、Vial は `KC_BSPACE`、`KC_LCTRL`、`KC_LANG1` のような古い名前を使います。下の表の文字列をそのまま使います
- **レイヤー番号。** `MO`、`TG`、`TO`、`OSL` は 0〜15、`LT` は 0〜15 のレイヤーまで表せます。dotmatrix40W は 5 レイヤー(0〜4)なので問題ありません

## RMK のキー名との対応

サンプル [examples/dotmatrix40w-rmk-default.json](../examples/dotmatrix40w-rmk-default.json) に出てくる全キーと、`User0`〜`User8` の対応です。サンプルのキーがこの表から漏れていないかは `scripts/check.sh` が確かめます。16 ビット値は RMK の `to_via_keycode` の規則で計算し、文字列は Vial(通信の版 6)が同じ値を表示するときの名前です。

規則をまとめると次のとおりです。

- ふつうのキー: RMK の番号がそのまま 16 ビット値になる(例: `A` = `0x0004`)
- `WM(キー, 修飾)`: 修飾のビット(`LCtrl` = 1、`LShift` = 2、`LAlt` = 4、`LGui` = 8、右側は 0x10 を足す)を 8 ビット左に寄せて足す。Vial では `LCTL(KC_Z)` のように書き、2つ以上の組み合わせは `C_S(KC_Z)` のような短い名前になる
- `SHIFTED(キー)`: `WM(キー, LShift)` と同じ(`LSFT(KC_1)`)
- `MO(n)` = `0x5220 + n`、`TG(n)` = `0x5260 + n`、`TO(n)` = `0x5200 + n`、`OSL(n)` = `0x5280 + n`
- `LT(n, キー)` = `0x4000 + n × 0x100 + キー`(`LT2(KC_RIGHT)`)
- `User0`〜`User8` = `0x7E00`〜`0x7E08`(`USER00`〜`USER08`)。Vial の画面では `vial.json` の `customKeycodes` のラベル(BT1 など)で表示される
- `BacklightUp` / `BacklightDown` = `0x7804` / `0x7803`(`BL_INC` / `BL_DEC`)

### 文字・数字・記号

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `A` | `KC_A` | `0x0004` |
| `B` | `KC_B` | `0x0005` |
| `Backspace` | `KC_BSPACE` | `0x002A` |
| `C` | `KC_C` | `0x0006` |
| `Comma` | `KC_COMMA` | `0x0036` |
| `D` | `KC_D` | `0x0007` |
| `Delete` | `KC_DELETE` | `0x004C` |
| `Dot` | `KC_DOT` | `0x0037` |
| `Enter` | `KC_ENTER` | `0x0028` |
| `Escape` | `KC_ESCAPE` | `0x0029` |
| `F` | `KC_F` | `0x0009` |
| `G` | `KC_G` | `0x000A` |
| `Grave` | `KC_GRAVE` | `0x0035` |
| `H` | `KC_H` | `0x000B` |
| `J` | `KC_J` | `0x000D` |
| `K` | `KC_K` | `0x000E` |
| `Kc0` | `KC_0` | `0x0027` |
| `Kc1` | `KC_1` | `0x001E` |
| `Kc2` | `KC_2` | `0x001F` |
| `Kc3` | `KC_3` | `0x0020` |
| `Kc4` | `KC_4` | `0x0021` |
| `Kc5` | `KC_5` | `0x0022` |
| `Kc6` | `KC_6` | `0x0023` |
| `Kc7` | `KC_7` | `0x0024` |
| `Kc8` | `KC_8` | `0x0025` |
| `Kc9` | `KC_9` | `0x0026` |
| `L` | `KC_L` | `0x000F` |
| `LeftBracket` | `KC_LBRACKET` | `0x002F` |
| `M` | `KC_M` | `0x0010` |
| `Minus` | `KC_MINUS` | `0x002D` |
| `N` | `KC_N` | `0x0011` |
| `RightBracket` | `KC_RBRACKET` | `0x0030` |
| `S` | `KC_S` | `0x0016` |
| `Slash` | `KC_SLASH` | `0x0038` |
| `Space` | `KC_SPACE` | `0x002C` |
| `V` | `KC_V` | `0x0019` |
| `X` | `KC_X` | `0x001B` |
| `Z` | `KC_Z` | `0x001D` |

### ファンクション

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `F1` | `KC_F1` | `0x003A` |
| `F10` | `KC_F10` | `0x0043` |
| `F11` | `KC_F11` | `0x0044` |
| `F12` | `KC_F12` | `0x0045` |
| `F2` | `KC_F2` | `0x003B` |
| `F3` | `KC_F3` | `0x003C` |
| `F4` | `KC_F4` | `0x003D` |
| `F5` | `KC_F5` | `0x003E` |
| `F6` | `KC_F6` | `0x003F` |
| `F7` | `KC_F7` | `0x0040` |
| `F8` | `KC_F8` | `0x0041` |
| `F9` | `KC_F9` | `0x0042` |

### カーソル・ページ

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `Down` | `KC_DOWN` | `0x0051` |
| `End` | `KC_END` | `0x004D` |
| `Home` | `KC_HOME` | `0x004A` |
| `Left` | `KC_LEFT` | `0x0050` |
| `PageDown` | `KC_PGDOWN` | `0x004E` |
| `PageUp` | `KC_PGUP` | `0x004B` |
| `Up` | `KC_UP` | `0x0052` |

### 修飾キー

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `LAlt` | `KC_LALT` | `0x00E2` |
| `LCtrl` | `KC_LCTRL` | `0x00E0` |
| `LGui` | `KC_LGUI` | `0x00E3` |
| `LShift` | `KC_LSHIFT` | `0x00E1` |

### 日本語入力

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `International1` | `KC_RO` | `0x0087` |
| `Language1` | `KC_LANG1` | `0x0090` |
| `Language2` | `KC_LANG2` | `0x0091` |

### テンキー

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `Kp0` | `KC_KP_0` | `0x0062` |
| `Kp4` | `KC_KP_4` | `0x005C` |
| `Kp5` | `KC_KP_5` | `0x005D` |
| `Kp6` | `KC_KP_6` | `0x005E` |
| `Kp7` | `KC_KP_7` | `0x005F` |
| `Kp8` | `KC_KP_8` | `0x0060` |
| `Kp9` | `KC_KP_9` | `0x0061` |
| `KpDot` | `KC_KP_DOT` | `0x0063` |
| `KpPlus` | `KC_KP_PLUS` | `0x0057` |

### メディア・音量

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `AudioMute` | `KC_MUTE` | `0x00A8` |
| `AudioVolDown` | `KC_VOLD` | `0x00AA` |
| `AudioVolUp` | `KC_VOLU` | `0x00A9` |
| `MediaNextTrack` | `KC_MNXT` | `0x00AB` |
| `MediaPlayPause` | `KC_MPLY` | `0x00AE` |
| `MediaPrevTrack` | `KC_MPRV` | `0x00AC` |

### マウス

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `MouseDown` | `KC_MS_D` | `0x00CE` |
| `MouseLeft` | `KC_MS_L` | `0x00CF` |
| `MouseRight` | `KC_MS_R` | `0x00D0` |
| `MouseUp` | `KC_MS_U` | `0x00CD` |

### バックライト

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `BacklightDown` | `BL_DEC` | `0x7803` |
| `BacklightUp` | `BL_INC` | `0x7804` |

### レイヤー

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `LT(2, Right)` | `LT2(KC_RIGHT)` | `0x424F` |
| `MO(1)` | `MO(1)` | `0x5221` |
| `MO(2)` | `MO(2)` | `0x5222` |
| `TG(1)` | `TG(1)` | `0x5261` |
| `TG(2)` | `TG(2)` | `0x5262` |

### 修飾つき(WM / SHIFTED)

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `SHIFTED(Equal)` | `LSFT(KC_EQUAL)` | `0x022E` |
| `SHIFTED(Kc0)` | `LSFT(KC_0)` | `0x0227` |
| `SHIFTED(Kc1)` | `LSFT(KC_1)` | `0x021E` |
| `SHIFTED(Kc2)` | `LSFT(KC_2)` | `0x021F` |
| `SHIFTED(Kc3)` | `LSFT(KC_3)` | `0x0220` |
| `SHIFTED(Kc4)` | `LSFT(KC_4)` | `0x0221` |
| `SHIFTED(Kc5)` | `LSFT(KC_5)` | `0x0222` |
| `SHIFTED(Kc6)` | `LSFT(KC_6)` | `0x0223` |
| `SHIFTED(Kc7)` | `LSFT(KC_7)` | `0x0224` |
| `SHIFTED(Kc8)` | `LSFT(KC_8)` | `0x0225` |
| `SHIFTED(Kc9)` | `LSFT(KC_9)` | `0x0226` |
| `SHIFTED(Minus)` | `LSFT(KC_MINUS)` | `0x022D` |
| `WM(C, LCtrl)` | `LCTL(KC_C)` | `0x0106` |
| `WM(Down, LCtrl)` | `LCTL(KC_DOWN)` | `0x0151` |
| `WM(Left, LCtrl)` | `LCTL(KC_LEFT)` | `0x0150` |
| `WM(Right, LCtrl)` | `LCTL(KC_RIGHT)` | `0x014F` |
| `WM(Up, LCtrl)` | `LCTL(KC_UP)` | `0x0152` |
| `WM(V, LCtrl)` | `LCTL(KC_V)` | `0x0119` |
| `WM(X, LCtrl)` | `LCTL(KC_X)` | `0x011B` |
| `WM(Z, LCtrl \| LShift)` | `C_S(KC_Z)` | `0x031D` |
| `WM(Z, LCtrl)` | `LCTL(KC_Z)` | `0x011D` |

### User(BLE 操作など)

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `User0` | `USER00` | `0x7E00` |
| `User1` | `USER01` | `0x7E01` |
| `User2` | `USER02` | `0x7E02` |
| `User3` | `USER03` | `0x7E03` |
| `User4` | `USER04` | `0x7E04` |
| `User5` | `USER05` | `0x7E05` |
| `User6` | `USER06` | `0x7E06` |
| `User7` | `USER07` | `0x7E07` |
| `User8` | `USER08` | `0x7E08` |

### 特別

| RMK | `.vil` | 16 ビット値 |
|---|---|---|
| `No` | `KC_NO` | `0x0000` |
| `_` | `KC_TRNS` | `0x0001` |

## 実機で確かめること(開催期間中)

- Claude が作った `.vil` を USB で読み込み、全レイヤーのキーとエンコーダが意図どおりになるか
- `uid` が一致していれば確認が出ないか
- エンコーダの `[反時計回り, 時計回り]` の順が、実際の回転方向と合っているか(ファームの未確認項目「encoder 実回転方向」とあわせて確かめる)
- `macro` を書かずに読み込んだとき、今のマクロが残るか
- BLE 接続のまま Web 版 Vial で読み込めるか
