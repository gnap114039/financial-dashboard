"""每日快照（不需啟動 FastAPI / Docker）：抓三張表存成今日快照，並用 Finnhub 補上持倉的 '-' 現價。

由備份 repo 的 GitHub Actions 每日排程執行，也可本機手動執行：
    DATA_DIR=src/data python api/snapshot.py

直接沿用 main.py 的 FEEDS / 快照 / 回寫邏輯，產出格式與後端快照一致；
今日快照已存在則不重抓（與後端 cache 行為相同），可重複執行。
"""
import asyncio
import csv
import io
import os
import re
from pathlib import Path

import httpx

from main import FEEDS, FETCH_TIMEOUT, _refresh_feed, patch_stock_snapshot, today_str

FINNHUB_URL = "https://finnhub.io/api/v1/quote"
SPECIAL_TICKERS = {"cash", "principal"}


def finnhub_key() -> str:
    """優先讀環境變數 FINNHUB_KEY；未設定時沿用前端 index.html 的 key（該 key 已隨 GitHub Pages 公開）。"""
    key = os.environ.get("FINNHUB_KEY", "").strip()
    if key:
        return key
    html = (Path(__file__).resolve().parent.parent / "src" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const FINNHUB_KEY = '([^']+)'", html)
    return m.group(1) if m else ""


def _shares(value: str) -> float:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return 0.0


def tickers_needing_price(snapshot: Path) -> list:
    """持倉中（股數 > 0、非 CASH / PRINCIPAL）且 Current Price 為 '-' 的代號，與前端抓 Finnhub 的條件一致。"""
    rows = csv.DictReader(io.StringIO(snapshot.read_text(encoding="utf-8")))
    return [
        row["Ticker"] for row in rows
        if row.get("Ticker", "").lower() not in SPECIAL_TICKERS
        and _shares(row.get("Total Share", "")) > 0
        and row.get("Current Price", "").strip() == "-"
    ]


async def fetch_prices(tickers: list, key: str) -> dict:
    prices = {}
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
        for ticker in tickers:
            try:
                resp = await client.get(FINNHUB_URL, params={"symbol": ticker, "token": key})
                resp.raise_for_status()
                price = resp.json().get("c")
            except (httpx.HTTPError, ValueError) as e:
                print(f"⚠ {ticker}：Finnhub 取價失敗（{e}），保留 '-'")
                continue
            if price:
                prices[ticker] = float(price)
            else:
                print(f"⚠ {ticker}：Finnhub 無報價，保留 '-'")
    return prices


async def main() -> None:
    for feed in FEEDS:
        resp = await _refresh_feed(feed, force=False)
        print(f"{feed}：{resp.headers['X-Data-Source']} · {resp.headers['X-Snapshot-Date']}")

    snapshot = FEEDS["stock"]["dir"] / f"stock_{today_str()}.csv"
    tickers = tickers_needing_price(snapshot)
    if not tickers:
        print("stock：所有持倉皆已有現價")
        return

    key = finnhub_key()
    if not key:
        print(f"⚠ 找不到 Finnhub key，{len(tickers)} 檔現價保留 '-'")
        return

    prices = await fetch_prices(tickers, key)
    if prices:
        result = await patch_stock_snapshot(prices)
        print(f"stock：已補上 {result['updated']} / {len(tickers)} 檔現價")


if __name__ == "__main__":
    asyncio.run(main())
