---
name: feedback-commit-checklist
description: 每次 commit 前必須先確認並同步 CLAUDE.md 和 SPEC.md
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9d1c587-1187-451d-a1c5-146b1f9cf5b1
---

每次 commit 前，先確認 CLAUDE.md 和 SPEC.md 的內容是否反映目前的開發進度。若有落差，先更新文件再 commit。

**Why:** 使用者希望文件隨時與程式碼同步，避免文件落後於實作。

**How to apply:** commit 前主動 check 兩份文件的「已完成功能」和版本紀錄，有缺漏就補上後一起納入同一個 commit。
