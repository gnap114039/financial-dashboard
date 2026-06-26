# 優化待辦清單

> 來源：2026-06-24 全專案唯讀分析（多代理掃描，所有行號已對照原始碼驗證）。
> 此檔僅記錄，尚未動工。完成的項目請打勾並註明 commit。

---

## 建議順序：先止血 → 再去重 → 後架構

1. 暖身（極低工本）
2. 止血兩個高危坑（CSV parser + 匯率外顯）— 決定「總資產」可不可信
3. 統一顯示層（formatter + renderAll）
4. 退休模型對齊通膨慣例
5. 後端體質與安全認知

---

## 一、極低工本暖身（零風險、立刻見效） ✅ 全數完成（commit 9483679）

- [x] **README 補 Currency + PRINCIPAL 欄位** — `README.md`，與 CLAUDE.md/SPEC.md 對齊
- [x] **`:focus-visible` 焦點環取代 `outline:none`** — `src/index.html`，恢復鍵盤可用性
- [x] **`usdToTWD` 除法前 assert > 0** — `src/index.html`，缺匯率時短路成錯誤狀態
- [x] **股票 tab 改用 `data-view` 屬性**（不再比對中文 label） — `src/index.html`
- [x] **Pin Chart.js CDN 版本（+SRI）** — `src/index.html`，鎖 4.4.6 + integrity
- [x] **加 `prefers-reduced-motion` guard** — `src/index.html`
- [x] **回寫快照結果改成顯示而非吞掉**（log `{updated}` / 失敗警告） — `src/index.html`
- [x] **後端時區改 `Asia/Taipei`** — `api/main.py` zoneinfo + tzdata、compose `TZ`、前端 `localDate()`
- [x] **Pin 後端依賴 + 移除 Dockerfile `--reload`** — `api/requirements.txt`, `api/Dockerfile`
- [x] **強化 `backup_data.sh`（fail loudly）** — `set -euo pipefail`、空 commit 乾淨退出

## 二、低工本、高影響（本輪核心）

- [x] **匯率失敗外顯（取代靜默 1:1）** — `src/index.html`（commit 4e7ddb9）。`toDisplay` 缺匯率回 NaN → `fmtD` 顯示「匯率不可用」；下拉只列有匯率的幣別、與 bank render 解耦；`renderOverview` 自癒退回 TWD。經 13-agent 對抗式審查（2 問題已修）
- [x] **集中 `renderAll()`，切幣別整頁重繪** — `src/index.html`（commit fc31795）。重繪 overview+投報+三 accordion+當前股票視圖；股票用 stockViewData 重繪不重打 Finnhub；onConfigChange 維持輕量
- [ ] **Finnhub 報價平行化（+ AbortController timeout）** — `src/index.html:1238-1274`。N×RTT → ~1×RTT，單檔卡死不再拖垮整個手風琴
- [ ] **統一三 fetcher 為單一 `fetchFeed()`** — `src/index.html:550-595`，收掉 ~45 行重複
- [ ] **600 月迴圈改 annuity 閉式解** — `src/index.html:744-751`，O(1) 精確、自然處理「無法達標」
- [ ] **無股票資料時投報卡仍給合理狀態 + 輸入驗證** — `src/index.html:788-789, 662-665`
- [ ] **NTD/TWD 統一成單一幣別碼** — `src/index.html:680, 690-691, 831, 887`
- [ ] **wire `force=true`（手動重抓按鈕）** — `api/main.py` + `src/index.html:553` 等，讓當日 Sheets 更正值可見
- [ ] **後端三 refresh/history 抽工廠 + config 化（DOC_ID/TZ/DATA_DIR 走 env）** — `api/main.py:20-72` 等，砍 ~90 行複製貼上、修掉 `/app/data` 硬編

## 三、中工本（資料正確性根治）

