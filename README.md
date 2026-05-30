# 退休資產追蹤 Dashboard

個人退休財務追蹤工具，監控資產配置與成長，預測退休計劃進度。

## 功能

- **總覽**：總資產、退休進度、預估退休年齡、投資報酬
- **銀行現金**：多銀行、多幣別三層展開
- **股票 / ETF**：四種視圖切換（清單 / 配置 / 比較 / 圓餅）
- **退休預測**：可編輯目標金額、月投入、通膨假設、預估報酬率
- **多幣別切換**：TWD / USD / EUR / JPY 等，即時匯率換算

## 技術架構

| 層 | 技術 |
|---|---|
| 前端 | 靜態 HTML + CSS + JavaScript（無框架） |
| 後端 | FastAPI + Docker（本機限定） |
| 資料來源 | Google Sheets 公開 CSV |
| 股價 | Finnhub API（即時）+ 手動備援 |
| 圖表 | Chart.js（CDN） |
| 部署 | GitHub Actions → GitHub Pages |

## 本機開發

### 前置需求

- Docker Desktop
- VS Code（建議搭配 Live Preview 擴充功能）

### 啟動

```bash
# 第一次或修改 api/main.py 後
docker compose up --build

# 一般啟動
docker compose up
```

啟動後用 VS Code Live Preview 開啟 `src/index.html`，或直接以瀏覽器開啟。

後端 API 運行於 `http://localhost:8000`，前端會自動偵測 localhost 並切換至 FastAPI 模式（支援每日快照）。

### 停止

```bash
docker compose down
```

## 資料格式

資料來源為 Google Sheets，需公開發布為 CSV：

**股票工作表**

| 欄位 | 說明 |
|---|---|
| `Ticker` | 股票代號，`CASH` 為券商現金 |
| `Total Share` | 持股數，`0` = 已清倉 |
| `Average` | 每股均價（USD） |
| `Total Price` | 持倉成本（USD），負值代表已實現獲利 |
| `Current Price` | 手動填入現價；填 `-` 則由 Finnhub 自動取得 |

**銀行現金工作表**

欄位：`Bank, NTD, USD, EUR, JPY, MYR, CNY`（幣別欄位動態偵測）

## 部署（GitHub Pages）

Push 到 `main` 分支後 GitHub Actions 自動部署。頁面有密碼保護（SHA-256 hash 驗證）。

若需更換密碼，在瀏覽器 console 執行：

```javascript
crypto.subtle.digest('SHA-256', new TextEncoder().encode('新密碼'))
  .then(b => console.log([...new Uint8Array(b)].map(x => x.toString(16).padStart(2,'0')).join('')))
```

將輸出的 hash 替換 `src/index.html` 中的 `PASSWORD_HASH`。
