#!/usr/bin/env bash
# CI とローカルで共通のチェック。コードが増えたらテストやリンターをここに足す。
set -euo pipefail
test -f README.md
test -f CLAUDE.md
echo "check: ok"
