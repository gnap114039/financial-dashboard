#!/bin/bash
cd "$(dirname "$0")/src/data"
git add .
git commit -m "backup: $(date '+%Y-%m-%d')" 2>/dev/null || echo "nothing to commit"
git push
