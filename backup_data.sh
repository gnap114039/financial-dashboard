#!/bin/bash
# 同步 src/data 與備份 repo：先拉下 GitHub Actions 每日排程存的快照，再把本機快照 commit + push。
set -euo pipefail

cd "$(dirname "$0")/src/data"

git fetch --quiet origin

# 同一天兩邊都有快照時以遠端（Actions）為準：移除本機未追蹤的同名檔，避免 pull 被擋
git diff --name-only --diff-filter=A HEAD origin/main | while read -r f; do
  if [ -e "$f" ] && [ -z "$(git ls-files -- "$f")" ]; then
    echo "以遠端版本為準，移除本機重複快照：$f"
    rm -- "$f"
  fi
done

git add -A
if ! git diff --cached --quiet; then
  git commit --quiet -m "backup: $(date '+%Y-%m-%d')"
fi

git pull --rebase --quiet origin main

# 沒有本機新快照就乾淨退出，不視為錯誤
if [ "$(git rev-list --count origin/main..HEAD)" -eq 0 ]; then
  echo "已同步遠端快照，沒有新的本機快照需要備份"
  exit 0
fi

git push --quiet origin main
echo "備份完成"
