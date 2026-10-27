# built-with-claude

[Built with Claude: Japan 2026](https://cerebralvalley.ai/e/built-with-claude-japan2026)(2026-11-02 〜 11-10、オンライン)に参加するためのリポジトリです。

## 作るもの

**自作キーボードのキー配置や動作を、日本語で話しかけるだけで設定できるツール**

「左手だけで Photoshop のショートカットを使いたい」のように話しかけると、Claude がキーマップを作って説明し、キーボードへの書き込みまで案内します。

自作キーボードの魅力は、自分の手や仕事に合わせて変えられることです。ただ、キー配置や動作を変えるにはファームウェアのコードを書き、ビルドして書き込む必要があり、多くの人がそこで止まってしまいます。デザイナーやイラストレーターなど、コードを書かない作り手こそ、道具を自分に合わせられるようにしたいと考えています。

最初の対象は、作者がデザインしているワイヤレス 40% キーボード「dotmatrix40W」です。

構想の詳細は [docs/project.md](docs/project.md) にあります。

## 現在の状況

- 2026-10: 題材を決め、開発ループの仕組みを用意しました(このリポジトリ)
- 2026-11-02 〜 11-10: ハッカソン期間中に本体を実装します

## 作り方: Claude Code が自走する開発ループ

開発そのものは Claude Code に任せています。始めは人が「何を作るかの採用」と「マージ」の2点を決めていましたが、2026-10-27 からは Claude が採用からマージまで進め、作者は結果を受け取るだけです。人が関わるのは、取り返しのつかない操作の確認と、実機での確認だけです。仕事をしながらでも、一週間で動くものを作り切るための仕組みです。

1. **提案**: 毎朝、Claude が半日以内で終わる大きさの課題を最大3件提案し、GitHub Issue(ラベル `proposal`)にします
2. **採用**: Claude が課題を採用し、`approved` ラベルを付けます(10-26 までは、作者がスマホで「採用 / 却下」を選んでいました)
3. **実装**: Claude がブランチを切り、ドラフト PR を作ります
4. **AI レビュー**: Claude が `/code-review` で自己レビューして直し、CI がグリーンになるまで回します
5. **マージ**: CI がグリーンで AI レビュー欄が埋まったら、Claude がマージし、結果を作者に短く報告します

詳細は [docs/loop.md](docs/loop.md) にあります。

## 関連する作品

- [everyday-knobs(まいにちのぶ)](https://y-morishita-biz.github.io/everyday-knobs/): ロータリーエンコーダ用のツマミをブラウザで設計し、STL / STEP で書き出せるジェネレーター。Claude Code と30日以上、1日1機能ずつ育てました
- [dotting dots](https://dotting-dots.stores.jp/): 作者がデザインを担当しているキーボードとデスクトップガジェットのショップ

## English summary

A tool that lets anyone customize their keyboard's keymap just by describing what they want in plain Japanese. Claude proposes a keymap, explains what changed, and guides the user through writing it to the keyboard, starting with the dotmatrix40W wireless keyboard.
Development runs on a loop where Claude Code proposes, implements and self-reviews every task, and, since 2026-10-27, also adopts tasks and merges them once CI is green. The human only confirms irreversible operations and checks the result on the real keyboard.

## リポジトリの構成

| パス | 内容 |
|---|---|
| [docs/project.md](docs/project.md) | 作るものの構想(課題、使う人、最初の範囲) |
| [docs/keymap-format.md](docs/keymap-format.md) | Claude が読み書きするキーマップの形式 |
| [docs/vil-format.md](docs/vil-format.md) | Vial のレイアウトファイル(.vil)の形式と、キー名の対応表 |
| [examples/](examples/) | キーマップのサンプル(実機の keyboard.toml から生成したものと、普段使いの Vial 配列から読み込んだもの) |
| [evals/](evals/) | 評価例のうち、キーの位置で判定できる条件(`scripts/check_eval.py` が読む) |
| [data/](data/) | RMK のキー名一覧など、検証に使うデータ |
| [docs/eval-cases.md](docs/eval-cases.md) | 日本語の依頼とキーマップ変更の評価例 |
| [docs/decisions/](docs/decisions/) | 設計の判断記録 |
| [skill-trial/](skill-trial/) | claude.ai のプロジェクトで試す Skill の手順書。`scripts/build_skill.sh` でスクリプトとデータを合わせた zip にする |
| [docs/plan.md](docs/plan.md) | 開催期間 9 日間の作業計画 |
| [docs/loop.md](docs/loop.md) | 開発ループの詳細 |
| [docs/ideas.md](docs/ideas.md) | 提案の前提とアイデアメモ |
| [CLAUDE.md](CLAUDE.md) | Claude Code 向けの作業ルール |
| [.github/](.github/) | Issue / PR テンプレート、CI |
| [scripts/check.sh](scripts/check.sh) | CI とローカルで共通のチェック |

## ライセンス

[MIT License](LICENSE)