- [x] **三 feed 共用引號 + 數字感知 parser（全走 `parseAmount`）** — `src/index.html`（commit 4e7ddb9）。新增 `splitCSVLine` + `parseCSV`，銀行/勞退改走它 + `parseAmount`，修掉千分位金額腐蝕（問題 #1）。16 項單元測試通過
- [x] **三套 formatter 統一成幣別感知 `fmtD`** — `src/index.html`（commit fc31795）。主數字全改 fmtD；fmtUSD 保留 USD-native；fmt 僅留明確 TWD 標注的參考列。經 12-agent 對抗式審查（0 真問題）
- [ ] **退休模型統一一套通膨慣例** — `src/index.html:739-751, 757`。建議全程實質：實質報酬、實質目標、月投入也折現，讓進度條/目標卡/退休年齡量同一個目標
- [ ] **抓回內容做 CSV 健檢，失敗則回退上一份快照** — `api/main.py:43-67`。防 Google HTML 錯誤頁毒化整天 cache
- [ ] **手風琴/tab 升級為語意元素（button/role/aria）** — `src/index.html:422, 445-451, 908`
- [ ] **CSS 變數化色盤 + 合併重複 row 樣式** — `src/index.html:8-336`，消除 ~12 個散落 hex、砍 ~40 行重複
- [ ] **PATCH 區分 auto vs manual，讓 Finnhub 盤中可刷新** — `api/main.py:91`
- [ ] **加最小 pytest（TestClient）** — `api/main.py`，鎖住 cache/fresh、PATCH、404、history 契約
- [ ] **獨立 Realized P&L 欄位（改資料模型）** — `src/index.html:1294-1299`，讓平倉會計正確可稽核

## 四、架構級（僅建議，後續里程碑）

- [ ] **Finnhub key + 真實存取控制搬到後端** — `src/index.html:514, 521`。唯一能讓密碼閘有意義、key 不外洩的根治法

---

## 附錄：已知問題與風險（依嚴重度）

| # | 嚴重度 | 問題 | 位置 |
|---|---|---|---|
| 1 | **High** | 銀行/勞退 CSV parser 不處理引號逗號，數字未走 `parseAmount`，`"1,234"`→`1`、`$1234`→NaN→0，金額被低估且無告警 | `src/index.html:597-607, 853-862, 885, 623-624` |
| 2 | **High** | 退休年齡迴圈混用通膨慣例：餘額用實質報酬、月投入用名目；目標卡用名目、年齡迴圈用實質。進度條與「可提早退休 ✓」可能矛盾 | `src/index.html:739-751, 757` |
| 3 | Medium | 密碼閘純屬裝飾：PASSWORD_HASH、Sheets URL、明文 Finnhub key 全隨 `src/` 上公開 Pages | `src/index.html:514, 521, 545-548` |
| 4 | Medium | 已清倉 realized P&L 由 `-Total Price` 反推，虧損/歸零列顯示成 0、隱藏真實平倉 | `src/index.html:1294-1299` |
| 5 | Medium | 匯率失敗靜默 1:1，外幣資產被當 1:1 計入總資產卻無提示 | `src/index.html:695, 830-844, 1357` |
| 6 | Medium | `usdToTWD` 除法未防 0，`/0 = Infinity` 污染 grandTotal | `src/index.html:1226, 1242, 1249, 1310` |
| 7 | Medium | Finnhub 逐檔序列化 await，無 timeout，一檔卡死整個手風琴 | `src/index.html:1238-1274` |
| 8 | Medium | 混幣顯示：切 USD 時手風琴/勞退/銀行/股票視圖仍是 NT$，`onCurrencyChange` 不重繪手風琴 | `src/index.html:652, 720, 814-818, 911, 1320` |
| 9 | Medium | 投報以「今日即期匯率」換算歷史成本，利息/資本利得隨匯率漂移 | `src/index.html:793, 1242, 1306-1311` |
| 10 | Medium | `force=true` 從 UI 不可達，當日快照寫入後一整天看不到 Sheets 更正值 | `api/main.py:54,111,139` + `src/index.html:553,565,577` |
| 11 | Medium | 後端不驗證抓回內容是否為 CSV，Google HTML 錯誤頁會被寫成快照服務整天 | `api/main.py:43-50, 65-67` |
| 12 | Medium | 後端 `datetime.now()` 無時區（多半 UTC），台灣 00:00–08:00 快照日期 off-by-one | `api/main.py:56,78,113,141` |
| 13 | Medium | PATCH 只填 `== '-'`，當天首次回寫後該列凍結，盤中不再更新 | `api/main.py:91` |
| 14 | Medium | 投報卡在 `!stockCostTWD` early-return，股票抓取失敗時兩張卡永遠顯示「—」 | `src/index.html:788-789, 807-811` |
| 15 | Medium | 無任何測試 | `api/` |
| 16 | Low | 視圖 tab 靠比對中文 label 切 active，改字/加 icon 即壞 | `src/index.html:976-978` |
| 17 | Low | 快照寫回 fire-and-forget `.catch(()=>{})`，失敗/404 無提示 | `src/index.html:1277-1283` |
| 18 | Low | NTD/TWD 雙碼、無障礙缺失、無 reduced-motion、Chart.js 未鎖版、docs 漂移 | 散見 |
| 19 | Low | 依賴未鎖版、Dockerfile `--reload`、快照非原子寫入、CORS `*`、backup 吞錯 | `api/`、`backup_data.sh` |
