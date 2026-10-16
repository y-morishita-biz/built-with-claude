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

## 作り方: 人間の判断を2点に絞った開発ループ

開発そのものは Claude Code に任せ、人間が判断するのは「何を作るかの採用」と「マージ」の2点だけです。仕事をしながらでも、一週間で動くものを作り切るための仕組みです。

1. **提案**: 毎朝、Claude が半日以内で終わる大きさの課題を最大3件提案し、GitHub Issue(ラベル `proposal`)にします
2. **採用**: 作者がスマホで「採用 / 却下」を選びます。採用された Issue には `approved` ラベルが付きます
3. **実装**: Claude がブランチを切り、ドラフト PR を作ります
4. **AI レビュー**: Claude が `/code-review` で自己レビューして直し、CI がグリーンになるまで回します
5. **マージ**: 作者がマージするかどうかを決めます

詳細は [docs/loop.md](docs/loop.md) にあります。

## 関連する作品

- [everyday-knobs(まいにちのぶ)](https://y-morishita-biz.github.io/everyday-knobs/): ロータリーエンコーダ用のツマミをブラウザで設計し、STL / STEP で書き出せるジェネレーター。Claude Code と30日以上、1日1機能ずつ育てました
- [dotting dots](https://dotting-dots.stores.jp/): 作者がデザインを担当しているキーボードとデスクトップガジェットのショップ

## English summary

A tool that lets anyone customize their keyboard's keymap just by describing what they want in plain Japanese. Claude proposes a keymap, explains what changed, and guides the user through writing it to the keyboard, starting with the dotmatrix40W wireless keyboard.
Development runs on a loop where Claude Code proposes, implements and self-reviews every task, and the human only approves tasks and merges.

## リポジトリの構成

| パス | 内容 |
|---|---|
| [docs/project.md](docs/project.md) | 作るものの構想(課題、使う人、最初の範囲) |
| [docs/keymap-format.md](docs/keymap-format.md) | Claude が読み書きするキーマップの形式 |
| [examples/](examples/) | キーマップのサンプル |
| [docs/decisions/](docs/decisions/) | 設計の判断記録 |
| [docs/loop.md](docs/loop.md) | 開発ループの詳細 |
| [docs/ideas.md](docs/ideas.md) | 提案の前提とアイデアメモ |
| [CLAUDE.md](CLAUDE.md) | Claude Code 向けの作業ルール |
| [.github/](.github/) | Issue / PR テンプレート、CI |
| [scripts/check.sh](scripts/check.sh) | CI とローカルで共通のチェック |

## ライセンス

[MIT License](LICENSE)
