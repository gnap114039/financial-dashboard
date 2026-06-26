#!/bin/bash
# 將 src/data 下的每日快照 commit + push 到備份 repo。
set -euo pipefail

cd "$(dirname "$0")/src/data"

git add -A

# 沒有變更就乾淨退出，不視為錯誤
if git diff --cached --quiet; then
  echo "沒有新的快照需要備份"
  exit 0
fi

git commit -m "backup: $(date '+%Y-%m-%d')"
git push
echo "備份完成"
