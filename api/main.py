from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import csv
import io
import os
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict

# ── 設定（皆可由環境變數覆寫，預設維持原值，行為不變）──
SHEET_DOC_ID = os.environ.get(
    "SHEET_DOC_ID",
    "2PACX-1vQ6oDlhxWgtYn3IVCV1-ewP6kMsULRuVJPXiAYLMV_dXVXRbH8VGI7LzM6wtXqXX9EJTxQgFKqb0BlF",
)
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
TZ = ZoneInfo(os.environ.get("TZ_NAME", "Asia/Taipei"))
FETCH_TIMEOUT = float(os.environ.get("FETCH_TIMEOUT", "10"))

# 每個資料來源：工作表 gid + 快照子目錄（檔名前綴 == feed 名）
FEEDS: Dict[str, Dict[str, object]] = {
    "stock":   {"gid": os.environ.get("STOCK_GID", "756201628"),   "dir": DATA_DIR / "stock"},
    "bank":    {"gid": os.environ.get("BANK_GID", "983098033"),    "dir": DATA_DIR / "bank"},
    "pension": {"gid": os.environ.get("PENSION_GID", "889457991"), "dir": DATA_DIR / "pension"},
}


def today_str() -> str:
    """以設定時區計算「今日」，避免容器 UTC 導致午夜後快照日期 off-by-one。"""
    return datetime.now(TZ).strftime("%Y-%m-%d")


def sheet_url(gid: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/e/{SHEET_DOC_ID}"
        f"/pub?gid={gid}&single=true&output=csv"
    )


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)


async def _fetch_sheet(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, timeout=FETCH_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"無法抓取 Google Sheets：{e}")
    return resp.text


async def _refresh_feed(feed: str, force: bool) -> PlainTextResponse:
    """回傳該 feed 的 CSV。今日快照存在且非強制時用快照；否則抓 Google Sheets 並存檔。"""
    cfg = FEEDS[feed]
    date_str = today_str()
    snapshot = cfg["dir"] / f"{feed}_{date_str}.csv"

    if not force and snapshot.exists():
        return PlainTextResponse(
            snapshot.read_text(encoding="utf-8"),
            headers={"X-Data-Source": "cache", "X-Snapshot-Date": date_str},
        )

    csv_content = await _fetch_sheet(sheet_url(cfg["gid"]))
    cfg["dir"].mkdir(parents=True, exist_ok=True)
    snapshot.write_text(csv_content, encoding="utf-8")

    return PlainTextResponse(
        csv_content,
        headers={"X-Data-Source": "fresh", "X-Snapshot-Date": date_str},
    )


def _list_history(feed: str):
    return [f.name for f in sorted(FEEDS[feed]["dir"].glob(f"{feed}_*.csv"))]


def _register_feed_routes(feed: str) -> None:
    """為單一 feed 註冊 refresh + history 兩個 GET 路由。"""

    async def refresh(force: bool = False):
        return await _refresh_feed(feed, force)

    async def history():
        return _list_history(feed)

    app.add_api_route(
        f"/api/{feed}/refresh", refresh, methods=["GET"],
        response_class=PlainTextResponse,
        name=f"refresh_{feed}",
        summary=f"回傳 {feed} CSV，今日快照存在則用快照（?force=true 強制重抓）",
    )
    app.add_api_route(
        f"/api/{feed}/history", history, methods=["GET"],
        name=f"history_{feed}",
        summary=f"列出所有 {feed} 歷史快照檔名",
    )


for _feed in FEEDS:
    _register_feed_routes(_feed)


@app.patch("/api/stock/snapshot")
async def patch_stock_snapshot(prices: Dict[str, float] = Body(...)):
    """Finnhub 取得的即時股價寫回今日股票快照，只更新 Current Price 為 '-' 的列。"""
    date_str = today_str()
    snapshot = FEEDS["stock"]["dir"] / f"stock_{date_str}.csv"
    if not snapshot.exists():
        raise HTTPException(status_code=404, detail="今日快照不存在")

    content = snapshot.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    fieldnames = list(reader.fieldnames)

    updated = 0
    for row in rows:
        ticker = row.get("Ticker", "")
        if ticker in prices and row.get("Current Price", "").strip() == "-":
            row["Current Price"] = str(round(prices[ticker], 4))
            updated += 1

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    snapshot.write_text(output.getvalue(), encoding="utf-8")

    return {"updated": updated}
