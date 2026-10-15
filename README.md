# built-with-claude

Built with Claude: Japan 2026 用のリポジトリです。
人間は「アイデアの承認」と「マージの承認」だけを行い、それ以外は Claude が回す開発ループで運用します。

## 開発ループ

1. **提案**: 毎朝、Claude が課題を最大3件提案し、GitHub Issue（ラベル `proposal`）を作って判断カードで知らせます。
2. **承認**: 陽介さんがスマホで「採用／却下」を選びます。採用された Issue には `approved` ラベルが付きます。
3. **実装**: Claude がブランチを切り、ドラフトPRを作ります。
4. **AIレビュー**: Claude が `/code-review` で自己レビューして修正し、CI がグリーンになるまで回します。
5. **マージ**: 陽介さんがマージ可否を判断します。

詳細は [docs/loop.md](docs/loop.md) を参照してください。
