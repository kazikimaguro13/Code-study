#!/usr/bin/env bash
# bridge dispatch helper for Code-study
#
# 使い方:
#   bash _ai_workspace/bridge/dispatch.sh <NUM> [<ALIAS_SUFFIX>]
#   例: bash _ai_workspace/bridge/dispatch.sh 001       # 既定 dev-b
#       bash _ai_workspace/bridge/dispatch.sh 001 a     # dev-a で実行
#
# alias 体系（~/.bashrc 想定）:
#   dev-a: CLAUDE_CONFIG_DIR=~/.claude-project-a
#   dev-b: CLAUDE_CONFIG_DIR=~/.claude-project-b  (Code-study 既定 / GitHub: kazikimaguro13)

set -euo pipefail

NUM="${1:?spec 番号を指定 (例: 001)}"
ALIAS_SUFFIX="${2:-b}"

case "${ALIAS_SUFFIX}" in
    a|b|c|d) ;;
    *) echo "ERROR: 不明な alias suffix: '${ALIAS_SUFFIX}' (a/b/c/d)" >&2; exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SPEC="_ai_workspace/bridge/inbox/spec_${NUM}.md"
RESULT="_ai_workspace/bridge/outbox/result_${NUM}.md"

if [ ! -f "${PROJECT_DIR}/${SPEC}" ]; then
    echo "ERROR: spec が見つかりません: ${PROJECT_DIR}/${SPEC}" >&2
    exit 1
fi

cd "${PROJECT_DIR}"
export CLAUDE_CONFIG_DIR="${HOME}/.claude-project-${ALIAS_SUFFIX}"

if [ ! -d "${CLAUDE_CONFIG_DIR}" ]; then
    echo "WARNING: ${CLAUDE_CONFIG_DIR} が無い。認証未設定の可能性。" >&2
fi

echo "[dispatch] spec=${SPEC} alias=dev-${ALIAS_SUFFIX} project=${PROJECT_DIR}"

claude --dangerously-skip-permissions -p \
  "${SPEC} を読んで実行して。完了後は同階層 ${RESULT} に _ai_workspace/bridge/templates/result_template.md の構造で結果を書いて。git push する場合は dev-${ALIAS_SUFFIX} アカウント (GitHub: kazikimaguro13) で origin に push して。" \
  < /dev/null
