# CLAUDE.md — 開發狀態與架構說明

## 專案簡介

個人退休資產追蹤 Dashboard，詳細需求見 [SPEC.md](SPEC.md)。

---

## 技術架構

```
瀏覽器（Live Preview / GitHub Pages）
  ├── src/index.html        → 唯一前端頁面
  └── http://localhost:8000 → FastAPI（本機限定）

FastAPI（Docker）
  ├── 從 Google Sheets 抓取 CSV 資料
  ├── 存每日快照到 src/data/
  └── 回傳資料給前端
```

### 環境偵測

`index.html` 透過 `window.location.hostname` 判斷環境：

- `localhost` / `127.0.0.1` → 走 FastAPI（`localhost:8000`），支援快照
- 其他（GitHub Pages）→ 直接 fetch Google Sheets 公開 CSV

---

## 資料夾結構

```
financial_dashboard/
├── CLAUDE.md
├── SPEC.md
├── .gitignore
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── deploy.yml        → GitHub Pages 自動部署
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py               → FastAPI endpoints
└── src/
    ├── index.html             → 前端主頁面
    ├── bank_cash.csv          → 已棄用（改用 Google Sheets）
    └── data/                  → 每日快照（已加入 .gitignore，不納入版控）
        ├── bank/              → bank_YYYY-MM-DD.csv
        └── stock/             → stock_YYYY-MM-DD.csv
```

---

## 啟動方式

### 後端（FastAPI）

```bash
docker compose up --build   # 第一次或 main.py 有修改
docker compose up           # 一般啟動
docker compose down         # 停止
```

### 前端

VS Code Live Preview 開啟 `src/index.html`，或直接用瀏覽器開啟。

---

## Google Sheets 資料來源

| 資料 | 工作表 gid |
|---|---|
| 股票 | `gid=756201628` |
| 銀行現金 | `gid=983098033` |

完整 URL 在 `api/main.py` 的 `STOCK_SHEET_URL` / `BANK_SHEET_URL`，以及 `src/index.html` 的 `STOCK_SHEET_URL` / `BANK_SHEET_URL`。

---

## API Endpoints

| Method | Path | 說明 |
|---|---|---|
| GET | `/api/stock/refresh` | 回傳股票 CSV，今日快照存在則用快照 |
| GET | `/api/stock/refresh?force=true` | 強制重新抓取 Google Sheets |
| GET | `/api/stock/history` | 列出所有股票快照檔名 |
| PATCH | `/api/stock/snapshot` | 將 Finnhub 即時股價回寫今日快照（僅更新 `-` 的列） |
| GET | `/api/bank/refresh` | 回傳銀行 CSV，今日快照存在則用快照 |
| GET | `/api/bank/refresh?force=true` | 強制重新抓取 Google Sheets |
| GET | `/api/bank/history` | 列出所有銀行快照檔名 |

Response header `X-Data-Source: cache | fresh` 標示資料來源。

---

## 股票資料欄位說明

| 欄位 | 說明 |
|---|---|
| `Ticker` | 股票代號，`CASH` 為券商現金 |
| `Total Share` | 持股數，0 = 已清倉 |
| `Average` | 每股均價（USD） |
| `Total Price` | 持倉成本（USD），負值代表已實現獲利 |
| `Current Price` | 手動填入的現價（USD），`-` 表示由 Finnhub 自動取得 |

---

## 已完成功能

- [x] 總覽卡片（總資產、退休進度、預估退休年齡、投資報酬）
- [x] 多幣別切換（動態偵測 CSV 幣別欄位）
- [x] 銀行現金 Accordion（三層：總覽 → 各銀行 → 幣別）
- [x] 股票 Accordion（持倉中 / 券商現金 / 已清倉）
- [x] Finnhub 即時股價 + 手動填價格備援（`Current Price` 欄位）
- [x] Finnhub 抓到的股價自動回寫今日快照（本機限定，不覆蓋手動填價）
- [x] 退休預測明細（可編輯四個參數）
- [x] 投資報酬明細（利息、資本利得、總收益）
- [x] Google Sheets 資料來源
- [x] FastAPI 每日快照機制
- [x] 本機 / GitHub Pages 環境自動切換
- [x] GitHub Pages 密碼保護（SHA-256 hash 驗證，sessionStorage 記住登入狀態）
- [x] GitHub Actions 自動部署至 GitHub Pages

## 待開發

- [ ] 每月花費統計分頁
- [ ] 資產成長趨勢圖（利用每日快照資料）
