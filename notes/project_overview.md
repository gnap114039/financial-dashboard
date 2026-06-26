---
name: project-overview
description: 退休資產追蹤 Dashboard 的專案背景與設計原則
metadata: 
  node_type: memory
  type: project
  originSessionId: a9d1c587-1187-451d-a1c5-146b1f9cf5b1
---

個人退休資產追蹤 Dashboard，監控資產配置與成長，作為退休規劃依據。

**Why:** 個人退休規劃用途，不是企業產品。
**How to apply:** 所有決策優先考慮簡單直覺，避免過度工程化。功能夠用即可，不需要企業級複雜度。

現在的架構（對照 CLAUDE.md）：
- 前端：單一 `src/index.html`，環境偵測自動切換資料來源
- 後端：FastAPI（Docker），負責抓 Google Sheets CSV + 每日快照
- 部署：GitHub Pages（靜態），本機用 Docker + Live Preview
- 資料來源：Google Sheets 公開 CSV（股票 / 銀行現金兩張工作表）

遷移自舊路徑 `/Users/gnap/Documents/financial` 的 session `0c8bdd05`。
