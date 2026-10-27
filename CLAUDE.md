# Claude 向け作業ルール

- ユーザーとのやり取りは日本語。返信は短く、質問は選択式にする。
- 2026-10-27 から自走モード。課題の採用からマージまで自分で判断して進め、結果だけを短く報告する。人に確認するのは、取り返しのつかない操作(秘密情報、リポジトリの公開設定、外部への送信など)と、実機が要る作業だけ。
- 課題は GitHub Issue で管理する。ラベル: `proposal`(提案中)、`approved`(採用)、`rejected`(却下)。自走モードでは、採用する課題に自分で `approved` を付ける。
- 実装は `approved` の Issue だけ。1 Issue = 1 ブランチ = 1 PR。PR本文に `Closes #番号` を書く。
- PR は必ずドラフトで作り、`/code-review` で自己レビューして指摘を直し、`scripts/check.sh` と CI がグリーンになってから Ready にする。
- main への直接 push はしない。マージは、`scripts/check.sh` と CI(`PR rules` を含む)がグリーンの Ready の PR だけを squash で行う。
- 1件の提案は「半日以内で終わる大きさ」に分割する。
- 課題はハッカソンの趣旨(docs/ideas.md の「提案の前提」)と、作るものの構想(docs/project.md)に沿ったものだけを出す。
- このリポジトリは Public。秘密情報、APIキー、個人情報は絶対にコミットしない。

## 参照するリポジトリ

- [y-morishita-biz/dotmatrix40W-RMK-Firmware](https://github.com/y-morishita-biz/dotmatrix40W-RMK-Firmware): dotmatrix40W で実際に動いている RMK + Vial ファームウェア。キー配置(`keyboard.toml`)、レイヤー構成、Vial の検証結果(`docs/verification.md`)の正はここ
- [dotting-dots/dotmatrix40W-technical-documents](https://github.com/dotting-dots/dotmatrix40W-technical-documents): 回路図、基板図、BOM、筐体データ。物理的なキー位置やエンコーダの位置の正はここ
- このリポジトリの文書と食い違ったら、上の2つを正として直す提案を出す
